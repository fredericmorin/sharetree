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

import pytest
from pathlib import Path
from unittest.mock import patch

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


# ── 403: no patterns / no access ─────────────────────────────────────────────

class TestForbidden:
    def test_empty_patterns_raises_403(self):
        assert http_exc(list_directory_entries, "", []).status_code == 403

    def test_subdir_not_covered_by_pattern_raises_403(self):
        # /secret/ is not reachable under /docs/*
        assert http_exc(list_directory_entries, "secret", ["/docs/*"]).status_code == 403

    def test_sibling_subdir_not_covered_raises_403(self):
        assert http_exc(list_directory_entries, "images", ["/docs/*"]).status_code == 403

    def test_path_traversal_single_dotdot_raises_403(self):
        assert http_exc(list_directory_entries, "..", ["/*"]).status_code == 403

    def test_path_traversal_double_dotdot_raises_403(self):
        assert http_exc(list_directory_entries, "../../etc", ["/*"]).status_code == 403

    def test_path_traversal_embedded_dotdot_raises_403(self):
        # docs/../../etc escapes the root even though it starts within it
        assert http_exc(list_directory_entries, "docs/../../etc", ["/*"]).status_code == 403

    def test_path_traversal_absolute_replaces_root_raises_403(self):
        # Path division with an absolute segment discards the left side
        assert http_exc(list_directory_entries, "/etc", ["/*"]).status_code == 403

    def test_path_traversal_embedded_absolute_raises_403(self):
        assert http_exc(list_directory_entries, "/etc/passwd", ["/*"]).status_code == 403

    def test_nonexistent_path_outside_any_pattern_raises_403(self):
        # Inaccessible dir should get 403, not 404, to avoid leaking existence
        assert http_exc(list_directory_entries, "secret", ["/docs/*"]).status_code == 403

    def test_deeply_nested_outside_pattern_raises_403(self):
        assert http_exc(list_directory_entries, "secret/sub/deep", ["/docs/*"]).status_code == 403


# ── 404: path does not exist ──────────────────────────────────────────────────

class TestNotFound:
    def test_nonexistent_root_level_dir_raises_404(self):
        assert http_exc(list_directory_entries, "missing", ["/*"]).status_code == 404

    def test_nonexistent_nested_dir_raises_404(self):
        assert http_exc(list_directory_entries, "docs/missing", ["/docs/*"]).status_code == 404

    def test_nonexistent_deep_nested_dir_raises_404(self):
        assert http_exc(list_directory_entries, "docs/sub/nope", ["/docs/*"]).status_code == 404


# ── 400: path is a file ───────────────────────────────────────────────────────

class TestNotADirectory:
    def test_root_level_file_raises_400(self):
        assert http_exc(list_directory_entries, "root_file.txt", ["/*"]).status_code == 400

    def test_nested_file_raises_400(self):
        assert http_exc(list_directory_entries, "docs/readme.txt", ["/docs/*"]).status_code == 400

    def test_deeply_nested_file_raises_400(self):
        assert http_exc(list_directory_entries, "docs/sub/deep.txt", ["/docs/*"]).status_code == 400


# ── Entry structure ───────────────────────────────────────────────────────────

class TestEntryStructure:
    def test_directory_entry_shape(self):
        entries = list_directory_entries("", ["/*"])
        docs = next(e for e in entries if e["name"] == "docs")
        assert docs == {"name": "docs", "type": "directory", "size": None, "path": "/docs"}

    def test_file_entry_shape(self):
        entries = list_directory_entries("", ["/*"])
        f = next(e for e in entries if e["name"] == "root_file.txt")
        assert f == {"name": "root_file.txt", "type": "file", "size": 4, "path": "/root_file.txt"}

    def test_nested_file_size(self):
        entries = list_directory_entries("docs", ["/docs/*"])
        readme = next(e for e in entries if e["name"] == "readme.txt")
        assert readme["size"] == 6

    def test_nested_file_path(self):
        entries = list_directory_entries("docs", ["/docs/*"])
        readme = next(e for e in entries if e["name"] == "readme.txt")
        assert readme["path"] == "/docs/readme.txt"

    def test_nested_dir_path(self):
        entries = list_directory_entries("docs", ["/docs/*"])
        sub = next(e for e in entries if e["name"] == "sub")
        assert sub["path"] == "/docs/sub"

    def test_deep_nested_entry_path(self):
        entries = list_directory_entries("docs/sub", ["/docs/*"])
        assert entries[0]["path"] == "/docs/sub/deep.txt"

    def test_image_file_size(self):
        entries = list_directory_entries("images", ["/*"])
        photo = next(e for e in entries if e["name"] == "photo.jpg")
        assert photo["size"] == 10


# ── Sorting ───────────────────────────────────────────────────────────────────

class TestSorting:
    def test_directories_sorted_before_files(self):
        entries = list_directory_entries("", ["/*"])
        types = [e["type"] for e in entries]
        last_dir_idx = max(i for i, t in enumerate(types) if t == "directory")
        first_file_idx = min(i for i, t in enumerate(types) if t == "file")
        assert last_dir_idx < first_file_idx

    def test_directories_sorted_alphabetically(self):
        entries = list_directory_entries("", ["/*"])
        dirs = [e["name"] for e in entries if e["type"] == "directory"]
        assert dirs == sorted(dirs)

    def test_files_sorted_alphabetically(self):
        entries = list_directory_entries("docs", ["/docs/*"])
        files = [e["name"] for e in entries if e["type"] == "file"]
        assert files == sorted(files)

    def test_mixed_dir_with_multiple_files_sorted(self, root):
        (root / "docs" / "alpha.txt").write_text("a")
        (root / "docs" / "zebra.txt").write_text("z")
        entries = list_directory_entries("docs", ["/docs/*"])
        files = [e["name"] for e in entries if e["type"] == "file"]
        assert files == sorted(files)


