from __future__ import annotations

from unittest.mock import patch


def test_start_learning_session_teach_first_uses_existing_intro() -> None:
    from dsa_coach.ai import start_learning_session
    from dsa_coach.ai.prompts import LEARNING_SESSION_INTRO
    from dsa_coach.progress import get_default_progress

    progress = get_default_progress()

    with patch("dsa_coach.ai.learning.get_ai_response", return_value="ok") as mock_resp:
        messages, response = start_learning_session(
            "sliding_window", progress, mode="teach_first"
        )

    assert response == "ok"
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    # Ensure the prompt used is the teach-first template
    called_user_message = mock_resp.call_args.kwargs["user_message"]
    assert called_user_message == LEARNING_SESSION_INTRO.format(
        pattern="Sliding Window"
    )


def test_start_learning_session_diagnose_first_uses_diagnose_intro() -> None:
    from dsa_coach.ai import start_learning_session
    from dsa_coach.ai.prompts import LEARNING_SESSION_DIAGNOSE_INTRO
    from dsa_coach.progress import get_default_progress

    progress = get_default_progress()

    with patch("dsa_coach.ai.learning.get_ai_response", return_value="ok") as mock_resp:
        _messages, _response = start_learning_session(
            "sliding_window", progress, mode="diagnose_first"
        )

    called_user_message = mock_resp.call_args.kwargs["user_message"]
    assert called_user_message == LEARNING_SESSION_DIAGNOSE_INTRO.format(
        pattern="Sliding Window"
    )


def test_interactive_learning_session_with_explicit_mode() -> None:
    """Test that explicit mode parameter is used directly without prompting."""
    from dsa_coach.ai import interactive_learning_session

    # When mode is explicitly passed, start_learning_session should be called with that mode.
    with (
        patch("dsa_coach.ai.session.load_conversation", return_value=None),
        patch(
            "dsa_coach.ai.learning.start_learning_session",
            return_value=([{"role": "user", "content": "x"}], "hi"),
        ) as mock_start,
        patch("dsa_coach.ai.ui.print_ai_response"),
        patch(
            "dsa_coach.ai.learning._read_multiline_natural", side_effect=["pause"]
        ),  # Natural multiline reader now
        patch("sys.stdin.isatty", return_value=True),
        patch("dsa_coach.ai.session.save_conversation"),
    ):
        # Pass mode explicitly - should use it directly without prompting
        interactive_learning_session(
            "sliding_window",
            progress={"profile": {}, "pattern_proficiency": {}},
            quests=[],
            mode="diagnose_first",
        )

    assert mock_start.call_args.kwargs["mode"] == "diagnose_first"


def test_interactive_learning_session_resume_with_empty_messages_does_not_crash_and_restarts() -> (
    None
):
    from dsa_coach.ai import interactive_learning_session

    saved = {
        "saved_at": "2025-12-23T00:00:00",
        "messages": [],
        "metadata": {"pattern": "sliding_window"},
    }

    with (
        patch("dsa_coach.ai.session.load_conversation", return_value=saved),
        patch(
            "dsa_coach.ai.learning.start_learning_session",
            return_value=([{"role": "user", "content": "x"}], "hi"),
        ) as mock_start,
        patch("dsa_coach.ai.ui.print_ai_response"),
        patch("dsa_coach.ai.learning._read_multiline_natural", side_effect=["pause"]),
        patch(
            "builtins.input",
            side_effect=[
                "y",  # resume prompt
                "t",  # choose teach-first (since it will restart)
            ],
        ),
        patch("sys.stdin.isatty", return_value=True),
        patch("dsa_coach.ai.session.save_conversation"),
    ):
        interactive_learning_session(
            "sliding_window",
            progress={"profile": {}, "pattern_proficiency": {}},
            quests=[],
        )

    # Empty saved session should force a restart, not a crash.
    assert mock_start.called


