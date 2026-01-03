"""Test natural multiline input (double-Enter to send, like Claude Code)."""

from __future__ import annotations

from unittest.mock import patch


def test_natural_multiline_double_enter_sends() -> None:
    """Ensure the natural multiline reader sends on double-Enter."""
    from dsa_coach.ai import interactive_learning_session

    with (
        patch("dsa_coach.ai.session.load_conversation", return_value=None),
        patch(
            "dsa_coach.ai.learning.start_learning_session",
            return_value=([{"role": "user", "content": "x"}], "hi"),
        ),
        patch("dsa_coach.ai.ui.print_ai_response"),
        patch(
            "dsa_coach.ai.learning._read_multiline_natural",
            side_effect=[
                "line1\nline2",  # multi-line message
                "pause",  # then pause
            ],
        ),
        patch("builtins.input", side_effect=["t"]),
        patch("sys.stdin.isatty", return_value=True),
        patch("dsa_coach.ai.session.save_conversation"),
        patch(
            "dsa_coach.ai.learning.continue_conversation", return_value=([], "ok")
        ) as mock_continue,
    ):
        interactive_learning_session(
            "sliding_window",
            progress={"profile": {}, "pattern_proficiency": {}},
            quests=[],
        )

    # The natural multiline reader should deliver multi-line messages as one.
    assert mock_continue.call_args.args[1] == "line1\nline2"
