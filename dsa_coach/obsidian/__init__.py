"""Obsidian integration for atomic note creation.

This module handles creation of interview-focused atomic notes
following the user's Obsidian workflow with proper structure,
cross-linking, and quality enforcement.
"""

from .analyzer import analyze_learning_session, should_create_note
from .note_generator import (
    generate_pattern_note,
    generate_problem_note,
    get_filename_for_pattern,
    get_filename_for_problem,
)
from .writer import (
    ensure_vault_structure,
    get_vault_path,
    list_existing_notes,
    note_exists,
    update_note,
    write_note,
)

__all__ = [
    "generate_pattern_note",
    "generate_problem_note",
    "get_filename_for_pattern",
    "get_filename_for_problem",
    "write_note",
    "ensure_vault_structure",
    "list_existing_notes",
    "note_exists",
    "update_note",
    "get_vault_path",
    "analyze_learning_session",
    "should_create_note",
]
