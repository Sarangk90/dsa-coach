"""Regression tests for note creation decision thresholds."""

from __future__ import annotations

from dsa_coach.obsidian.analyzer import should_create_note


def test_should_create_note_rejects_short_sessions():
    create, reason = should_create_note(
        pattern="graphs",
        progress=90,
        session_messages=3,
        progress_gain=50,
    )
    assert create is False
    assert "too short" in reason


def test_should_create_note_accepts_progress_threshold():
    create, reason = should_create_note(
        pattern="graphs",
        progress=45,
        session_messages=6,
        progress_gain=15,
    )
    assert create is True
    assert "Pattern learned" in reason


def test_should_create_note_accepts_substantial_session_even_with_low_progress():
    create, reason = should_create_note(
        pattern="graphs",
        progress=20,
        session_messages=12,
        progress_gain=5,
    )
    assert create is True
    assert "Substantial session" in reason


def test_should_create_note_rejects_when_thresholds_not_met():
    create, reason = should_create_note(
        pattern="graphs",
        progress=30,
        session_messages=5,
        progress_gain=5,
    )
    assert create is False
    assert "didn't meet thresholds" in reason
