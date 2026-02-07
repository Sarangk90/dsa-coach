"""Regression tests for terminal fallback (non-rich) output paths."""

from __future__ import annotations

import pytest

from dsa_coach.agent import terminal


@pytest.fixture
def plain_ui(monkeypatch):
    monkeypatch.setattr(terminal, "RICH_AVAILABLE", False)
    monkeypatch.setattr(terminal, "PROMPT_TOOLKIT_AVAILABLE", False)
    return terminal.TerminalUI()


def test_basic_render_methods_print_plain_output(plain_ui, capsys):
    plain_ui.print_header()
    plain_ui.render_message("user", "hello")
    plain_ui.render_message("assistant", "world")
    plain_ui.render_tool_activity("get_hint")
    plain_ui.render_error("oops")
    plain_ui.render_tool_error("tool", "bad")
    plain_ui.render_success("ok")
    plain_ui.render_info("info")
    plain_ui.render_welcome("welcome")
    plain_ui.render_goodbye()
    plain_ui.render_help()
    plain_ui.render_thinking()
    plain_ui.render_reasoning("reasoning text")

    out = capsys.readouterr().out
    assert "DSA Coach - Your AI Mentor" in out
    assert "hello" in out
    assert "● world" in out
    assert "[Running: get_hint...]" in out
    assert "✗ oops" in out
    assert "✗ tool failed: bad" in out
    assert "✅ ok" in out
    assert "welcome" in out
    assert "Keep grinding!" in out
    assert "Commands:" in out
    assert "∴ Thinking..." in out
    assert "reasoning text" in out


def test_render_session_picker_plain_output(plain_ui, capsys):
    plain_ui.render_session_picker(
        [
            {
                "updated_at": "2026-02-01T10:00:00",
                "first_message": "Need help with arrays",
                "message_count": 3,
            }
        ]
    )
    out = capsys.readouterr().out
    assert "Recent Sessions" in out
    assert "Need help with arrays" in out
    assert "3 messages" in out


def test_render_conversation_history_plain_output(plain_ui, capsys):
    plain_ui.render_conversation_history(
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
        ]
    )
    out = capsys.readouterr().out
    assert "Resumed Conversation" in out
    assert "▌ u1" in out
    assert "● a1" in out


@pytest.mark.asyncio
async def test_get_input_fallback_handles_keyboard_interrupt(plain_ui, monkeypatch):
    def raise_interrupt(_prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)
    assert await plain_ui.get_input() is None
