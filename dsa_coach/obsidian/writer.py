"""Write notes to Obsidian vault with atomic operations.

Handles file I/O with proper error handling, directory creation,
and atomic writes to prevent data loss.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_vault_path() -> Path | None:
    """Get Obsidian vault path from environment.

    Returns:
        Path to vault, or None if not configured
    """
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()
    if not vault_path:
        return None

    path = Path(vault_path).expanduser()
    return path if path.exists() else None


def ensure_vault_structure() -> dict[str, Path | None]:
    """Ensure Patterns/ and Problems/ subdirectories exist.

    Returns:
        Dict with 'patterns', 'problems', and 'vault' paths (None if not configured)
    """
    vault = get_vault_path()
    if not vault:
        return {"vault": None, "patterns": None, "problems": None}

    patterns_dir = vault / "Patterns"
    problems_dir = vault / "Problems"

    try:
        patterns_dir.mkdir(parents=True, exist_ok=True)
        problems_dir.mkdir(parents=True, exist_ok=True)

        # Create Advanced subfolder for complex pattern variations
        (patterns_dir / "Advanced").mkdir(exist_ok=True)

        return {
            "vault": vault,
            "patterns": patterns_dir,
            "problems": problems_dir,
        }
    except Exception as e:
        return {"vault": vault, "patterns": None, "problems": None, "error": str(e)}


def write_note(
    content: str,
    filename: str,
    note_type: Literal["pattern", "problem"] = "pattern",
    overwrite: bool = False,
) -> tuple[bool, str, Path | None]:
    """Write note to vault with atomic operation.

    Args:
        content: Complete markdown content
        filename: Note filename (e.g., "sliding-window.md")
        note_type: "pattern" or "problem"
        overwrite: Whether to overwrite existing file

    Returns:
        (success: bool, message: str, filepath: Path | None)
    """
    structure = ensure_vault_structure()

    if not structure["vault"]:
        return (False, "OBSIDIAN_VAULT_PATH not configured in .env", None)

    target_dir = (
        structure["patterns"] if note_type == "pattern" else structure["problems"]
    )

    if not target_dir:
        return (False, f"Could not create {note_type} directory", None)

    filepath = target_dir / filename

    # Check if file exists
    if filepath.exists() and not overwrite:
        return (False, f"Note already exists: {filepath}", filepath)

    try:
        # Atomic write: write to temp file, then rename
        temp_path = filepath.with_suffix(".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(filepath)

        return (True, f"Note created: {filepath}", filepath)
    except Exception as e:
        return (False, f"Failed to write note: {e}", None)


def list_existing_notes(
    note_type: Literal["pattern", "problem", "all"] = "all",
) -> list[dict[str, str]]:
    """List existing notes in vault.

    Args:
        note_type: "pattern", "problem", or "all"

    Returns:
        List of dicts with 'name', 'type', 'path'
    """
    structure = ensure_vault_structure()

    if not structure["vault"]:
        return []

    notes = []

    if note_type in ("pattern", "all") and structure["patterns"]:
        patterns_dir = structure["patterns"]
        for path in patterns_dir.rglob("*.md"):
            notes.append(
                {
                    "name": path.stem,
                    "type": "pattern",
                    "path": str(path),
                    "relative_path": str(path.relative_to(structure["vault"])),
                }
            )

    if note_type in ("problem", "all") and structure["problems"]:
        problems_dir = structure["problems"]
        for path in problems_dir.glob("*.md"):
            notes.append(
                {
                    "name": path.stem,
                    "type": "problem",
                    "path": str(path),
                    "relative_path": str(path.relative_to(structure["vault"])),
                }
            )

    return sorted(notes, key=lambda x: x["name"])


def update_note(
    filepath: Path, new_section: str, section_title: str = ""
) -> tuple[bool, str]:
    """Append new section to existing note without breaking structure.

    Args:
        filepath: Path to existing note
        new_section: Content to append
        section_title: Optional section header

    Returns:
        (success: bool, message: str)
    """
    if not filepath.exists():
        return (False, "Note does not exist")

    try:
        content = filepath.read_text(encoding="utf-8")

        # Add separator and new section
        if section_title:
            update = f"\n\n---\n\n## {section_title}\n\n{new_section}"
        else:
            update = f"\n\n{new_section}"

        updated_content = content + update

        # Atomic write
        temp_path = filepath.with_suffix(".tmp")
        temp_path.write_text(updated_content, encoding="utf-8")
        temp_path.replace(filepath)

        return (True, f"Note updated: {filepath}")
    except Exception as e:
        return (False, f"Failed to update note: {e}")


def note_exists(
    filename: str, note_type: Literal["pattern", "problem"] = "pattern"
) -> bool:
    """Check if a note already exists."""
    structure = ensure_vault_structure()
    target_dir = (
        structure["patterns"] if note_type == "pattern" else structure["problems"]
    )

    if not target_dir:
        return False

    return (target_dir / filename).exists()
