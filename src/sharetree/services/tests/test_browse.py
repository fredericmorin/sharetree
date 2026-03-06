"""
Tests for sharetree.services.browse.list_directory_entries

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
from typing import Iterable
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from sharetree.services.browse import list_directory_entries

#  Fixtures


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


def names(entries: list) -> list[str]:
    return [e["name"] for e in entries]


def http_exc(fn, *args, **kwargs) -> HTTPException:
    with pytest.raises(HTTPException) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value


def test_forbidden(root: Path) -> None:
    assert http_exc(list_directory_entries, "", []).status_code == 403
    assert http_exc(list_directory_entries, "secret", ["/docs/*"]).status_code == 403
    assert http_exc(list_directory_entries, "images", ["/docs/*"]).status_code == 403
    assert http_exc(list_directory_entries, "..", ["/*"]).status_code == 403
    assert http_exc(list_directory_entries, "../../etc", ["/*"]).status_code == 403
    assert http_exc(list_directory_entries, "docs/../../etc", ["/*"]).status_code == 403
    assert http_exc(list_directory_entries, "/etc", ["/*"]).status_code == 403
    assert http_exc(list_directory_entries, "/etc/passwd", ["/*"]).status_code == 403
    assert http_exc(list_directory_entries, "secret", ["/docs/*"]).status_code == 403
    assert http_exc(list_directory_entries, "secret/sub/deep", ["/docs/*"]).status_code == 403


def test_not_found(root: Path) -> None:
    assert http_exc(list_directory_entries, "missing", ["/*"]).status_code == 404
    assert http_exc(list_directory_entries, "docs/missing", ["/docs/*"]).status_code == 404
    assert http_exc(list_directory_entries, "docs/sub/nope", ["/docs/*"]).status_code == 404


def test_not_a_dir(root: Path) -> None:
    assert http_exc(list_directory_entries, "root_file.txt", ["/*"]).status_code == 400
    assert http_exc(list_directory_entries, "docs/readme.txt", ["/docs/*"]).status_code == 400
    assert http_exc(list_directory_entries, "docs/sub/deep.txt", ["/docs/*"]).status_code == 400


def test_patterns(root: Path) -> None:
    def _test(
        path: str,
        patterns: list[str],
        expect_files: Iterable[str] | None = None,
        expect_error_code: int | None = None,
    ) -> None:
        if expect_error_code is not None:
            with pytest.raises(HTTPException) as exc_info:
                list_directory_entries(path, patterns)
            assert exc_info.value.status_code == 403
        else:
            assert expect_files is not None
            entries = list_directory_entries(path, patterns)
            assert set(names(entries)) == set(expect_files)

    #  Pattern: /* (wildcard — everything)
    _test("", ["/*"], {"docs", "images", "secret", "root_file.txt"})
    _test("docs", ["/*"], {"guide.txt", "readme.txt", "sub"})
    _test("docs/sub", ["/*"], ["deep.txt"])

    #  Pattern: /dir/* (restricted subtree)
    # Root shows ancestor dirs that lead to matching patterns
    _test("", ["/docs/*"], ["docs"])
    _test("docs", ["/docs/*"], {"guide.txt", "readme.txt", "sub"})
    _test("docs/sub", ["/docs/*"], ["deep.txt"])
    _test("images", ["/docs/*"], expect_error_code=403)
    _test("secret", ["/docs/*"], expect_error_code=403)

    #  Pattern: exact filename
    _test("", ["/root_file.txt"], ["root_file.txt"])
    _test("docs", ["/docs/readme.txt"], ["readme.txt"])

    #  Pattern: exact folder name
    _test("", ["/docs"], {"docs"})
    _test("docs", ["/docs"], {"guide.txt", "readme.txt", "sub"})

    #  Pattern: multiple patterns (union)
    _test("", ["/docs", "/images"], {"docs", "images"})
    _test("docs", ["/docs/*", "/images/*"], {"guide.txt", "readme.txt", "sub"})
    _test("images", ["/docs/*", "/images/*"], ["photo.jpg"])
    _test("secret", ["/docs/*", "/images/*"], expect_error_code=403)

    #  Pattern: /** (double-star)
    _test("", ["/**"], {"docs", "images", "secret", "root_file.txt"})
    _test("docs", ["/**"], {"guide.txt", "readme.txt", "sub"})

    #  Empty directory
    (root / "empty").mkdir()
    _test("empty", ["/*"], [])
    (root / "docs" / "empty_sub").mkdir()
    _test("docs/empty_sub", ["/docs/*"], [])

    #  ancestor directories
    _test("", ["/docs/sub/deep.txt"], ["docs"])
    _test("docs", ["/docs/sub/deep.txt"], ["sub"])
    _test("docs/sub", ["/docs/sub/deep.txt"], ["deep.txt"])


def test_pattern_union_redundant_patterns_same_result(root) -> None:
    a = list_directory_entries("docs", ["/docs/*"])
    b = list_directory_entries("docs", ["/docs/*", "/docs/*"])
    assert names(a) == names(b)