def test_interactive_learning_session_autosaves_after_each_exchange() -> None:
    from dsa_coach.ai import interactive_learning_session

    # New session: start -> one message -> autosave should happen after the exchange (not only on pause).
    with (
        patch("dsa_coach.ai.session.load_conversation", return_value=None),
        patch(
            "dsa_coach.ai.learning.start_learning_session",
            return_value=([{"role": "user", "content": "x"}], "hi"),
        ),
        patch(
            "dsa_coach.ai.learning.continue_conversation",
            return_value=(
                [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "resp"},
                ],
                "resp",
            ),
        ),
        patch("dsa_coach.ai.ui.print_ai_response"),
        patch(
            "dsa_coach.ai.learning._read_multiline_natural",
            side_effect=["hello", KeyboardInterrupt()],
        ),
        patch(
            "builtins.input",
            side_effect=[
                "t",  # choose teach-first
            ],
        ),
        patch("sys.stdin.isatty", return_value=True),
        patch.dict("os.environ", {"COACH_AUTOSAVE": "1"}, clear=False),
        patch("dsa_coach.ai.session.save_conversation") as mock_save,
    ):
        interactive_learning_session(
            "sliding_window",
            progress={"profile": {}, "pattern_proficiency": {}},
            quests=[],
        )

    # Without autosave, we'd only save once in the Ctrl+C handler.
    # With autosave enabled, we should save at least once after the exchange + once on Ctrl+C.
    assert mock_save.call_count >= 2


def test_interactive_learning_session_resume_can_show_full_transcript() -> None:
    from dsa_coach.ai import interactive_learning_session

    saved = {
        "saved_at": "2025-12-23T00:00:00",
        "messages": [
            {"role": "user", "content": "Teach me Sliding Window"},
            {"role": "assistant", "content": "Intro"},
            {"role": "user", "content": "Got it"},
            {"role": "assistant", "content": "Great"},
        ],
        "metadata": {"pattern": "sliding_window"},
    }

    with (
        patch("dsa_coach.ai.session.load_conversation", return_value=saved),
        patch("dsa_coach.ai.learning._read_multiline_natural", side_effect=["pause"]),
        patch("builtins.input", side_effect=["y"]),
        patch.dict("os.environ", {"COACH_RESUME_SHOW": "all"}, clear=False),
        patch("dsa_coach.ai.ui.print_ai_response") as mock_print,
        patch("sys.stdin.isatty", return_value=True),
        patch("dsa_coach.ai.session.save_conversation"),
    ):
        interactive_learning_session(
            "sliding_window",
            progress={"profile": {}, "pattern_proficiency": {}},
            quests=[],
        )

    # Should print all non-system messages on resume (You + Mentor).
    assert mock_print.call_count >= 4


def test_multiline_input_sent_as_single_message() -> None:
    """With prompt_toolkit, user can type/paste multiline and it's sent as one message."""
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
            side_effect=["line1\nline2\nline3", EOFError()],
        ),
        patch(
            "builtins.input",
            side_effect=[
                "t",  # choose teach-first
            ],
        ),
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

    # Multiline input should be delivered as ONE message.
    assert mock_continue.call_args.args[1] == "line1\nline2\nline3"


def test_editor_command_subl_wait_is_added_when_missing() -> None:
    from dsa_coach.ai import interactive_learning_session

    # Reach :editor then exit via Ctrl+C. We only assert the subprocess command.
    with (
        patch("dsa_coach.ai.session.load_conversation", return_value=None),
        patch(
            "dsa_coach.ai.learning.start_learning_session",
            return_value=([{"role": "user", "content": "x"}], "hi"),
        ),
        patch("dsa_coach.ai.ui.print_ai_response"),
        patch(
            "dsa_coach.ai.learning._read_multiline_natural",
            side_effect=[":editor", KeyboardInterrupt()],
        ),
        patch.dict("os.environ", {"EDITOR": "subl"}, clear=False),
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.read_text", return_value="hello from editor"),
        patch(
            "builtins.input",
            side_effect=[
                "t",
            ],
        ),
        patch("sys.stdin.isatty", return_value=True),
        patch("dsa_coach.ai.session.save_conversation"),
        patch("dsa_coach.ai.learning.continue_conversation", return_value=([], "ok")),
    ):
        interactive_learning_session(
            "sliding_window",
            progress={"profile": {}, "pattern_proficiency": {}},
            quests=[],
        )

    called = mock_run.call_args.args[0]
    assert called[0] == "subl"
    assert "-w" in called


def test_editor_alias_e_works() -> None:
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
            side_effect=[":e", KeyboardInterrupt()],
        ),
        patch.dict("os.environ", {"EDITOR": "subl"}, clear=False),
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.read_text", return_value="hello from editor"),
        patch(
            "builtins.input",
            side_effect=[
                "t",
            ],
        ),
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

    assert mock_run.called
    assert mock_continue.call_args.args[1] == "hello from editor"
