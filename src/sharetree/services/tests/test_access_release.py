"""Tests for release_access_code service function."""

from unittest.mock import patch, MagicMock


def test_release_clears_session_id():
    mock_row = MagicMock()
    mock_session = MagicMock()
    mock_session.get.return_value = mock_row
    mock_session.__enter__ = lambda s: mock_session
    mock_session.__exit__ = MagicMock(return_value=False)

    with patch("sharetree.services.access.get_session", return_value=mock_session):
        from sharetree.services.access import release_access_code

        result = release_access_code("somecode")

    assert result is True
    assert mock_row.session_id is None
    mock_session.commit.assert_called_once()


def test_release_nonexistent_code_returns_false():
    mock_session = MagicMock()
    mock_session.get.return_value = None
    mock_session.__enter__ = lambda s: mock_session
    mock_session.__exit__ = MagicMock(return_value=False)

    with patch("sharetree.services.access.get_session", return_value=mock_session):
        from sharetree.services.access import release_access_code

        result = release_access_code("nonexistent")

    assert result is False
    mock_session.commit.assert_not_called()
