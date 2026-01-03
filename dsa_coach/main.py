"""Main CLI entrypoint for DSA Coach."""

from __future__ import annotations

import sys
from collections.abc import Callable

# Import all command handlers
from dsa_coach.commands import (
    design,
    done,
    hint,
    learn,
    mistakes,
    next_quest,
    recall,
    reset,
    review,
    sessions,
    start,
    status,
    summary,
    today,
)

CLI_HELP = """
DSA Coach - An Adaptive CLI for Interview Preparation
=====================================================

Your personal Principal Engineer mentor that adapts to your skill level,
tracks your progress, and guides you to mastery.

Commands:
    python coach.py start       - Initialize your profile
    python coach.py status      - Show your progress
    python coach.py next        - Get your next quest
    python coach.py done        - Mark current quest complete
    python coach.py hint        - Get an adaptive hint
    python coach.py review      - Request code review
    python coach.py recall      - Spaced repetition quiz
    python coach.py learn       - Interactive learning session (teach + practice)
    python coach.py design      - Start system design session
    python coach.py mistakes    - Review your mistake log
    python coach.py reset       - Reset pattern progress (safe)
"""


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(CLI_HELP)
        return

    command = sys.argv[1].lower()

    commands: dict[str, Callable[[], None]] = {
        "start": start.cmd_start,
        "status": status.cmd_status,
        "next": next_quest.cmd_next,
        "done": done.cmd_done,
        "hint": hint.cmd_hint,
        "review": review.cmd_review,
        "recall": recall.cmd_recall,
        "design": lambda: design.cmd_design(sys.argv[2] if len(sys.argv) > 2 else None),
        "learn": lambda: learn.cmd_learn(sys.argv[2] if len(sys.argv) > 2 else None),
        "mistakes": mistakes.cmd_mistakes,
        "today": today.cmd_today,
        "summary": summary.cmd_summary,
        "sessions": sessions.cmd_sessions,
        "reset": lambda: reset.cmd_reset(sys.argv[2:]),
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(CLI_HELP)


if __name__ == "__main__":
    main()
