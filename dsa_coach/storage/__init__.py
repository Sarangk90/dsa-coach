"""Storage module for DSA Coach.

This module provides data persistence through two mechanisms:

**SQLite Database (coach.db)** - Used by agent mode:
- User profiles and progress tracking
- Pattern proficiency and quest completions
- AI conversation sessions and messages
- Concept understanding tracking

**JSON Files** - Used for static data:
- quests.json: Static curriculum data (read-only)
"""

import json
from pathlib import Path
from typing import Any

from .db import Database
from .models import (
    ConceptUnderstanding,
    Message,
    PatternProgress,
    QuestCompletion,
    Session,
    UserProfile,
)

# ==================== JSON Storage ====================


def load_json(filepath: Path) -> dict[str, Any]:
    """Load JSON from disk; return empty dict if file does not exist.

    Used for:
    - quests.json (static curriculum data)

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data or empty dict if file doesn't exist
    """
    if filepath.exists():
        with filepath.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


__all__ = [
    # New SQLite storage
    "Database",
    "Session",
    "Message",
    "UserProfile",
    "PatternProgress",
    "QuestCompletion",
    "ConceptUnderstanding",
    # JSON helpers
    "load_json",
]
