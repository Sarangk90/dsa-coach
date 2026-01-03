from __future__ import annotations

import sys

from dsa_coach.storage.sync import SyncDatabase


def _normalize_pattern(pattern: str) -> str:
    return pattern.replace("-", "_").replace(" ", "_").lower()


def _reset_pattern_progress(db: SyncDatabase, pattern_id: str) -> None:
    """Reset a single pattern's progress."""
    progress = db.get_pattern_progress("default", pattern_id)
    if progress:
        progress.confidence = 0
        progress.quests_completed = 0
        progress.concepts_understood = []
        progress.mastered = False
        progress.last_practiced = None
        progress.next_review = None
        db.upsert_pattern_progress(progress)


def _confirm_or_abort(action: str, yes: bool) -> bool:
    """Return True if the destructive action should proceed."""
    if yes:
        return True

    if not sys.stdin.isatty():
        print("Refusing to modify progress in non-interactive mode without --yes.")
        return False

    resp = input(f"{action} Continue? [y/N] ").strip().lower()
    return resp in ("y", "yes")


def cmd_reset(argv: list[str] | None = None) -> None:
    """Reset pattern progress (confidence/attempts/successes) safely.

    Usage:
      python coach.py reset pattern <pattern> [--yes]
      python coach.py reset patterns [--yes]
    """
    args = list(argv or [])
    yes = False
    if "--yes" in args or "-y" in args:
        yes = True
        args = [a for a in args if a not in ("--yes", "-y")]

    if not args or args[0] in ("-h", "--help", "help"):
        print(
            "Usage:\n"
            "  python coach.py reset pattern <pattern> [--yes]\n"
            "  python coach.py reset patterns [--yes]\n"
        )
        return

    with SyncDatabase() as db:
        all_patterns = db.get_all_pattern_progress()
        pattern_ids = {p.pattern_id for p in all_patterns}

        if args[0] == "patterns":
            if not _confirm_or_abort("This will reset ALL pattern progress to 0.", yes=yes):
                return
            for pattern in all_patterns:
                _reset_pattern_progress(db, pattern.pattern_id)
            print("✅ Reset all pattern progress.")
            return

        if args[0] == "pattern":
            if len(args) < 2:
                print("Missing pattern name. Example: python coach.py reset pattern sliding_window")
                return
            pattern = _normalize_pattern(args[1])
            if pattern not in pattern_ids:
                print(f"Pattern not found: {pattern}")
                print(f"Available patterns: {', '.join(sorted(pattern_ids))}")
                return
            if not _confirm_or_abort(f"This will reset progress for '{pattern}'.", yes=yes):
                return
            _reset_pattern_progress(db, pattern)
            print(f"✅ Reset pattern progress: {pattern}")
            return

        # Convenience: allow `python coach.py reset <pattern> [--yes]`
        pattern = _normalize_pattern(args[0])
        if pattern in pattern_ids:
            if not _confirm_or_abort(f"This will reset progress for '{pattern}'.", yes=yes):
                return
            _reset_pattern_progress(db, pattern)
            print(f"✅ Reset pattern progress: {pattern}")
            return

    print("Unknown reset target. Use one of:")
    print("  python coach.py reset pattern <pattern> [--yes]")
    print("  python coach.py reset patterns [--yes]")




