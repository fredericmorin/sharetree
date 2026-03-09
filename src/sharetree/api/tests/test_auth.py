"""Tests for GET /api/v1/auth (forward-auth endpoint)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from sharetree.app import app

AUTH_URL = "/api/v1/auth"

_EMPTY_ACCESS = {"valid_active_codes": [], "accessible_paths": [], "active_code_details": []}
_FULL_ACCESS = {"valid_active_codes": ["code1"], "accessible_paths": ["/*"], "active_code_details": []}
_DOCS_ACCESS = {"valid_active_codes": ["code1"], "accessible_paths": ["/docs/*"], "active_code_details": []}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    (tmp_path / "report.pdf").write_bytes(b"%PDF")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.txt").write_text("guide")
    return tmp_path


@pytest.fixture(autouse=True)
def patch_share_root(root: Path):
    with patch("sharetree.services.browse.settings") as mock_settings:
        mock_settings.SHARE_ROOT = root
        yield


def test_missing_header_returns_400(client: TestClient) -> None:
    resp = client.get(AUTH_URL)
    assert resp.status_code == 400


def test_wrong_prefix_returns_400(client: TestClient) -> None:
    resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "browse/report.pdf"})
    assert resp.status_code == 400


def test_empty_path_returns_400(client: TestClient) -> None:
    resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "/"})
    assert resp.status_code == 400


def test_no_session_codes_returns_403(client: TestClient) -> None:
    with patch("sharetree.api.auth.access_service.resolve_access_code_paths", return_value=_EMPTY_ACCESS):
        resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "/report.pdf"})
    assert resp.status_code == 403


def test_allowed_file_returns_200(client: TestClient) -> None:
    with patch("sharetree.api.auth.access_service.resolve_access_code_paths", return_value=_FULL_ACCESS):
        resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "/report.pdf"})
    assert resp.status_code == 200
    assert resp.json()["allowed"] is True


def test_pattern_mismatch_returns_403(client: TestClient) -> None:
    with patch("sharetree.api.auth.access_service.resolve_access_code_paths", return_value=_DOCS_ACCESS):
        resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "/report.pdf"})
    assert resp.status_code == 403


def test_file_not_found_returns_404(client: TestClient) -> None:
    with patch("sharetree.api.auth.access_service.resolve_access_code_paths", return_value=_FULL_ACCESS):
        resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "/missing.pdf"})
    assert resp.status_code == 404


def test_allowed_nested_file_returns_200(client: TestClient) -> None:
    with patch("sharetree.api.auth.access_service.resolve_access_code_paths", return_value=_DOCS_ACCESS):
        resp = client.get(AUTH_URL, headers={"X-Forwarded-Uri": "/docs/guide.txt"})
    assert resp.status_code == 200
    assert resp.json()["allowed"] is True
