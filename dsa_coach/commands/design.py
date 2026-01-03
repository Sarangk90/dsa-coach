"""Design command - start an interactive system design session."""

from dsa_coach.ui import UI

try:
    from rich.console import Console
    _console = Console()
    _ui = UI(rich_available=True, console=_console)
except ImportError:
    _ui = UI(rich_available=False, console=None)


def cmd_design(topic: str = None):
    """Start an interactive system design session."""
    _ui.print_styled("\n⚠️  System Design quests are currently disabled/under restructuring.", "yellow")
    _ui.print_styled("Focus on DSA quests for now.\n", "cyan")
