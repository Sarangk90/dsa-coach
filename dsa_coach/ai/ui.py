"""UI utilities for AI mentorship output."""

from __future__ import annotations

import os
import shutil
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console as ConsoleType

# Reading width for comfortable text display (80-90 is optimal)
# Can be overridden via COACH_WIDTH environment variable
READING_WIDTH = int(os.getenv("COACH_WIDTH", "88"))

console: ConsoleType | None

try:
    from rich.align import Align
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel

    RICH_AVAILABLE = True

    # Create console with constrained width for readable output
    console = Console(width=READING_WIDTH)

    def get_left_padding() -> int:
        """Calculate padding needed to center content."""
        term_width = shutil.get_terminal_size().columns
        return max(0, (term_width - READING_WIDTH) // 2)

except ImportError:
    RICH_AVAILABLE = False
    console = None

    def get_left_padding() -> int:
        """Fallback padding calculation."""
        return 0


def print_ai_response(text: str, role: str = "Mentor") -> None:
    """Print AI response with nice formatting.

    Args:
        text: Response text to display
        role: Role label (default: "Mentor")
    """
    chat_style = (os.getenv("COACH_CHAT_STYLE") or "discord").strip().lower()

    if RICH_AVAILABLE and chat_style == "discord":
        # Discord-like bubbles: left for Mentor, right for You.
        is_user = role.strip().lower() in {"you", "user"}
        title = "🧑 You" if is_user else "🎓 Mentor"
        border_style = "magenta" if is_user else "cyan"
        body = Markdown(text)

        panel = Panel(
            body,
            title=title,
            border_style=border_style,
            padding=(1, 2),
            expand=False,
        )
        console.print()
        console.print(Align(panel, align="right" if is_user else "left"))
        console.print()
    elif RICH_AVAILABLE:
        icon = "🧑" if role.strip().lower() in {"you", "user"} else "🎓"
        color = "magenta" if role.strip().lower() in {"you", "user"} else "cyan"
        console.print()
        console.print(f"[bold {color}]{icon} {role}:[/bold {color}]")
        console.print()

        md = Markdown(text)
        console.print(md)
        console.print()
    else:
        # Fallback: simple word wrapping for non-rich terminals
        import textwrap

        wrapped = textwrap.fill(text, width=READING_WIDTH)
        icon = "🧑" if role.strip().lower() in {"you", "user"} else "🎓"
        print(f"\n{icon} {role}:\n{wrapped}\n")


def get_user_prompt(label: str = "You") -> str:
    """Return an input prompt that is easy to distinguish in terminal history.

    Uses ANSI styling when appropriate, with a plain-text fallback (e.g., NO_COLOR,
    non-interactive stdout).
    """
    chat_style = (os.getenv("COACH_CHAT_STYLE") or "discord").strip().lower()

    # In discord mode we keep the prompt compact (bubbles provide the structure).
    if chat_style == "discord":
        base = f"{label} > "
        if not sys.stdout.isatty() or os.getenv("NO_COLOR") is not None:
            return "\n" + base
        return f"\n\033[1;35m🧑 {label}\033[0m \033[2m›\033[0m "

    base = f"{label} > "
    if not sys.stdout.isatty():
        return "\n" + base
    if os.getenv("NO_COLOR") is not None:
        return "\n" + base

    # Funky but readable: dim divider + bold label + subtle arrow.
    # Keep it deterministic and widely-supported by terminals.
    term_width = shutil.get_terminal_size().columns
    width = min(READING_WIDTH, term_width)
    divider = "─" * max(10, width)

    # Dim divider, bold magenta label, dim chevrons.
    return f"\n\033[2m{divider}\033[0m\n\033[1;35m🧑 {label}\033[0m \033[2m››\033[0m "


def clear_last_input_line() -> None:
    """Clear the previous terminal line (best-effort) to avoid duplicate echoes.

    In interactive TTY mode, `input()` leaves the typed line in history. When we
    re-render the same content as a Rich "chat bubble", it looks duplicated.
    This helper clears the just-entered line before printing the bubble.
    """
    if not sys.stdout.isatty():
        return

    # Move cursor up one line, clear it, return to start of line.
    # This is widely supported by ANSI terminals.
    sys.stdout.write("\033[1A\033[2K\r")
    sys.stdout.flush()
