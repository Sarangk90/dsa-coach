from unittest.mock import MagicMock, patch

from dsa_coach.commands import start
from dsa_coach.storage.models import UserProfile


def test_start_creates_profile(capsys):
    with (
        patch("builtins.input", return_value="TestUser"),
        patch("dsa_coach.commands.start.SyncDatabase") as mock_db_class,
    ):
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.get_or_create_profile.return_value = UserProfile(
            id="default", name="DSA Learner"
        )

        start.cmd_start()

    captured = capsys.readouterr()
    assert "Profile Created!" in captured.out
    # Verify update_profile was called
    mock_db.update_profile.assert_called_once()


def test_start_existing_profile(capsys):
    with patch("dsa_coach.commands.start.SyncDatabase") as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.get_or_create_profile.return_value = UserProfile(
            id="default", name="Test User"
        )

        start.cmd_start()

    captured = capsys.readouterr()
    assert "Welcome back" in captured.out
    assert "Test User" in captured.out
