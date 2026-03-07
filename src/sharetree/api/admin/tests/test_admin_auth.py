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


@pytest.fixture(autouse=True)
def patch_admin_groups():
    with patch("sharetree.api.admin.deps.settings") as mock_settings:
        mock_settings.ADMIN_GROUPS = ["admins"]
        yield


@pytest.fixture()
def mock_create_access_code():
    with patch("sharetree.services.access.create_access_code", return_value="testcode123") as mock:
        yield mock


def test_no_remote_groups_header_is_forbidden():
    response = client.post(ADMIN_URL, json=VALID_BODY)
    assert response.status_code == 403


def test_wrong_group_is_forbidden():
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users"})
    assert response.status_code == 403


def test_multiple_wrong_groups_is_forbidden():
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users,staff,guests"})
    assert response.status_code == 403


def test_correct_group_is_allowed(mock_create_access_code):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "admins"})
    assert response.status_code == 200


def test_correct_group_among_multiple_is_allowed(mock_create_access_code):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": "users,admins,staff"})
    assert response.status_code == 200


def test_empty_remote_groups_header_is_forbidden():
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": ""})
    assert response.status_code == 403


def test_whitespace_group_names_are_handled(mock_create_access_code):
    response = client.post(ADMIN_URL, json=VALID_BODY, headers={"Remote-Groups": " admins "})
    assert response.status_code == 200
