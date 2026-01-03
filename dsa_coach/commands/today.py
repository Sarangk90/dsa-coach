"""Today command - DEPRECATED."""

from dsa_coach.ui import UI

try:
    from rich.console import Console
    _console = Console()
    _ui = UI(rich_available=True, console=_console)
except ImportError:
    _ui = UI(rich_available=False, console=None)


def cmd_today():
    """Show deprecated message."""
    _ui.print_styled("\n⚠️  Day-wise schedule has been removed.", "yellow")
    _ui.print_styled("Use 'python coach.py status' to see your progress or 'python coach.py next' to get a quest.\n", "cyan")
