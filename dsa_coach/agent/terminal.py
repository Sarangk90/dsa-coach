"""Rich terminal UI for DSA Coach agent.

Provides a beautiful terminal interface with dashboard and chat.
Uses the same advanced input UX from mentor.py for consistency.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

try:
    from rich import box
    from rich.console import Console as RichConsole
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit.styles import Style as PTStyle

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from dsa_coach.curriculum import get_pattern_name

# Terminal width
TERMINAL_WIDTH = int(os.environ.get("COACH_WIDTH", 88))


class TerminalUI:
    """Rich terminal UI for the coaching experience."""

    console: Console | None

    def __init__(self):
        if RICH_AVAILABLE:
            self.console = RichConsole(width=TERMINAL_WIDTH)
        else:
            self.console = None

        self.session = None
        self.session_start_time: datetime | None = None
        if PROMPT_TOOLKIT_AVAILABLE:
            self._setup_prompt_session()

    def start_session_timer(self) -> None:
        """Start the session timer."""
        self.session_start_time = datetime.now()

    def _format_elapsed_time(self) -> str:
        """Format elapsed session time as MM:SS or HH:MM:SS."""
        if not self.session_start_time:
            return ""
        elapsed = datetime.now() - self.session_start_time
        total_seconds = int(elapsed.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _setup_prompt_session(self):
        """Initialize prompt_toolkit session."""
        # Command auto-completion
        completer = WordCompleter(
            ["quit", "exit", "help", "dashboard", "status", "patterns"],
            ignore_case=True,
        )

        # Key bindings
        kb = KeyBindings()

        @kb.add("c-j")  # Ctrl+J for newline
        def _(event):
            """Ctrl+J → insert newline."""
            event.current_buffer.insert_text("\n")

        @kb.add("enter")
        def _(event):
            """Enter → send message."""
            event.current_buffer.validate_and_handle()

        # Capture self for closure
        ui_self = self

        # Dynamic toolbar
        def bottom_toolbar():
            from prompt_toolkit.application import get_app

            try:
                app = get_app()
                text = app.current_buffer.text
                line_count = text.count("\n") + 1 if text else 1
            except Exception:
                line_count = 1

            line_info = f"{line_count} line{'s' if line_count != 1 else ''}"

            # Get elapsed time from session timer
            elapsed = ui_self._format_elapsed_time()
            timer_part = ""
            if elapsed:
                timer_part = f' │ <style fg="#ffcc00">⏱️ {elapsed}</style>'

            return HTML(
                f'<style bg="#333333" fg="#888888">'
                f" <b>Ctrl+J</b> newline │ <b>Enter</b> send │ <b>Ctrl+D</b> exit │ "
                f'<style fg="#aaddff">{line_info}</style>'
                f"{timer_part}"
                f" </style>"
            )

        # Style
        style = PTStyle.from_dict(
            {
                "prompt": "bold fg:ansicyan",
                "bottom-toolbar": "bg:#333333 fg:#888888",
            }
        )

        self.session = PromptSession(
            multiline=True,
            key_bindings=kb,
            completer=completer,
            complete_while_typing=False,
            history=InMemoryHistory(),
            bottom_toolbar=bottom_toolbar,
            style=style,
            enable_history_search=False,
            refresh_interval=0.5,
        )

    def clear(self) -> None:
        """Clear the terminal."""
        if self.console:
            self.console.clear()
        else:
            print("\n" * 50)

    def print_header(self) -> None:
        """Print the DSA Coach header."""
        if self.console:
            header = Text()
            header.append("🎯 ", style="bold")
            header.append("DSA Coach", style="bold cyan")
            header.append(" - Your AI Mentor", style="dim")
            self.console.print(Panel(header, box=box.DOUBLE))
        else:
            print("=" * 50)
            print("🎯 DSA Coach - Your AI Mentor")
            print("=" * 50)

    def render_dashboard(self, state: dict) -> None:
        """Render the dashboard panel."""
        if not self.console or not state:
            return

        profile = state.get("profile", {})
        current_quest = state.get("current_quest")
        weak_patterns = state.get("weak_patterns", [])
        alerts = state.get("alerts", [])

        # Create layout
        table = Table(box=box.ROUNDED, show_header=False, expand=True)
        table.add_column("Section", style="cyan", width=20)
        table.add_column("Content", style="white")

        # Profile section
        quests_completed = profile.get("quests_completed", 0)
        member_since = profile.get("member_since", "N/A")[:10]

        profile_text = Text()
        profile_text.append(
            f"✅ {quests_completed} quests completed", style="bold green"
        )
        profile_text.append(f"\n   Member since: {member_since}", style="dim")

        table.add_row("📊 Progress", profile_text)

        # Current Quest
        if current_quest:
            quest_text = Text()
            quest_text.append(f"{current_quest['title']}\n", style="bold")
            quest_text.append(f"   Pattern: {current_quest['pattern']} • ", style="dim")
            quest_text.append(f"{current_quest['difficulty']}", style="dim cyan")
            table.add_row("🎯 Current", quest_text)
        else:
            table.add_row("🎯 Current", Text("No active quest", style="dim italic"))

        # Weak Patterns
        if weak_patterns:
            patterns_text = Text()
            for i, p in enumerate(weak_patterns[:3]):
                if i > 0:
                    patterns_text.append("  •  ")
                conf = p.get("confidence", 0)
                color = "red" if conf < 30 else "yellow" if conf < 60 else "green"
                patterns_text.append(
                    f"{get_pattern_name(p['pattern_id'])}", style=f"bold {color}"
                )
                patterns_text.append(f" ({conf}%)", style="dim")
            table.add_row("💪 Focus", patterns_text)

        # Alerts
        if alerts:
            alert_text = Text()
            for alert in alerts[:2]:
                icon = "📋" if alert["type"] == "review" else "⚠️"
                alert_text.append(f"{icon} {alert['message']}\n", style="bold")
            table.add_row("⚠️ Alerts", alert_text)

        self.console.print(
            Panel(
                table,
                title="[bold cyan]Dashboard[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )

    def render_message(self, role: str, content: str) -> None:
        """Render a chat message."""
        if self.console:
            if role == "user":
                self.console.print(
                    Panel(
                        content,
                        title="[bold blue]You[/bold blue]",
                        border_style="blue",
                        box=box.ROUNDED,
                    )
                )
            else:
                # Try to render as markdown
                try:
                    md = Markdown(content)
                    self.console.print(
                        Panel(
                            md,
                            title="[bold green]🤖 Coach[/bold green]",
                            border_style="green",
                            box=box.ROUNDED,
                        )
                    )
                except Exception:
                    self.console.print(
                        Panel(
                            content,
                            title="[bold green]🤖 Coach[/bold green]",
                            border_style="green",
                            box=box.ROUNDED,
                        )
                    )
        else:
            prefix = "You: " if role == "user" else "Coach: "
            print(f"\n{prefix}{content}\n")

    def render_tool_activity(self, tool_name: str) -> None:
        """Show that a tool is being executed."""
        if self.console:
            self.console.print(
                f"  [dim]⚙️ {tool_name.replace('_', ' ').title()}...[/dim]"
            )
        else:
            print(f"  [Running: {tool_name}...]")

    def render_error(self, message: str) -> None:
        """Render an error message."""
        if self.console:
            self.console.print(
                Panel(
                    f"[bold red]❌ {message}[/bold red]",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
        else:
            print(f"\n❌ Error: {message}\n")

    def render_tool_error(self, tool_name: str, error: str) -> None:
        """Render a tool error prominently (more visible than regular errors)."""
        if self.console:
            self.console.print(
                Panel(
                    f"[bold red]⚠️ {tool_name} failed:[/bold red]\n{error}",
                    title="[bold red]Tool Error[/bold red]",
                    border_style="red",
                    box=box.HEAVY,  # More prominent border
                )
            )
        else:
            print(f"\n⚠️ TOOL ERROR [{tool_name}]: {error}\n")

    def render_success(self, message: str) -> None:
        """Render a success message."""
        if self.console:
            self.console.print(f"[bold green]✅ {message}[/bold green]")
        else:
            print(f"✅ {message}")

    def render_info(self, message: str) -> None:
        """Render an info message."""
        if self.console:
            self.console.print(f"[dim]{message}[/dim]")
        else:
            print(message)

    async def get_input(self, prompt: str = "You › ") -> str | None:
        """Get input from the user (Async).

        Uses prompt_toolkit for multiline support if available.

        Returns:
            str: User input (stripped)
            None: If cancelled (Ctrl+C)
        Raises:
            EOFError: If user wants to exit (Ctrl+D)
        """
        if self.console:
            self.console.print()

        # Async prompt_toolkit
        if self.session:
            try:
                # Use patch_stdout to handle background prints if any
                with patch_stdout():
                    text = await self.session.prompt_async([("class:prompt", prompt)])
                    return text.strip() if text else ""
            except KeyboardInterrupt:
                return None
            except EOFError:
                raise

        # Fallback: simple double-Enter mode (blocking, but okay for simple fallback)
        print(prompt, end="", flush=True)
        lines: list[str] = []
        try:
            while True:
                # Use executor to avoid blocking loop strictly speaking,
                # but for fallback input it's acceptable to block.
                # Ideally we'd use run_in_executor but input() is tricky.
                # Given this is a fallback, we'll keep it simple/blocking.
                line = input("" if lines else "")
                if line == "" and len(lines) > 0:
                    break
                lines.append(line)
        except KeyboardInterrupt:
            return None

        return "\n".join(lines).strip()

    def render_welcome(self, greeting: str) -> None:
        """Render the welcome message."""
        if self.console:
            self.console.print()
            self.console.print(
                Panel(
                    greeting,
                    title="[bold green]🤖 Coach[/bold green]",
                    border_style="green",
                    box=box.DOUBLE,
                )
            )
        else:
            print(f"\n{greeting}\n")

    def render_goodbye(self) -> None:
        """Render goodbye message."""
        if self.console:
            self.console.print(
                Panel(
                    "[bold]Keep grinding! See you next time. 💪[/bold]",
                    border_style="cyan",
                    box=box.DOUBLE,
                )
            )
        else:
            print("\nKeep grinding! See you next time. 💪\n")

    def render_help(self) -> None:
        """Render help information."""
        help_text = """
**Commands:**
- Type naturally to chat with your coach
- `quit` or `exit` - End the session
- `help` - Show this help
- `status` - Show your progress
- `patterns` - List all patterns
- `dashboard` - Refresh dashboard

**Quick Actions:**
- "I want to learn [pattern]"
- "Give me a problem"
- "I need a hint"
- "Review my code"
- "What should I work on?"
"""
        if self.console:
            self.console.print(
                Panel(
                    Markdown(help_text),
                    title="[bold cyan]Help[/bold cyan]",
                    border_style="cyan",
                )
            )
        else:
            print(help_text)

    def render_thinking(self) -> None:
        """Show thinking indicator."""
        if self.console:
            self.console.print("[dim]🤔 Thinking...[/dim]")
        else:
            print("Thinking...")

    def render_reasoning(self, content: str) -> None:
        """Show AI reasoning text as it thinks (Claude Code style)."""
        if not content or not content.strip():
            return
        if self.console:
            self.console.print(f"[dim italic]{content}[/dim italic]")
        else:
            print(f"  {content}")
