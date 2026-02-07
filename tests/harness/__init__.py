"""Test harness for DSA Coach.

This module provides a programmatic interface for testing the SDK agent,
including conversation management and state inspection.
"""

from .coach_harness import CoachTestHarness, ConversationResponse, DatabaseSnapshot

__all__ = ["CoachTestHarness", "ConversationResponse", "DatabaseSnapshot"]
