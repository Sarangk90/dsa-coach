from unittest.mock import MagicMock, patch

from dsa_coach.commands import hint
from dsa_coach.storage.models import PatternProgress, Session


def test_hint_no_active_quest(capsys):
    with patch("dsa_coach.commands.hint.SyncDatabase") as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.get_latest_session.return_value = None

        hint.cmd_hint()

    captured = capsys.readouterr()
    assert "No active quest" in captured.out


def test_hint_static(capsys):
    quest = {"id": "q1", "pattern": "sliding_window", "hints": {"low": "Static Hint"}}

    # Mock the AI import to fail, forcing static hints
    import sys

    mock_ai = MagicMock()
    mock_ai.get_adaptive_hint.side_effect = ImportError

    with (
        patch("dsa_coach.commands.hint.SyncDatabase") as mock_db_class,
        patch("dsa_coach.commands.hint.get_all_quests", return_value=[quest]),
        patch.dict(sys.modules, {"dsa_coach.ai": None}),  # Block AI import
    ):
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.get_latest_session.return_value = Session(id="test", current_quest="q1")
        mock_db.get_pattern_progress.return_value = PatternProgress(
            id="default_sliding_window",
            user_id="default",
            pattern_id="sliding_window",
            confidence=10,
        )

        hint.cmd_hint()

    captured = capsys.readouterr()
    assert "Static Hint" in captured.out


def test_hint_ai(capsys):
    quest = {"id": "q1", "pattern": "sliding_window", "hints": {"low": "Static Hint"}}

    with (
        patch("dsa_coach.commands.hint.SyncDatabase") as mock_db_class,
        patch("dsa_coach.commands.hint.get_all_quests", return_value=[quest]),
        patch("dsa_coach.ai.get_adaptive_hint", return_value="AI Hint"),
    ):
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.get_latest_session.return_value = Session(id="test", current_quest="q1")
        mock_db.get_pattern_progress.return_value = PatternProgress(
            id="default_sliding_window",
            user_id="default",
            pattern_id="sliding_window",
            confidence=10,
        )

        hint.cmd_hint()

    captured = capsys.readouterr()
    assert "AI Hint" in captured.out