# ── Pattern: /* (wildcard — everything) ───────────────────────────────────────

class TestPatternWildcardAll:
    def test_root_lists_all_entries(self):
        entries = list_directory_entries("", ["/*"])
        assert set(names(entries)) == {"docs", "images", "secret", "root_file.txt"}

    def test_subdir_lists_all_entries(self):
        entries = list_directory_entries("docs", ["/*"])
        assert set(names(entries)) == {"guide.txt", "readme.txt", "sub"}

    def test_deep_subdir_lists_entries(self):
        entries = list_directory_entries("docs/sub", ["/*"])
        assert names(entries) == ["deep.txt"]

    def test_star_crosses_path_separator(self):
        # fnmatch * matches across /, so /* grants recursive access
        entries = list_directory_entries("docs/sub", ["/*"])
        assert len(entries) == 1


# ── Pattern: /dir/* (restricted subtree) ─────────────────────────────────────

class TestPatternSubdirWildcard:
    def test_root_is_browseable_but_returns_no_entries(self):
        # Root is navigable (pattern starts with "/") but no root entries match /docs/*
        entries = list_directory_entries("", ["/docs/*"])
        assert entries == []

    def test_target_subdir_lists_entries(self):
        entries = list_directory_entries("docs", ["/docs/*"])
        assert set(names(entries)) == {"guide.txt", "readme.txt", "sub"}

    def test_deep_path_within_subdir_is_accessible(self):
        # fnmatch * crosses /, so /docs/* covers docs/sub/ too
        entries = list_directory_entries("docs/sub", ["/docs/*"])
        assert names(entries) == ["deep.txt"]

    def test_sibling_subdir_is_forbidden(self):
        assert http_exc(list_directory_entries, "images", ["/docs/*"]).status_code == 403

    def test_secret_subdir_is_forbidden(self):
        assert http_exc(list_directory_entries, "secret", ["/docs/*"]).status_code == 403


# ── Pattern: exact filename ───────────────────────────────────────────────────

class TestPatternExactFile:
    def test_exact_root_file_visible(self):
        entries = list_directory_entries("", ["/root_file.txt"])
        assert names(entries) == ["root_file.txt"]

    def test_other_root_entries_hidden(self):
        entries = list_directory_entries("", ["/root_file.txt"])
        assert all(e["name"] == "root_file.txt" for e in entries)

    def test_exact_nested_file_visible(self):
        entries = list_directory_entries("docs", ["/docs/readme.txt"])
        assert names(entries) == ["readme.txt"]

    def test_other_nested_files_hidden(self):
        entries = list_directory_entries("docs", ["/docs/readme.txt"])
        assert "guide.txt" not in names(entries)
        assert "sub" not in names(entries)


# ── Pattern: multiple patterns (union) ───────────────────────────────────────

class TestPatternUnion:
    def test_two_exact_dir_patterns_both_visible(self):
        entries = list_directory_entries("", ["/docs", "/images"])
        assert set(names(entries)) == {"docs", "images"}

    def test_two_exact_dir_patterns_excludes_others(self):
        entries = list_directory_entries("", ["/docs", "/images"])
        assert "secret" not in names(entries)
        assert "root_file.txt" not in names(entries)

    def test_two_subdir_wildcards_each_grants_own_tree(self):
        entries_docs = list_directory_entries("docs", ["/docs/*", "/images/*"])
        entries_images = list_directory_entries("images", ["/docs/*", "/images/*"])
        assert set(names(entries_docs)) == {"guide.txt", "readme.txt", "sub"}
        assert names(entries_images) == ["photo.jpg"]

    def test_two_subdir_wildcards_still_forbids_secret(self):
        assert http_exc(list_directory_entries, "secret", ["/docs/*", "/images/*"]).status_code == 403

    def test_redundant_patterns_deduplicated_effectively(self):
        # Same result whether pattern appears once or twice
        a = list_directory_entries("docs", ["/docs/*"])
        b = list_directory_entries("docs", ["/docs/*", "/docs/*"])
        assert names(a) == names(b)


# ── Pattern: /** (double-star) ────────────────────────────────────────────────

class TestPatternDoubleWildcard:
    def test_root_lists_everything(self):
        entries = list_directory_entries("", ["/**"])
        assert set(names(entries)) == {"docs", "images", "secret", "root_file.txt"}

    def test_subdir_lists_contents(self):
        entries = list_directory_entries("docs", ["/**"])
        assert set(names(entries)) == {"guide.txt", "readme.txt", "sub"}


# ── Empty directory ───────────────────────────────────────────────────────────

class TestEmptyDirectory:
    def test_empty_dir_returns_empty_list(self, root):
        (root / "empty").mkdir()
        entries = list_directory_entries("empty", ["/*"])
        assert entries == []

    def test_empty_subdir_returns_empty_list(self, root):
        (root / "docs" / "empty_sub").mkdir()
        entries = list_directory_entries("docs/empty_sub", ["/docs/*"])
        assert entries == []
