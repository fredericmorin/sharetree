"""Tests for POST /api/v1/access/activate."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from sharetree.app import app

ACTIVATE_URL = "/api/v1/access/activate"


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_activate_unclaimed_code_succeeds(client):
    with patch("sharetree.api.access.access_service.is_access_code_unclaimed", return_value=True), patch(
        "sharetree.api.access.access_service.prune_invalid_access_codes", return_value=["abc123"]
    ), patch("sharetree.api.access.access_service.set_access_code_session") as mock_claim:
        res = client.post(ACTIVATE_URL, json={"code": "abc123"})

    assert res.status_code == 200
    assert res.json()["error_code"] is None
    mock_claim.assert_called_once()


def test_activate_claimed_code_returns_404(client):
    with patch("sharetree.api.access.access_service.is_access_code_unclaimed", return_value=False):
        res = client.post(ACTIVATE_URL, json={"code": "claimed"})

    assert res.status_code == 404
    assert res.json()["error_code"] == "NOT_FOUND"


def test_activate_nonexistent_code_returns_404(client):
    with patch("sharetree.api.access.access_service.is_access_code_unclaimed", return_value=False):
        res = client.post(ACTIVATE_URL, json={"code": "doesnotexist"})

    assert res.status_code == 404


def test_activate_already_active_code_returns_already_active(client):
    # Simulate a code already in the session by activating it once, then again.
    with patch("sharetree.api.access.access_service.is_access_code_unclaimed", return_value=True), patch(
        "sharetree.api.access.access_service.prune_invalid_access_codes", return_value=["abc123"]
    ), patch("sharetree.api.access.access_service.set_access_code_session"):
        client.post(ACTIVATE_URL, json={"code": "abc123"})

    # Second activation: code is now in session, so unclaimed check is skipped;
    # prune returns it as still valid.
    with patch(
        "sharetree.api.access.access_service.prune_invalid_access_codes", return_value=["abc123"]
    ):
        res = client.post(ACTIVATE_URL, json={"code": "abc123"})

    assert res.status_code == 200
    assert res.json()["error_code"] == "ALREADY_ACTIVE"


def test_activate_claimed_code_does_not_call_set_session(client):
    with patch("sharetree.api.access.access_service.is_access_code_unclaimed", return_value=False), patch(
        "sharetree.api.access.access_service.set_access_code_session"
    ) as mock_claim:
        client.post(ACTIVATE_URL, json={"code": "claimed"})

    mock_claim.assert_not_called()


def test_activate_records_session_id_on_first_claim(client):
    with patch("sharetree.api.access.access_service.is_access_code_unclaimed", return_value=True), patch(
        "sharetree.api.access.access_service.prune_invalid_access_codes", return_value=["newcode"]
    ), patch("sharetree.api.access.access_service.set_access_code_session") as mock_claim:
        client.post(ACTIVATE_URL, json={"code": "newcode"})

    mock_claim.assert_called_once()
    code_arg, session_id_arg = mock_claim.call_args.args
    assert code_arg == "newcode"
    assert isinstance(session_id_arg, str) and len(session_id_arg) > 0
