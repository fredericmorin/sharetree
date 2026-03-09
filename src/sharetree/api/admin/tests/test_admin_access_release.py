"""Tests for POST /api/v1/admin/access/release."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from sharetree.app import app

LOGIN_URL = "/api/v1/admin/login"
RELEASE_URL = "/api/v1/admin/access/release"
ADMIN_PASSWORD = "supersecret"


@pytest.fixture()
def trust_headers_disabled():
    with (
        patch("sharetree.api.admin.deps.settings") as mock_deps,
        patch("sharetree.api.admin.auth.settings") as mock_auth,
    ):
        mock_deps.TRUST_HEADERS = False
        mock_auth.TRUST_HEADERS = False
        mock_auth.ADMIN_PASSWORD = ADMIN_PASSWORD
        yield


@pytest.fixture()
def admin_client(trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    client.post(LOGIN_URL, json={"password": ADMIN_PASSWORD})
    return client


def test_release_found_returns_200(admin_client):
    with patch("sharetree.api.admin.access.access_service.release_access_code", return_value=True):
        res = admin_client.post(RELEASE_URL, json={"code": "somecode"})
    assert res.status_code == 200


def test_release_not_found_returns_404(admin_client):
    with patch("sharetree.api.admin.access.access_service.release_access_code", return_value=False):
        res = admin_client.post(RELEASE_URL, json={"code": "missing"})
    assert res.status_code == 404


def test_release_requires_auth(trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    with patch("sharetree.api.admin.access.access_service.release_access_code", return_value=True):
        res = client.post(RELEASE_URL, json={"code": "anycode"})
    assert res.status_code == 403
