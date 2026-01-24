"""Note command - manual operations for Obsidian atomic notes.

Provides CLI interface for creating, updating, and listing notes
without requiring the agent.
"""

from __future__ import annotations

import asyncio

from dsa_coach.curriculum import get_pattern_name
from dsa_coach.obsidian.writer import get_vault_path, list_existing_notes
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.tools.obsidian import (
    create_pattern_note as create_tool,
)
from dsa_coach.tools.obsidian import (
    propose_pattern_note as propose_tool,
)
from dsa_coach.ui import UI


def _get_ui() -> UI:
    """Get UI instance."""
    try:
        from rich.console import Console

        return UI(rich_available=True, console=Console())
    except ImportError:
        return UI(rich_available=False, console=None)


def cmd_note(subcommand: str | None = None, *args):
    """Manage Obsidian notes for patterns and problems.

    Usage:
        python coach.py note list              # List all notes
        python coach.py note create <pattern>  # Create pattern note interactively
        python coach.py note update <name>     # Update existing note
    """
    ui = _get_ui()

    # Check vault configuration
    vault = get_vault_path()
    if not vault:
        ui.print_styled("\n❌ Obsidian vault not configured.", "red")
        ui.print_styled("   Add OBSIDIAN_VAULT_PATH to your .env file.", "dim")
        ui.print_styled(
            "   Example: OBSIDIAN_VAULT_PATH=/path/to/Obsidian/DSA-Prep\n", "dim"
        )
        return

    if not subcommand or subcommand == "list":
        _cmd_note_list(ui)
    elif subcommand == "create":
        pattern = args[0] if args else None
        _cmd_note_create(pattern, ui)
    elif subcommand == "update":
        note_name = args[0] if args else None
        _cmd_note_update(note_name, ui)
    elif subcommand == "propose":
        pattern = args[0] if args else None
        _cmd_note_propose(pattern, ui)
    else:
        ui.print_styled(f"\n❌ Unknown subcommand: {subcommand}", "red")
        ui.print_styled("\nUsage:", "cyan")
        ui.print_styled("  python coach.py note list", "white")
        ui.print_styled("  python coach.py note create <pattern>", "white")
        ui.print_styled("  python coach.py note update <name>", "white")
        ui.print_styled("  python coach.py note propose <pattern>", "white")


def _cmd_note_list(ui: UI):
    """List all notes in vault."""
    ui.print_styled("\n📚 Notes in Obsidian Vault\n", "cyan")

    notes = list_existing_notes("all")

    if not notes:
        ui.print_styled("  No notes found. Create your first note with:", "dim")
        ui.print_styled("  python coach.py note create <pattern>\n", "green")
        return

    # Group by type
    patterns = [n for n in notes if n["type"] == "pattern"]
    problems = [n for n in notes if n["type"] == "problem"]

    if patterns:
        ui.print_styled(f"  📋 Patterns ({len(patterns)}):", "yellow")
        for note in patterns:
            ui.print_styled(f"     • {note['name']}", "white")

    if problems:
        ui.print_styled(f"\n  🎯 Problems ({len(problems)}):", "yellow")
        for note in problems:
            ui.print_styled(f"     • {note['name']}", "white")

    ui.print_styled(f"\n  Total: {len(notes)} notes\n", "green")


def _cmd_note_propose(pattern: str | None, ui: UI):
    """Propose note structure for a pattern."""
    if not pattern:
        ui.print_styled("\n❌ Pattern name required.", "red")
        ui.print_styled("   Usage: python coach.py note propose <pattern>\n", "dim")
        return

    # Normalize pattern name
    pattern = pattern.replace("-", "_").lower()

    # Get progress from database
    with SyncDatabase() as db:
        pattern_progress = db.get_pattern_progress("default", pattern)
        current_progress = pattern_progress.progress if pattern_progress else 0

    ui.print_styled(f"\n🔍 Analyzing '{pattern}' for note creation...\n", "cyan")

    # Run proposal tool
    result = asyncio.run(
        propose_tool(
            pattern=pattern,
            progress=current_progress,
            session_insights="Manual note creation via CLI",
        )
    )

    if not result.success:
        ui.print_styled(f"❌ {result.error or result.message}", "red")
        return

    proposal = result.data

    ui.print_styled(f"📝 Proposed Note: {proposal['title']}", "bold cyan")
    ui.print_styled(f"   Filename: {proposal['filename']}", "dim")
    ui.print_styled(f"   Estimated: {proposal['estimated_lines']} lines\n", "dim")

    ui.print_styled("   Sections:", "yellow")
    for section in proposal["sections"]:
        ui.print_styled(f"     • {section}", "white")

    ui.print_styled(f"\n   Tags: {', '.join(proposal['tags'])}", "dim")

    if proposal["needs_diagram"]:
        ui.print_styled("   ✓ Includes mermaid diagram", "green")

    ui.print_styled("\n   Ready to create? Use:", "cyan")
    ui.print_styled(f"   python coach.py note create {pattern}\n", "green")


