"""Analyze learning sessions to determine when notes should be created."""

from __future__ import annotations


def should_create_note(
    pattern: str,
    progress: float,
    session_messages: int,
    progress_gain: float,
) -> tuple[bool, str]:
    """Determine if a pattern note should be created after a learning session.

    Args:
        pattern: Pattern name
        progress: Current progress level
        session_messages: Number of messages in session
        progress_gain: Progress increase from session

    Returns:
        (should_create: bool, reason: str)
    """
    # Don't create note if session was too short
    if session_messages < 4:
        return (False, "Session too short (< 4 messages)")

    # Create note if progress is now above threshold (pattern understood)
    if progress >= 40 and progress_gain > 10:
        return (
            True,
            f"Pattern learned (progress: {progress:.0f}%, gain: +{progress_gain:.0f}%)",
        )

    # Create note if session was substantial even if progress is still low
    if session_messages >= 10:
        return (True, f"Substantial session ({session_messages} messages)")

    return (False, "Session didn't meet thresholds for note creation")
