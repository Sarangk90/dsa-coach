"""Storage module for DSA Coach.

This module provides data persistence through two mechanisms:

**SQLite Database (coach.db)** - Used by agent mode:
- User profiles and progress tracking
- Pattern proficiency and quest completions
- AI conversation sessions and messages
- Concept understanding tracking

**JSON Files** - Used for static and file-based data:
- quests.json: Static curriculum data (read-only)
- conversations/*.json: AI session persistence (optional backup)
"""

import contextlib
import json
import os
import tempfile
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
    - conversations/*.json (AI session backups)

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data or empty dict if file doesn't exist
    """
    if filepath.exists():
        with filepath.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filepath: Path, data: dict[str, Any]) -> None:
    """Atomically save JSON to disk.

    Writes to a temp file in the same directory then replaces the target path.
    This reduces the risk of partially-written or corrupted data.

    Used for:
    - conversations/*.json (AI session persistence)

    Args:
        filepath: Path to JSON file
        data: Dictionary to serialize as JSON

    Raises:
        OSError: If file operations fail
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{filepath.name}.", dir=str(filepath.parent)
    )
    tmp_path_obj = Path(tmp_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        tmp_path_obj.replace(filepath)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp_path_obj.unlink()


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
    "save_json",
]
