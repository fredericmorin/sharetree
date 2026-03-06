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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 403 — no patterns
# ---------------------------------------------------------------------------


def test_no_patterns_is_forbidden() -> None:
    assert http_exc("root_file.txt", []).status_code == 403
    assert http_exc("docs/readme.txt", []).status_code == 403


# ---------------------------------------------------------------------------
# 403 — path traversal
# ---------------------------------------------------------------------------


def test_path_traversal_is_forbidden() -> None:
    assert http_exc("..", ["/*"]).status_code == 403
    assert http_exc("../../etc/passwd", ["/*"]).status_code == 403
    assert http_exc("docs/../../etc/passwd", ["/*"]).status_code == 403
    # Absolute path overrides SHARE_ROOT in Python Path joining
    assert http_exc("/etc/passwd", ["/*"]).status_code == 403
    assert http_exc("/etc", ["/*"]).status_code == 403


# ---------------------------------------------------------------------------
# 403 — pattern mismatch (file exists but not allowed)
# ---------------------------------------------------------------------------


def test_file_outside_pattern_is_forbidden() -> None:
    # secret dir not covered by /docs/*
    assert http_exc("secret/private.txt", ["/docs/*"]).status_code == 403
    # images not covered by /docs/*
    assert http_exc("images/photo.jpg", ["/docs/*"]).status_code == 403
    # root file not covered by /docs/*
    assert http_exc("root_file.txt", ["/docs/*"]).status_code == 403
    # wrong file within same dir
    assert http_exc("docs/guide.txt", ["/docs/readme.txt"]).status_code == 403
    # deep file not covered
    assert http_exc("docs/sub/deep.txt", ["/images/*"]).status_code == 403


# ---------------------------------------------------------------------------
# 404 — file does not exist
# ---------------------------------------------------------------------------


def test_missing_file_is_not_found() -> None:
    assert http_exc("missing.txt", ["/*"]).status_code == 404
    assert http_exc("docs/missing.txt", ["/docs/*"]).status_code == 404
    assert http_exc("docs/sub/nope.txt", ["/docs/*"]).status_code == 404
    assert http_exc("docs/sub/nope.txt", ["/**"]).status_code == 404


# ---------------------------------------------------------------------------
# 400 — path is a directory
# ---------------------------------------------------------------------------


def test_directory_path_is_bad_request() -> None:
    # Pattern must match the path for the is_file() check to be reached;
    # /* and /** both match directory paths, exposing the 400.
    assert http_exc("docs", ["/*"]).status_code == 400
    assert http_exc("docs", ["/**"]).status_code == 400
    assert http_exc("docs/sub", ["/**"]).status_code == 400
    assert http_exc("images", ["/*"]).status_code == 400


def test_directory_path_with_non_matching_pattern_is_forbidden() -> None:
    # /docs/* matches contents of docs/, not the docs/ dir itself → 403
    assert http_exc("docs", ["/docs/*"]).status_code == 403
    assert http_exc("docs/sub", ["/docs/sub/*"]).status_code == 403


# ---------------------------------------------------------------------------
# Success — returns resolved Path
# ---------------------------------------------------------------------------


def test_returns_path_object(root: Path) -> None:
    result = get_file_path("root_file.txt", ["/*"])
    assert isinstance(result, Path)
    assert result == (root / "root_file.txt").resolve()


def test_root_file_with_wildcard(root: Path) -> None:
    result = get_file_path("root_file.txt", ["/*"])
    assert result.name == "root_file.txt"
    assert result.is_file()


def test_nested_file(root: Path) -> None:
    result = get_file_path("docs/readme.txt", ["/docs/*"])
    assert result.name == "readme.txt"
    assert result.is_file()


def test_deep_file(root: Path) -> None:
    result = get_file_path("docs/sub/deep.txt", ["/docs/*"])
    assert result.name == "deep.txt"
    assert result.is_file()


# ---------------------------------------------------------------------------
# Pattern: /* (wildcard at root — fnmatch * matches /)
# ---------------------------------------------------------------------------


def test_wildcard_root_grants_all_files() -> None:
    assert get_file_path("root_file.txt", ["/*"]).is_file()
    assert get_file_path("docs/readme.txt", ["/*"]).is_file()
    assert get_file_path("docs/guide.txt", ["/*"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/*"]).is_file()
    assert get_file_path("images/photo.jpg", ["/*"]).is_file()
    assert get_file_path("secret/private.txt", ["/*"]).is_file()


# ---------------------------------------------------------------------------
# Pattern: /dir/* (restricted subtree)
# ---------------------------------------------------------------------------


def test_subtree_pattern_allows_files_inside() -> None:
    assert get_file_path("docs/readme.txt", ["/docs/*"]).is_file()
    assert get_file_path("docs/guide.txt", ["/docs/*"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/docs/*"]).is_file()


def test_subtree_pattern_blocks_files_outside() -> None:
    assert http_exc("images/photo.jpg", ["/docs/*"]).status_code == 403
    assert http_exc("secret/private.txt", ["/docs/*"]).status_code == 403
    assert http_exc("root_file.txt", ["/docs/*"]).status_code == 403


# ---------------------------------------------------------------------------
# Pattern: exact file path
# ---------------------------------------------------------------------------


def test_exact_file_pattern_allows_only_that_file() -> None:
    assert get_file_path("docs/readme.txt", ["/docs/readme.txt"]).is_file()
    assert http_exc("docs/guide.txt", ["/docs/readme.txt"]).status_code == 403
    assert http_exc("docs/sub/deep.txt", ["/docs/readme.txt"]).status_code == 403


def test_exact_deep_file_pattern() -> None:
    assert get_file_path("docs/sub/deep.txt", ["/docs/sub/deep.txt"]).is_file()
    assert http_exc("docs/readme.txt", ["/docs/sub/deep.txt"]).status_code == 403


# ---------------------------------------------------------------------------
# Pattern: /** (double-star)
# ---------------------------------------------------------------------------


def test_double_star_grants_all_files() -> None:
    assert get_file_path("root_file.txt", ["/**"]).is_file()
    assert get_file_path("docs/readme.txt", ["/**"]).is_file()
    assert get_file_path("docs/sub/deep.txt", ["/**"]).is_file()
    assert get_file_path("secret/private.txt", ["/**"]).is_file()


# ---------------------------------------------------------------------------
# Multiple patterns (union)
# ---------------------------------------------------------------------------


def test_multiple_patterns_union() -> None:
    patterns = ["/docs/*", "/images/*"]
    assert get_file_path("docs/readme.txt", patterns).is_file()
    assert get_file_path("docs/guide.txt", patterns).is_file()
    assert get_file_path("images/photo.jpg", patterns).is_file()
    assert http_exc("secret/private.txt", patterns).status_code == 403
    assert http_exc("root_file.txt", patterns).status_code == 403


def test_multiple_exact_patterns() -> None:
    patterns = ["/docs/readme.txt", "/images/photo.jpg"]
    assert get_file_path("docs/readme.txt", patterns).is_file()
    assert get_file_path("images/photo.jpg", patterns).is_file()
    assert http_exc("docs/guide.txt", patterns).status_code == 403
    assert http_exc("docs/sub/deep.txt", patterns).status_code == 403
    assert http_exc("secret/private.txt", patterns).status_code == 403


def test_redundant_patterns_same_result(root: Path) -> None:
    a = get_file_path("docs/readme.txt", ["/docs/*"])
    b = get_file_path("docs/readme.txt", ["/docs/*", "/docs/*"])
    assert a == b
