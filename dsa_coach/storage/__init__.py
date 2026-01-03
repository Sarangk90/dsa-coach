"""Storage module for DSA Coach.

This module provides data persistence through two mechanisms:

**SQLite Database (coach.db)** - Used by agent mode:
- User profiles and progress tracking
- Pattern proficiency and quest completions
- AI conversation sessions and messages
- Concept understanding tracking

**JSON Files** - Used by legacy CLI and static data:
- quests.json: Static curriculum data (read-only)
- progress.json: Legacy user progress (V1 CLI commands)
- conversations/*.json: AI session persistence (optional backup)

The dual system exists during migration from V1 (JSON) to V2 (SQLite).
Legacy CLI commands use JSON for simplicity and backward compatibility.
Agent mode uses SQLite for better concurrency and querying.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from .db import Database
from .models import (
    Session,
    Message,
    UserProfile,
    PatternProgress,
    QuestCompletion,
    ConceptUnderstanding,
)


# ==================== JSON Storage (Legacy & Static Data) ====================


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON from disk; return empty dict if file does not exist.

    Used for:
    - quests.json (static curriculum data)
    - progress.json (legacy V1 CLI progress)
    - conversations/*.json (AI session backups)

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data or empty dict if file doesn't exist
    """
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filepath: Path, data: Dict[str, Any]) -> None:
    """Atomically save JSON to disk.

    Writes to a temp file in the same directory then replaces the target path.
    This reduces the risk of partially-written or corrupted data.

    Used for:
    - progress.json (legacy V1 CLI progress)
    - conversations/*.json (AI session persistence)

    Args:
        filepath: Path to JSON file
        data: Dictionary to serialize as JSON

    Raises:
        OSError: If file operations fail
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{filepath.name}.", dir=str(filepath.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


__all__ = [
    # New SQLite storage
    "Database",
    "Session",
    "Message",
    "UserProfile",
    "PatternProgress",
    "QuestCompletion",
    "ConceptUnderstanding",
    # Legacy JSON storage
    "load_json",
    "save_json",
]

