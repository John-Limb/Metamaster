"""Tests for the admin password reset CLI."""
import sys
from unittest.mock import MagicMock, patch

import pytest


def test_reset_admin_password_updates_hash_and_revokes_tokens(capsys):
    """Happy path: admin user found, password_hash updated, tokens revoked."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "admin"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    mock_auth_service = MagicMock()
    mock_auth_service.revoke_all_user_tokens.return_value = 3

    with (
        patch("app.core.reset_password.SessionLocal", return_value=mock_db),
        patch(
            "app.core.reset_password.generate_random_password",
            return_value="TestPass1!",
        ),
        patch("app.core.reset_password.hash_password", return_value="hashed_value"),
        patch("app.core.reset_password.AuthService", return_value=mock_auth_service),
    ):
        from app.core.reset_password import reset_admin_password

        reset_admin_password()

    assert mock_user.password_hash == "hashed_value"
    assert mock_user.requires_password_change is True
    mock_db.commit.assert_called_once()
    mock_auth_service.revoke_all_user_tokens.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "TestPass1!" in captured.out
    assert "admin" in captured.out


def test_reset_admin_password_exits_when_no_admin(capsys):
    """No admin user in DB: print error and exit with code 1."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with (
        patch("app.core.reset_password.SessionLocal", return_value=mock_db),
        pytest.raises(SystemExit) as exc_info,
    ):
        from app.core.reset_password import reset_admin_password

        reset_admin_password()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "No admin user found" in captured.out


def test_reset_admin_password_closes_db_on_exception(capsys):
    """DB session is always closed, even if an exception occurs mid-reset."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = RuntimeError("DB exploded")

    with (
        patch("app.core.reset_password.SessionLocal", return_value=mock_db),
        pytest.raises(RuntimeError),
    ):
        from app.core.reset_password import reset_admin_password

        reset_admin_password()

    mock_db.close.assert_called_once()
