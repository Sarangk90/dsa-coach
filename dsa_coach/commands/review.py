"""Review command - request AI code review for current solution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dsa_coach.paths import SOLUTIONS_DIR
from dsa_coach.quests import get_all_quests
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI

if TYPE_CHECKING:
    from rich.console import Console

_console: Console | None

try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel

    _console = RichConsole()
    _ui = UI(rich_available=True, console=_console)
except ImportError:
    _console = None
    _ui = UI(rich_available=False, console=None)


def cmd_review():
    """Request AI code review for current solution."""
    with SyncDatabase() as db:
        session = db.get_latest_session()
        current_id = session.current_quest if session else None
        progress_compat = db.build_progress_compat()
    if not current_id:
        _ui.print_styled("No active quest. Complete a quest first.", "yellow")
        _ui.print_styled("Run 'python coach.py next' to get a quest.", "dim")
        return

    # Find the solution file
    try:
        all_quests = get_all_quests()
    except Exception as e:
        _ui.print_styled(f"Error loading quest data: {e}", "red")
        return

    quest = next((q for q in all_quests if q["id"] == current_id), None)

    if not quest:
        _ui.print_styled(f"Quest '{current_id}' not found in quest database.", "red")
        return

    day = quest.get("day", 1)
    solution_file = SOLUTIONS_DIR / f"day{day}" / f"{current_id}.py"

    if not solution_file.exists():
        _ui.print_styled(f"Solution file not found: {solution_file}", "red")
        _ui.print_styled("Make sure you've created the solution file first.", "dim")
        return

    # Read solution with error handling
    try:
        with solution_file.open(encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        _ui.print_styled(f"Error reading solution file: {e}", "red")
        return

    if not code.strip():
        _ui.print_styled("Solution file is empty. Add your code first.", "yellow")
        return

    # Try to use LLM for review
    try:
        from dsa_coach.ai import review_code

        feedback = review_code(quest, code, progress_compat)

        if _ui.rich_available and _console:
            _console.print(Panel(feedback, title="🔍 Code Review", border_style="cyan"))
        else:
            print(f"\n{'=' * 50}")
            print(" 🔍 Code Review")
            print(f"{'=' * 50}")
            print(feedback)
            print(f"{'=' * 50}\n")
    except ImportError:
        _ui.print_styled("AI features not available. Install dependencies:", "yellow")
        _ui.print_styled("pip install anthropic openai python-dotenv", "dim")
        _ui.print_styled("\nFor now, self-review using the DIVE protocol:", "dim")
        _ui.print_styled("- Does your solution handle edge cases?", "dim")
        _ui.print_styled("- Is the time/space complexity optimal?", "dim")
        _ui.print_styled("- Are variable names descriptive?", "dim")
    except Exception as e:
        _ui.print_styled(f"Error during code review: {e}", "red")
        _ui.print_styled("Please check your API key configuration in .env", "dim")
