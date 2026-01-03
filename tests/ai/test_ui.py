from __future__ import annotations

import os
from unittest.mock import patch


def test_get_user_prompt_plain_when_not_tty() -> None:
    from dsa_coach.ai.ui import get_user_prompt

    with patch("sys.stdout.isatty", return_value=False):
        assert get_user_prompt("You") == "\nYou > "


def test_get_user_prompt_plain_when_no_color_set() -> None:
    from dsa_coach.ai.ui import get_user_prompt

    with (
        patch("sys.stdout.isatty", return_value=True),
        patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False),
    ):
        assert get_user_prompt("You") == "\nYou > "


def test_get_user_prompt_funky_when_tty_and_color_allowed() -> None:
    from dsa_coach.ai.ui import READING_WIDTH, get_user_prompt

    with (
        patch("sys.stdout.isatty", return_value=True),
        patch.dict(os.environ, {"COACH_CHAT_STYLE": "classic"}, clear=True),
        patch("shutil.get_terminal_size", return_value=os.terminal_size((120, 40))),
    ):
        s = get_user_prompt("You")

    # Divider length is capped at reading width.
    assert ("─" * READING_WIDTH) in s
    # Funky label
    assert "🧑 You" in s
    # ANSI (bold/dim) should be present
    assert "\033[" in s


def test_get_user_prompt_discord_mode_is_compact() -> None:
    from dsa_coach.ai.ui import get_user_prompt

    with (
        patch("sys.stdout.isatty", return_value=True),
        # Clear env to ensure NO_COLOR doesn't force the plain fallback.
        patch.dict(os.environ, {"COACH_CHAT_STYLE": "discord"}, clear=True),
    ):
        s = get_user_prompt("You")

    # Discord mode should not include the big divider spam.
    assert "─" not in s
    assert "🧑 You" in s


def test_get_user_prompt_defaults_to_discord_style() -> None:
    from dsa_coach.ai.ui import get_user_prompt

    with (
        patch("sys.stdout.isatty", return_value=True),
        patch.dict(os.environ, {}, clear=True),
    ):
        s = get_user_prompt("You")

    assert "─" not in s
    assert "🧑 You" in s
