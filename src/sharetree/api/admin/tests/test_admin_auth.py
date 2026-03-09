"""
Tests for admin endpoint authentication.

Two modes:
- TRUST_HEADERS=False (default): session-based auth via /api/v1/admin/login
- TRUST_HEADERS=True: Remote-Groups header forwarded by upstream proxy
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from sharetree.app import app

ADMIN_URL = "/api/v1/admin/access/create"
LOGIN_URL = "/api/v1/admin/login"
LOGOUT_URL = "/api/v1/admin/logout"
VALID_BODY = {"patterns": ["/docs/*"], "nick": "test"}
ADMIN_PASSWORD = "supersecret"

# All protected admin endpoints: (method, path, json_body)
PROTECTED_ADMIN_ENDPOINTS = [
    ("POST", "/api/v1/admin/access/create", {"patterns": ["/docs/*"], "nick": "test"}),
    ("GET", "/api/v1/admin/access/sessions", None),
    ("GET", "/api/v1/admin/browse", None),
    ("GET", "/api/v1/admin/browse/some/path", None),
]


@pytest.fixture()
def mock_create_access_code():
    with patch("sharetree.services.access.create_access_code", return_value="testcode123") as mock:
        yield mock


@pytest.fixture()
def trust_headers_enabled():
    with (
        patch("sharetree.api.admin.deps.settings") as mock_deps,
        patch("sharetree.api.admin.auth.settings") as mock_auth,
    ):
        mock_deps.TRUST_HEADERS = True
        mock_auth.TRUST_HEADERS = True
        mock_auth.ADMIN_PASSWORD = None
        yield


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


# ---------------------------------------------------------------------------
# TRUST_HEADERS=False — session-based auth
# ---------------------------------------------------------------------------


def test_unauthenticated_session_is_forbidden(trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY)
    assert response.status_code == 403


def test_login_with_correct_password_grants_access(mock_create_access_code, trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    login_res = client.post(LOGIN_URL, json={"password": ADMIN_PASSWORD})
    assert login_res.status_code == 200
    assert login_res.json()["data"]["authenticated"] is True

    admin_res = client.post(ADMIN_URL, json=VALID_BODY)
    assert admin_res.status_code == 200


def test_login_with_wrong_password_is_rejected(trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(LOGIN_URL, json={"password": "wrongpassword"})
    assert res.status_code == 401


def test_logout_clears_admin_session(mock_create_access_code, trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    client.post(LOGIN_URL, json={"password": ADMIN_PASSWORD})
    assert client.post(ADMIN_URL, json=VALID_BODY).status_code == 200

    client.post(LOGOUT_URL)
    assert client.post(ADMIN_URL, json=VALID_BODY).status_code == 403


# ---------------------------------------------------------------------------
# TRUST_HEADERS=True — Remote-Groups header
# ---------------------------------------------------------------------------


def test_no_remote_groups_header_is_forbidden(trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY)
    assert response.status_code == 403


def test_wrong_group_is_forbidden(trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users"})
    assert response.status_code == 403


def test_multiple_wrong_groups_is_forbidden(trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users,staff,guests"})
    assert response.status_code == 403


def test_correct_group_is_allowed(mock_create_access_code, trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "admins"})
    assert response.status_code == 200


def test_correct_group_among_multiple_is_allowed(mock_create_access_code, trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users,admins,staff"})
    assert response.status_code == 200


def test_empty_remote_groups_header_is_forbidden(trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": ""})
    assert response.status_code == 403


def test_whitespace_group_names_are_handled(mock_create_access_code, trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": " admins "})
    assert response.status_code == 200


def test_login_endpoint_returns_404_when_trust_headers_enabled(trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(LOGIN_URL, json={"password": "anything"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Parametrized: every protected admin endpoint enforces auth
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("method,path,body", PROTECTED_ADMIN_ENDPOINTS)
def test_all_admin_endpoints_require_session_auth(method, path, body, trust_headers_disabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.request(method, path, json=body)
    assert response.status_code == 403, f"{method} {path} should be 403 without session auth"


@pytest.mark.parametrize("method,path,body", PROTECTED_ADMIN_ENDPOINTS)
def test_all_admin_endpoints_require_remote_groups_header(method, path, body, trust_headers_enabled):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.request(method, path, json=body)
    assert response.status_code == 403, f"{method} {path} should be 403 without Remote-Groups header"
