"""Conversation persistence for AI mentorship sessions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dsa_coach.paths import CONVERSATIONS_DIR
from dsa_coach.storage import load_json, save_json


def save_conversation(
    session_type: str, session_id: str, messages: list, metadata: dict | None = None
) -> Path:
    """Save conversation to disk for later resumption.

    Args:
        session_type: Type of session ("learn" or "design")
        session_id: Unique identifier (pattern name or design id)
        messages: List of message dicts
        metadata: Optional metadata dict

    Returns:
        Path to saved conversation file
    """
    conversation = {
        "session_type": session_type,
        "session_id": session_id,
        "messages": messages,
        "metadata": metadata or {},
        "saved_at": datetime.now().isoformat(),
    }

    filepath = CONVERSATIONS_DIR / f"{session_type}_{session_id}.json"
    save_json(filepath, conversation)

    return filepath


def load_conversation(session_type: str, session_id: str) -> dict | None:
    """Load a saved conversation if it exists.

    Args:
        session_type: Type of session ("learn" or "design")
        session_id: Unique identifier

    Returns:
        Conversation dict or None if not found
    """
    filepath = CONVERSATIONS_DIR / f"{session_type}_{session_id}.json"

    if filepath.exists():
        return load_json(filepath)
    return None


def delete_conversation(session_type: str, session_id: str) -> None:
    """Delete a saved conversation.

    Args:
        session_type: Type of session
        session_id: Unique identifier
    """
    filepath = CONVERSATIONS_DIR / f"{session_type}_{session_id}.json"
    if filepath.exists():
        filepath.unlink()


def list_saved_conversations() -> list[dict]:
    """List all saved conversations.

    Returns:
        List of conversation metadata dicts
    """
    conversations = []

    for filepath in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with filepath.open() as f:
                data = json.load(f)
                conversations.append(
                    {
                        "type": data.get("session_type", "unknown"),
                        "id": data.get("session_id", filepath.stem),
                        "messages": len(data.get("messages", [])),
                        "saved_at": data.get("saved_at", "unknown"),
                    }
                )
        except Exception:
            pass

    return conversations