def _cmd_note_create(pattern: str | None, ui: UI):
    """Create a new pattern note interactively."""
    if not pattern:
        ui.print_styled("\n❌ Pattern name required.", "red")
        ui.print_styled("   Usage: python coach.py note create <pattern>\n", "dim")

        # Show available patterns from database
        with SyncDatabase() as db:
            all_patterns = db.get_all_pattern_progress()
            pattern_ids = [p.pattern_id for p in all_patterns]
        if pattern_ids:
            ui.print_styled("   Available patterns:", "cyan")
            for p in sorted(pattern_ids)[:10]:
                ui.print_styled(f"     • {p}", "dim")
        return

    # Normalize pattern name
    pattern = pattern.replace("-", "_").lower()

    # Get pattern progress from database
    with SyncDatabase() as db:
        pattern_progress = db.get_pattern_progress("default", pattern)

    if not pattern_progress:
        ui.print_styled(f"\n❌ Pattern '{pattern}' not found in your progress.", "red")
        ui.print_styled(
            "   Start learning it first with: python coach.py learn\n", "dim"
        )
        return

    current_progress = pattern_progress.progress

    ui.print_styled(f"\n📝 Creating note for '{get_pattern_name(pattern)}'", "cyan")
    ui.print_styled(f"   Current progress: {current_progress:.0f}%\n", "dim")

    # Interactive input
    ui.print_styled("Answer the following to create your note:\n", "yellow")

    title = input("Title (e.g., 'Sliding Window'): ").strip() or get_pattern_name(
        pattern
    )

    print("\nCore Concept (2-3 paragraphs explaining WHAT this is):")
    description = _read_multiline_input()

    print("\nWhy This Matters for Interviews:")
    why_matters = _read_multiline_input()

    print("\n60-Second Elevator Pitch:")
    sixty_second = _read_multiline_input()

    print("\nCode Example (15-30 lines):")
    code_example = _read_multiline_input()

    print("\nCode Explanation:")
    code_explanation = _read_multiline_input()

    key_terms = input("\nKey Terminology (comma-separated): ").strip()
    follow_ups = input("Expected Follow-up Questions (comma-separated): ").strip()
    pitfalls = input("Common Pitfalls (comma-separated): ").strip()

    companies = input("Companies Using This (optional, comma-separated): ").strip()
    use_cases = input("Real-World Use Cases (optional, comma-separated): ").strip()
    related = input("Related Patterns (optional, comma-separated): ").strip()

    has_diagram = input("\nInclude mermaid diagram? [y/N]: ").strip().lower() == "y"

    # Build trade-offs (simplified for CLI)
    trade_offs = '[{"aspect": "General", "description": "See note content", "when_to_use": "Context-dependent"}]'

    ui.print_styled("\n⏳ Creating note...\n", "yellow")

    # Call create tool
    result = asyncio.run(
        create_tool(
            pattern=pattern,
            title=title,
            description=description,
            why_matters=why_matters,
            trade_offs=trade_offs,
            code_example=code_example,
            code_explanation=code_explanation,
            sixty_second_pitch=sixty_second,
            key_terminology=key_terms,
            follow_up_questions=follow_ups,
            common_pitfalls=pitfalls,
            companies=companies,
            use_cases=use_cases,
            related_patterns=related,
            has_diagram=has_diagram,
        )
    )

    if result.success:
        ui.print_styled(f"✅ {result.message}", "green")
        ui.print_styled(f"   {result.data['filepath']}\n", "dim")
    else:
        ui.print_styled(f"❌ {result.error}", "red")


def _cmd_note_update(note_name: str | None, ui: UI):
    """Update an existing note with new insights."""
    if not note_name:
        ui.print_styled("\n❌ Note name required.", "red")
        ui.print_styled("   Usage: python coach.py note update <note-name>\n", "dim")
        return

    ui.print_styled(f"\n✏️  Updating note: {note_name}\n", "cyan")

    section_title = input("Section Title (e.g., 'New Insight'): ").strip()
    print("\nNew Content:")
    new_content = _read_multiline_input()

    if not new_content:
        ui.print_styled("❌ No content provided.", "red")
        return

    from dsa_coach.tools.obsidian import update_note_with_insights

    result = asyncio.run(
        update_note_with_insights(
            note_name=note_name,
            new_insights=new_content,
            section_title=section_title or "Additional Insights",
        )
    )

    if result.success:
        ui.print_styled(f"✅ {result.message}\n", "green")
    else:
        ui.print_styled(f"❌ {result.error}\n", "red")


def _read_multiline_input() -> str:
    """Read multi-line input until empty line."""
    lines = []
    while True:
        try:
            line = input()
            if not line:
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)
