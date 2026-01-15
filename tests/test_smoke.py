"""Smoke tests for basic CLI functionality."""

import coach


def test_status_no_profile(clean_progress):
    """Test status command when no profile exists."""
    # Should print error but not crash
    coach.cmd_status()
