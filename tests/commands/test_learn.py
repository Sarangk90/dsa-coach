from unittest.mock import patch

import pytest

from dsa_coach.commands import learn
from dsa_coach.progress import save_progress


@pytest.mark.skip(
    reason="TODO: Rewrite test - learn command changed, uses deprecated progress API"
)
def test_learn_specific_pattern(populated_progress, capsys):
    """Test learning a specific pattern shows the dashboard and allows diagnose."""
    # Now shows a pattern-first dashboard. User selects option 1 (Diagnose)
    # and the test verifies mentor.interactive_learning_session is called.
    with (
        patch("mentor.interactive_learning_session") as mock_session,
        patch("dsa_coach.commands.learn.get_all_quests", return_value=[]),
        patch("builtins.input", return_value="1"),
    ):  # Choose "Diagnose My Level"
        learn.cmd_learn("sliding_window")

    # Verify we showed the pattern dashboard
    captured = capsys.readouterr()
    assert "sliding_window" in captured.out.lower() or "Sliding Window" in captured.out

    # Verify learning session was started
    mock_session.assert_called_once()
    args = mock_session.call_args[0]
    assert args[0] == "sliding_window"


@pytest.mark.skip(
    reason="TODO: Rewrite test - learn command changed, uses deprecated progress API"
)
def test_learn_weakest_pattern(populated_progress, capsys):
    """Test learning without pattern shows pattern selection."""
    # Setup progress with weakest pattern
    from dsa_coach.progress import load_progress

    progress = load_progress()
    progress["pattern_proficiency"]["sliding_window"] = {"confidence": 10.0}
    progress["pattern_proficiency"]["two_pointers"] = {"confidence": 50.0}
    save_progress(progress)

    # When no pattern specified, cmd_learn shows a pattern selection menu
    # Then the pattern dashboard. User selects option 1 (Diagnose).
    # Mock inputs:
    # "1" for sliding_window from list
    # "1" for diagnose
    # "n" for "Start this problem now? [Y/n]"

    with (
        patch("mentor.interactive_learning_session") as mock_session,
        patch("dsa_coach.commands.learn.get_all_quests", return_value=[]),
        patch("builtins.input", side_effect=["1", "1", "n"]),
    ):
        learn.cmd_learn()

    mock_session.assert_called_once()
    args = mock_session.call_args[0]
    assert args[0] == "sliding_window"
