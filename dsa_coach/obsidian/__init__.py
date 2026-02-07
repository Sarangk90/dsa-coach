"""Obsidian integration for atomic note creation.

This module handles creation of interview-focused atomic notes
following the user's Obsidian workflow with proper structure,
cross-linking, and quality enforcement.
"""

from .analyzer import should_create_note
from .note_generator import (
    generate_pattern_note,
    generate_problem_note,
    get_filename_for_pattern,
    get_filename_for_problem,
)
from .writer import (
    get_vault_path,
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
    "note_exists",
    "update_note",
    "get_vault_path",
    "should_create_note",
]
