#!/usr/bin/env python3
"""
DSA Coach - An Adaptive CLI for Interview Preparation
=====================================================

Your personal Principal Engineer mentor that adapts to your skill level,
tracks your progress, and guides you to mastery.

Usage:
    python coach.py             - Start interactive AI coach (default)
    python coach.py --legacy    - Use legacy command mode

Agent Mode (default):
    Launches an interactive AI coaching session where you can chat
    naturally with your coach. The coach uses tools to manage your
    progress, assign quests, provide hints, and more.

Legacy Commands (use --legacy flag):
    python coach.py --legacy start       - Initialize your profile
    python coach.py --legacy status      - Show your progress
    python coach.py --legacy next        - Get your next quest
    python coach.py --legacy done        - Mark current quest complete
    python coach.py --legacy hint        - Get an adaptive hint
    python coach.py --legacy review      - Request code review
    python coach.py --legacy recall      - Spaced repetition quiz
    python coach.py --legacy learn       - Interactive learning session
    python coach.py --legacy design      - Start system design session
    python coach.py --legacy mistakes    - Review your mistake log
"""

import sys
from collections.abc import Callable

# Note: All modular implementations are now in dsa_coach package
# This file only handles CLI routing and legacy command mode

# =============================================================================
# CLI COMMANDS
# =============================================================================


def cmd_start():
    """Initialize profile and workspace."""
    from dsa_coach.commands.start import cmd_start as _cmd_start

    _cmd_start()


def cmd_status():
    """Show current progress and stats."""
    from dsa_coach.commands.status import cmd_status as _cmd_status

    _cmd_status()


def cmd_next():
    """Get the next optimal quest."""
    from dsa_coach.commands.next_quest import cmd_next as _cmd_next

    _cmd_next()


def cmd_done(success: bool = True, time_mins: int | None = None):
    """Mark current quest as complete."""
    from dsa_coach.commands.done import cmd_done as _cmd_done

    _cmd_done(success, time_mins)


def cmd_hint():
    """Get an adaptive hint for the current quest."""
    from dsa_coach.commands.hint import cmd_hint as _cmd_hint

    _cmd_hint()


def cmd_review():
    """Request AI code review for current solution."""
    from dsa_coach.commands.review import cmd_review as _cmd_review

    _cmd_review()


def cmd_recall():
    """Spaced repetition quiz on due items."""
    from dsa_coach.commands.recall import cmd_recall as _cmd_recall

    _cmd_recall()


def cmd_design(topic: str | None = None):
    """Start an interactive system design session."""
    from dsa_coach.commands.design import cmd_design as _cmd_design

    _cmd_design(topic)


def cmd_learn(pattern: str | None = None):
    """Start an interactive learning session on a pattern."""
    from dsa_coach.commands.learn import cmd_learn as _cmd_learn

    _cmd_learn(pattern)


def cmd_mistakes():
    """Review mistake log."""
    from dsa_coach.commands.mistakes import cmd_mistakes as _cmd_mistakes

    _cmd_mistakes()


def cmd_today():
    """Show today's focus and recommendations."""
    from dsa_coach.commands.today import cmd_today as _cmd_today

    _cmd_today()


def cmd_summary():
    """Full progress dump for debugging and overview."""
    from dsa_coach.commands.summary import cmd_summary as _cmd_summary

    _cmd_summary()


def cmd_sessions():
    """List and manage saved conversation sessions."""
    from dsa_coach.commands.sessions import cmd_sessions as _cmd_sessions

    _cmd_sessions()


def cmd_reset(argv: list[str] | None = None):
    """Reset pattern progress (confidence/attempts/successes)."""
    from dsa_coach.commands.reset import cmd_reset as _cmd_reset

    _cmd_reset(argv or [])


def cmd_note(argv: list[str] | None = None):
    """Manage Obsidian notes for patterns and problems."""
    from dsa_coach.commands.note import cmd_note as _cmd_note

    args = argv or []
    subcommand = args[0] if args else None
    remaining = args[1:] if len(args) > 1 else []
    _cmd_note(subcommand, *remaining)


# =============================================================================
# MAIN
# =============================================================================


def run_legacy_command(argv: list[str]):
    """Run a legacy CLI command."""
    if len(argv) < 1:
        print("Legacy mode requires a command. Use --help for usage.")
        return

    command = argv[0].lower()

    commands: dict[str, Callable[[], None]] = {
        "start": cmd_start,
        "status": cmd_status,
        "next": cmd_next,
        "done": cmd_done,
        "hint": cmd_hint,
        "review": cmd_review,
        "recall": cmd_recall,
        "design": lambda: cmd_design(argv[1] if len(argv) > 1 else None),
        "learn": lambda: cmd_learn(argv[1] if len(argv) > 1 else None),
        "mistakes": cmd_mistakes,
        "today": cmd_today,
        "summary": cmd_summary,
        "sessions": cmd_sessions,
        "reset": lambda: cmd_reset(argv[1:]),
        "note": lambda: cmd_note(argv[1:]),
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


def run_agent_mode():
    """Run the interactive AI coach agent."""
    try:
        from dsa_coach.agent.loop import main as agent_main

        agent_main()
    except ImportError as e:
        print(f"Error: Could not start agent mode: {e}")
        print("Try running: pip install pydantic-ai aiosqlite")
        print("\nFalling back to legacy mode. Use --legacy <command>")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting agent: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        return

    # Check for legacy mode
    if len(sys.argv) > 1 and sys.argv[1] == "--legacy":
        run_legacy_command(sys.argv[2:])
        return

    # Check for direct commands (backward compatibility for a transition period)
    # If the first arg is a known command, run legacy mode
    legacy_commands = {
        "start",
        "status",
        "next",
        "done",
        "hint",
        "review",
        "recall",
        "design",
        "learn",
        "mistakes",
        "today",
        "summary",
        "sessions",
        "reset",
        "note",
    }

    if len(sys.argv) > 1 and sys.argv[1].lower() in legacy_commands:
        # Run legacy command directly
        run_legacy_command(sys.argv[1:])
        return

    # Default: run agent mode
    run_agent_mode()


if __name__ == "__main__":
    main()
