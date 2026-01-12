from unittest.mock import MagicMock, patch

from dsa_coach.commands import status
from dsa_coach.storage.models import PatternProgress, UserProfile


def test_status_output(capsys):
    with patch("dsa_coach.commands.status.SyncDatabase") as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db

        # Mock profile with custom name (not default "DSA Learner")
        mock_db.get_or_create_profile.return_value = UserProfile(
            id="default", name="Test User", quests_completed=5
        )
        mock_db.get_all_pattern_progress.return_value = [
            PatternProgress(
                id="default_arrays_hashing",
                user_id="default",
                pattern_id="arrays_hashing",
                confidence=80,
            )
        ]
        mock_db.get_completed_quests.return_value = []
        mock_db.get_latest_session.return_value = None
        mock_db.get_due_reviews.return_value = []

        status.cmd_status()

    captured = capsys.readouterr()
    assert "Test User" in captured.out
    assert "Completed" in captured.out


def test_status_no_profile(capsys):
    with patch("dsa_coach.commands.status.SyncDatabase") as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db

        # Return default profile (DSA Learner) which triggers "no profile" message
        mock_db.get_or_create_profile.return_value = UserProfile(
            id="default", name="DSA Learner"
        )
        mock_db.get_all_pattern_progress.return_value = []
        mock_db.get_completed_quests.return_value = []
        mock_db.get_latest_session.return_value = None
        mock_db.get_due_reviews.return_value = []

        status.cmd_status()

    captured = capsys.readouterr()
    assert "No profile found" in captured.out
