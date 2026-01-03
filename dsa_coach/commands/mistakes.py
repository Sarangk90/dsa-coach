"""Mistakes command - review mistake log."""

from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI

try:
    from rich.console import Console

    _console = Console()
    _ui = UI(rich_available=True, console=_console)
except ImportError:
    _ui = UI(rich_available=False, console=None)


def cmd_mistakes():
    """Review mistake log."""
    with SyncDatabase() as db:
        mistakes = db.get_recent_mistakes("default", limit=10)
        recurring = db.get_recurring_mistake_types("default")

    if not mistakes:
        _ui.print_styled("No mistakes logged yet. Keep coding!", "green")
        return

    _ui.print_styled("\n📝 Mistake Journal\n", "cyan")

    # Show recent mistakes
    _ui.print_styled("Recent Mistakes:", "yellow")
    for i, m in enumerate(mistakes, 1):
        pattern = m.get("pattern_id", "N/A").replace("_", " ").title()
        quest = m.get("quest_id", "Unknown")
        mistake_type = m.get("mistake_type", "N/A").replace("_", " ").title()
        description = m.get("description", "N/A")
        lesson = m.get("lesson_learned", "")

        _ui.print_styled(f"{i}. [{pattern}] {quest}", "yellow")
        _ui.print_styled(f"   Type: {mistake_type}", "dim")
        _ui.print_styled(f"   What happened: {description}", "dim")
        if lesson:
            _ui.print_styled(f"   Lesson learned: {lesson}", "green")

    # Show recurring patterns
    if recurring:
        _ui.print_styled("\n⚠️  Recurring Mistake Patterns:", "red")
        for r in recurring:
            # DB query returns "type" not "mistake_type"
            mtype = (
                r.get("type", r.get("mistake_type", "unknown"))
                .replace("_", " ")
                .title()
            )
            count = r.get("count", 0)
            patterns = r.get("patterns", [])
            pattern_str = ", ".join(p.replace("_", " ").title() for p in patterns[:3])
            _ui.print_styled(f"   • {mtype} (x{count}) - seen in: {pattern_str}", "red")
