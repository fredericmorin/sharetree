"""
Tests for sharetree.services.browse.get_file_path

Filesystem layout created by the `root` fixture:

    <tmp>/
    ├ docs/
    │   ├ guide.txt
    │   ├ readme.txt
    │   └ sub/
    │       └ deep.txt
    ├ images/
    │   └ photo.jpg
    ├ secret/
    │   └ private.txt
    └ root_file.txt
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from sharetree.services.browse import get_file_path


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.txt").write_text("readme")
    (tmp_path / "docs" / "guide.txt").write_text("guide")
    (tmp_path / "docs" / "sub").mkdir()
    (tmp_path / "docs" / "sub" / "deep.txt").write_text("deep")

    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "photo.jpg").write_bytes(b"\xff" * 10)

    (tmp_path / "secret").mkdir()
    (tmp_path / "secret" / "private.txt").write_text("private")

    (tmp_path / "root_file.txt").write_text("root")

    return tmp_path


@pytest.fixture(autouse=True)
def patch_share_root(root: Path):
    with patch("sharetree.services.browse.settings") as mock_settings:
        mock_settings.SHARE_ROOT = root
        yield


def http_exc(path: str, patterns: list[str]) -> HTTPException:
    with pytest.raises(HTTPException) as exc_info:
        get_file_path(path, patterns)
    return exc_info.value


def test_get_file_path_patterns() -> None:
    # 403 — no patterns
    assert http_exc("root_file.txt", []).status_code == 403
    assert http_exc("docs/readme.txt", []).status_code == 403

    # 403 — path traversal
    assert http_exc("..", ["/*"]).status_code == 403
    assert http_exc("../../etc/passwd", ["/*"]).status_code == 403
    assert http_exc("docs/../../etc/passwd", ["/*"]).status_code == 403
    assert http_exc("/etc/passwd", ["/*"]).status_code == 403
    assert http_exc("/etc", ["/*"]).status_code == 403

    # 403 — pattern mismatch (file exists but not allowed)
    assert http_exc("secret/private.txt", ["/docs/*"]).status_code == 403
    assert http_exc("images/photo.jpg", ["/docs/*"]).status_code == 403
    assert http_exc("root_file.txt", ["/docs/*"]).status_code == 403
    assert http_exc("docs/guide.txt", ["/docs/readme.txt"]).status_code == 403
    assert http_exc("docs/sub/deep.txt", ["/images/*"]).status_code == 403

    # 404 — file does not exist
    assert http_exc("missing.txt", ["/*"]).status_code == 404
    assert http_exc("docs/missing.txt", ["/docs/*"]).status_code == 404
    assert http_exc("docs/sub/nope.txt", ["/docs/*"]).status_code == 404
    assert http_exc("docs/sub/nope.txt", ["/**"]).status_code == 404

    # 400 — path is a directory
    assert http_exc("docs", ["/*"]).status_code == 400
    assert http_exc("docs", ["/**"]).status_code == 400
    assert http_exc("docs/sub", ["/**"]).status_code == 400
    assert http_exc("images", ["/*"]).status_code == 400
    assert http_exc("docs", ["/docs/*"]).status_code == 403
    assert http_exc("docs/sub", ["/docs/sub/*"]).status_code == 403

    # Success — returns resolved Path
    assert get_file_path("root_file.txt", ["/*"]).is_file()
    assert get_file_path("docs/readme.txt", ["/docs/*"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/docs/*"]).is_file()

    # Pattern: /* (wildcard at root — fnmatch * matches /)
    assert get_file_path("root_file.txt", ["/*"]).is_file()
    assert get_file_path("docs/readme.txt", ["/*"]).is_file()
    assert get_file_path("docs/guide.txt", ["/*"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/*"]).is_file()
    assert get_file_path("images/photo.jpg", ["/*"]).is_file()
    assert get_file_path("secret/private.txt", ["/*"]).is_file()

    # Pattern: /dir/* (restricted subtree)
    assert get_file_path("docs/readme.txt", ["/docs/*"]).is_file()
    assert get_file_path("docs/guide.txt", ["/docs/*"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/docs/*"]).is_file()
    assert http_exc("images/photo.jpg", ["/docs/*"]).status_code == 403
    assert http_exc("secret/private.txt", ["/docs/*"]).status_code == 403
    assert http_exc("root_file.txt", ["/docs/*"]).status_code == 403

    # Pattern: exact file path
    assert get_file_path("docs/readme.txt", ["/docs/readme.txt"]).is_file()
    assert http_exc("docs/guide.txt", ["/docs/readme.txt"]).status_code == 403
    assert http_exc("docs/sub/deep.txt", ["/docs/readme.txt"]).status_code == 403
    assert get_file_path("docs/sub/deep.txt", ["/docs/sub/deep.txt"]).is_file()
    assert http_exc("docs/readme.txt", ["/docs/sub/deep.txt"]).status_code == 403

    # Pattern: /** (double-star)
    assert get_file_path("root_file.txt", ["/**"]).is_file()
    assert get_file_path("docs/readme.txt", ["/**"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/**"]).is_file()
    assert get_file_path("secret/private.txt", ["/**"]).is_file()

    # Multiple patterns (union)
    patterns = ["/docs/*", "/images/*"]
    assert get_file_path("docs/readme.txt", patterns).is_file()
    assert get_file_path("docs/guide.txt", patterns).is_file()
    assert get_file_path("images/photo.jpg", patterns).is_file()
    assert http_exc("secret/private.txt", patterns).status_code == 403
    assert http_exc("root_file.txt", patterns).status_code == 403

    # Multiple exact pattern
    patterns = ["/docs/readme.txt", "/images/photo.jpg"]
    assert get_file_path("docs/readme.txt", patterns).is_file()
    assert get_file_path("images/photo.jpg", patterns).is_file()
    assert http_exc("docs/guide.txt", patterns).status_code == 403
    assert http_exc("docs/sub/deep.txt", patterns).status_code == 403
    assert http_exc("secret/private.txt", patterns).status_code == 403

    # Redundant patterns same result
    a = get_file_path("docs/readme.txt", ["/docs/*"])
    b = get_file_path("docs/readme.txt", ["/docs/*", "/docs/*"])
    assert a == b
