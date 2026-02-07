"""Smoke tests for basic entrypoint functionality."""

import coach


def test_coach_entrypoint_exposes_main():
    """Entry module should expose a callable main function."""
    assert callable(coach.main)
