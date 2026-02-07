"""Tests for tiny UI abstraction wrapper."""

from __future__ import annotations

from dsa_coach.ui import UI


def test_print_styled_plain_falls_back_to_stdout(capsys):
    ui = UI(rich_available=False, console=None)

    ui.print_styled("hello world", style="bold")

    out = capsys.readouterr().out
    assert "hello world" in out


def test_print_panel_plain_renders_title_and_content(capsys):
    ui = UI(rich_available=False, console=None)

    ui.print_panel("Test Panel", "Panel body", style="cyan")

    out = capsys.readouterr().out
    assert "Test Panel" in out
    assert "Panel body" in out
    assert "=" * 50 in out


def test_print_styled_uses_rich_console_when_available():
    calls: list[tuple] = []

    class FakeConsole:
        def print(self, *args, **kwargs):
            calls.append((args, kwargs))

    ui = UI(rich_available=True, console=FakeConsole())

    ui.print_styled("styled text", style="red")

    assert calls
    assert calls[0][0] == ("styled text",)
    assert calls[0][1] == {"style": "red"}


def test_print_panel_uses_rich_panel_when_available():
    calls: list[tuple] = []

    class FakeConsole:
        def print(self, *args, **kwargs):
            calls.append((args, kwargs))

    ui = UI(rich_available=True, console=FakeConsole())

    ui.print_panel("Panel Title", "Body content", style="green")

    assert calls
    assert len(calls[0][0]) == 1
    panel_obj = calls[0][0][0]
    assert "Panel Title" in str(panel_obj.title)
    assert panel_obj.border_style == "green"
