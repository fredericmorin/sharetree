"""
Tests for sharetree.services.browse.list_directory_entries

Filesystem layout created by the `root` fixture:

    <tmp>/
    ├── docs/
    │   ├── guide.txt       (5 bytes)
    │   ├── readme.txt      (6 bytes)
    │   └── sub/
    │       └── deep.txt    (4 bytes)
    ├── images/
    │   └── photo.jpg       (10 bytes)
    ├── secret/
    │   └── private.txt     (7 bytes)
    └── root_file.txt       (4 bytes)
"""

from pathlib import Path
from typing import Iterable
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from sharetree.services.browse import list_directory_entries

# ── Fixtures ──────────────────────────────────────────────────────────────────


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
    with patch("sharetree.services.browse.SHARE_ROOT", root):
        yield


def names(entries: list) -> list[str]:
    return [e["name"] for e in entries]


def http_exc(fn, *args, **kwargs) -> HTTPException:
    with pytest.raises(HTTPException) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value


def test_forbidden():
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


def test_not_found():
    assert http_exc(list_directory_entries, "missing", ["/*"]).status_code == 404
    assert http_exc(list_directory_entries, "docs/missing", ["/docs/*"]).status_code == 404
    assert http_exc(list_directory_entries, "docs/sub/nope", ["/docs/*"]).status_code == 404


def test_not_a_dir():
    assert http_exc(list_directory_entries, "root_file.txt", ["/*"]).status_code == 400
    assert http_exc(list_directory_entries, "docs/readme.txt", ["/docs/*"]).status_code == 400
    assert http_exc(list_directory_entries, "docs/sub/deep.txt", ["/docs/*"]).status_code == 400


# ── Pattern: /* (wildcard — everything) ───────────────────────────────────────


def test_patterns():
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

    _test("", ["/*"], {"docs", "images", "secret", "root_file.txt"})
    _test("docs", ["/*"], {"guide.txt", "readme.txt", "sub"})
    _test("docs/sub", ["/*"], ["deep.txt"])

    # Root is navigable (pattern starts with "/") but no root entries match /docs/*
    entries = list_directory_entries("", ["/docs/*"])
    assert entries == []

    entries = list_directory_entries("docs", ["/docs/*"])
    assert set(names(entries)) == {"guide.txt", "readme.txt", "sub"}

    entries = list_directory_entries("docs/sub", ["/docs/*"])
    assert names(entries) == ["deep.txt"]

    assert http_exc(list_directory_entries, "images", ["/docs/*"]).status_code == 403

    assert http_exc(list_directory_entries, "secret", ["/docs/*"]).status_code == 403


# ── Pattern: exact filename ───────────────────────────────────────────────────


def test_pattern_exact_file_visible_at_root():
    entries = list_directory_entries("", ["/root_file.txt"])
    assert names(entries) == ["root_file.txt"]


def test_pattern_exact_file_hides_other_root_entries():
    entries = list_directory_entries("", ["/root_file.txt"])
    assert all(e["name"] == "root_file.txt" for e in entries)


def test_pattern_exact_nested_file_visible():
    entries = list_directory_entries("docs", ["/docs/readme.txt"])
    assert names(entries) == ["readme.txt"]


def test_pattern_exact_nested_file_hides_siblings():
    entries = list_directory_entries("docs", ["/docs/readme.txt"])
    assert "guide.txt" not in names(entries)
    assert "sub" not in names(entries)


# ── Pattern: multiple patterns (union) ───────────────────────────────────────


def test_pattern_union_two_dirs_both_visible():
    entries = list_directory_entries("", ["/docs", "/images"])
    assert set(names(entries)) == {"docs", "images"}


def test_pattern_union_two_dirs_excludes_others():
    entries = list_directory_entries("", ["/docs", "/images"])
    assert "secret" not in names(entries)
    assert "root_file.txt" not in names(entries)


def test_pattern_union_each_wildcard_grants_own_subtree():
    entries_docs = list_directory_entries("docs", ["/docs/*", "/images/*"])
    entries_images = list_directory_entries("images", ["/docs/*", "/images/*"])
    assert set(names(entries_docs)) == {"guide.txt", "readme.txt", "sub"}
    assert names(entries_images) == ["photo.jpg"]


def test_pattern_union_still_forbids_uncovered_dir():
    assert http_exc(list_directory_entries, "secret", ["/docs/*", "/images/*"]).status_code == 403


def test_pattern_union_redundant_patterns_same_result():
    a = list_directory_entries("docs", ["/docs/*"])
    b = list_directory_entries("docs", ["/docs/*", "/docs/*"])
    assert names(a) == names(b)


# ── Pattern: /** (double-star) ────────────────────────────────────────────────


def test_pattern_double_star_root_lists_everything():
    entries = list_directory_entries("", ["/**"])
    assert set(names(entries)) == {"docs", "images", "secret", "root_file.txt"}


def test_pattern_double_star_subdir_lists_contents():
    entries = list_directory_entries("docs", ["/**"])
    assert set(names(entries)) == {"guide.txt", "readme.txt", "sub"}


# ── Empty directory ───────────────────────────────────────────────────────────


def test_empty_dir_returns_empty_list(root):
    (root / "empty").mkdir()
    entries = list_directory_entries("empty", ["/*"])
    assert entries == []


def test_empty_subdir_returns_empty_list(root):
    (root / "docs" / "empty_sub").mkdir()
    entries = list_directory_entries("docs/empty_sub", ["/docs/*"])
    assert entries == []
