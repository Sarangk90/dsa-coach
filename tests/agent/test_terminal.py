"""Tests for terminal helpers and lightweight UI behavior."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from dsa_coach.agent import terminal


def test_format_time_ago_variants():
    now = datetime.now()

    assert terminal.format_time_ago(now - timedelta(seconds=20)) == "just now"
    assert terminal.format_time_ago(now - timedelta(minutes=2)) == "2 mins ago"
    assert terminal.format_time_ago(now - timedelta(hours=3)) == "3 hours ago"
    assert terminal.format_time_ago(now - timedelta(days=1, minutes=1)) == "yesterday"
    assert terminal.format_time_ago(now - timedelta(days=5)) == "5 days ago"


def test_truncate_preview_normalizes_whitespace_and_applies_ellipsis():
    text = "line one\nline two\t  line three"

    assert terminal.truncate_preview("", max_len=10) == ""
    assert terminal.truncate_preview("short", max_len=10) == "short"
    assert terminal.truncate_preview(text, max_len=18) == "line one line t..."


def test_terminal_ui_format_elapsed_time(monkeypatch):
    monkeypatch.setattr(terminal, "RICH_AVAILABLE", False)
    monkeypatch.setattr(terminal, "PROMPT_TOOLKIT_AVAILABLE", False)

    ui = terminal.TerminalUI()

    assert ui._format_elapsed_time() == ""

    ui.session_start_time = datetime.now() - timedelta(seconds=65)
    elapsed = ui._format_elapsed_time()
    assert elapsed.startswith("01:")

    ui.session_start_time = datetime.now() - timedelta(hours=1, minutes=2, seconds=3)
    elapsed = ui._format_elapsed_time()
    assert elapsed.startswith("1:02:")


@pytest.mark.asyncio
async def test_get_session_selection_valid_and_invalid(monkeypatch):
    monkeypatch.setattr(terminal, "RICH_AVAILABLE", False)
    monkeypatch.setattr(terminal, "PROMPT_TOOLKIT_AVAILABLE", False)
    ui = terminal.TerminalUI()

    monkeypatch.setattr("builtins.input", lambda: "2")
    assert await ui.get_session_selection(3) == 1

    monkeypatch.setattr("builtins.input", lambda: "x")
    assert await ui.get_session_selection(3) is None

    monkeypatch.setattr("builtins.input", lambda: "9")
    assert await ui.get_session_selection(3) is None

    monkeypatch.setattr("builtins.input", lambda: "c")
    assert await ui.get_session_selection(3) is None


@pytest.mark.asyncio
async def test_get_input_fallback_double_enter(monkeypatch):
    monkeypatch.setattr(terminal, "RICH_AVAILABLE", False)
    monkeypatch.setattr(terminal, "PROMPT_TOOLKIT_AVAILABLE", False)
    ui = terminal.TerminalUI()

    lines = iter(["first line", "second line", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(lines))

    assert await ui.get_input(prompt="> ") == "first line\nsecond line"
