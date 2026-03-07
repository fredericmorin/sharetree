"""
Tests for admin endpoint authentication via the Remote-Groups header.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from sharetree.app import app

client = TestClient(app, raise_server_exceptions=False)

ADMIN_URL = "/api/v1/admin/access/create"
VALID_BODY = {"patterns": ["/docs/*"], "nick": "test"}


@pytest.fixture()
def mock_create_access_code():
    with patch("sharetree.services.access.create_access_code", return_value="testcode123") as mock:
        yield mock


@pytest.fixture()
def trust_headers_enabled():
    with patch("sharetree.api.admin.deps.settings") as mock_settings:
        mock_settings.TRUST_HEADERS = True
        yield


@pytest.fixture()
def trust_headers_disabled():
    with patch("sharetree.api.admin.deps.settings") as mock_settings:
        mock_settings.TRUST_HEADERS = False
        yield


# --- TRUST_HEADERS=False (default) ---


def test_trust_headers_disabled_allows_all_requests(mock_create_access_code, trust_headers_disabled):
    response = client.post(ADMIN_URL, json=VALID_BODY)
    assert response.status_code == 200


def test_trust_headers_disabled_ignores_wrong_group(mock_create_access_code, trust_headers_disabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users"})
    assert response.status_code == 200


# --- TRUST_HEADERS=True ---


def test_no_remote_groups_header_is_forbidden(trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY)
    assert response.status_code == 403


def test_wrong_group_is_forbidden(trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users"})
    assert response.status_code == 403


def test_multiple_wrong_groups_is_forbidden(trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users,staff,guests"})
    assert response.status_code == 403


def test_correct_group_is_allowed(mock_create_access_code, trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "admins"})
    assert response.status_code == 200


def test_correct_group_among_multiple_is_allowed(mock_create_access_code, trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users,admins,staff"})
    assert response.status_code == 200


def test_empty_remote_groups_header_is_forbidden(trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": ""})
    assert response.status_code == 403


def test_whitespace_group_names_are_handled(mock_create_access_code, trust_headers_enabled):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": " admins "})
    assert response.status_code == 200
