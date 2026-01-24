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

    from ..ai.client import TokenUsage

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


def format_time_ago(dt: datetime) -> str:
    """Format datetime as human-readable relative time.

    Returns: "just now", "2 mins ago", "3 hours ago", "yesterday", "5 days ago", "Jan 10"
    """
    delta = datetime.now() - dt
    total_seconds = delta.total_seconds()

    if total_seconds < 60:
        return "just now"
    if total_seconds < 3600:
        mins = int(total_seconds // 60)
        return f"{mins} min{'s' if mins != 1 else ''} ago"
    if total_seconds < 86400:
        hours = int(total_seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if delta.days == 1:
        return "yesterday"
    if delta.days < 7:
        return f"{delta.days} days ago"
    return dt.strftime("%b %d")


def truncate_preview(text: str, max_len: int = 60) -> str:
    """Truncate text for preview with ellipsis."""
    if not text:
        return ""
    # Replace newlines with spaces for single-line preview
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


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
        self._current_token_usage: TokenUsage | None = None
        if PROMPT_TOOLKIT_AVAILABLE:
            self._setup_prompt_session()

    def start_session_timer(self) -> None:
        """Start the session timer."""
        self.session_start_time = datetime.now()

    def update_token_usage(self, token_usage: TokenUsage | None) -> None:
        """Update the token usage state for display in toolbar.

        Args:
            token_usage: Current token usage from agent, or None
        """
        self._current_token_usage = token_usage

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
            ["quit", "exit", "help", "dashboard", "status", "patterns", "/resume"],
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

            # Get token usage display
            token_part = ""
            if ui_self._current_token_usage:
                usage = ui_self._current_token_usage
                token_display = usage.format_display()

                # Color based on warning threshold (75%+)
                if usage.is_warning_threshold:
                    color = "#ff4444"  # Red for warning
                    icon = "⚠️"
                else:
                    color = "#aaddff"  # Cyan for normal
                    icon = "📊"

                token_part = f' │ <style fg="{color}">{icon} {token_display}</style>'

            return HTML(
                f'<style bg="#333333" fg="#888888">'
                f" <b>Ctrl+J</b> newline │ <b>Enter</b> send │ <b>Ctrl+D</b> exit │ "
                f'<style fg="#aaddff">{line_info}</style>'
                f"{timer_part}"
                f"{token_part}"
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
        """Print the DSA Coach header (copy-friendly)."""
        if self.console:
            from rich.rule import Rule

            self.console.print()
            self.console.print(
                Rule("[bold cyan]🎯 DSA Coach[/bold cyan] [dim]- Your AI Mentor[/dim]")
            )
            self.console.print()
        else:
            print("\n─── 🎯 DSA Coach - Your AI Mentor ───\n")

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
            quest_text.append(
                f"{current_quest.get('title', 'Unknown')}\n", style="bold"
            )
            pattern_display = current_quest.get("pattern_name") or current_quest.get(
                "pattern_id", "Unknown"
            )
            quest_text.append(f"   Pattern: {pattern_display} • ", style="dim")
            quest_text.append(
                f"{current_quest.get('difficulty', 'medium')}", style="dim cyan"
            )
            table.add_row("🎯 Current", quest_text)
        else:
            table.add_row("🎯 Current", Text("No active quest", style="dim italic"))

        # Weak Patterns
        if weak_patterns:
            patterns_text = Text()
            for i, p in enumerate(weak_patterns[:3]):
                if i > 0:
                    patterns_text.append("  •  ")
                prog = p.get("progress", 0)
                color = "red" if prog < 30 else "yellow" if prog < 60 else "green"
                patterns_text.append(
                    f"{get_pattern_name(p['pattern_id'])}", style=f"bold {color}"
                )
                patterns_text.append(f" ({prog}%)", style="dim")
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
        """Render a chat message (Claude Code style - copy-friendly)."""
        if self.console:
            if role == "user":
                # User message: bold yellow text (no special chars, copies clean)
                self.console.print(f"[bold yellow]{content}[/bold yellow]")
            else:
                # Coach message: bullet prefix + markdown content
                self.console.print()
                try:
                    md = Markdown(content)
                    self.console.print("[white]●[/white] ", end="")
                    self.console.print(md)
                except Exception:
                    self.console.print(f"[white]●[/white] {content}")
                self.console.print()
        else:
            prefix = "" if role == "user" else "● "
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
        """Render an error message (copy-friendly, no border)."""
        if self.console:
            self.console.print(f"[bold red]✗[/bold red] {message}")
        else:
            print(f"✗ {message}")

    def render_tool_error(self, tool_name: str, error: str) -> None:
        """Render a tool error (copy-friendly, no border)."""
        if self.console:
            self.console.print(f"[bold red]✗ {tool_name} failed:[/bold red] {error}")
        else:
            print(f"✗ {tool_name} failed: {error}")

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

    async def get_input(self, prompt: str = "> ") -> str | None:
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
        """Render the welcome message (copy-friendly, no border)."""
        if self.console:
            self.console.print()
            self.console.print(f"[white]●[/white] {greeting}")
            self.console.print()
        else:
            print(f"\n● {greeting}\n")

    def render_goodbye(self) -> None:
        """Render goodbye message (copy-friendly, no border)."""
        if self.console:
            self.console.print()
            self.console.print(
                "[bold cyan]●[/bold cyan] Keep grinding! See you next time. 💪"
            )
            self.console.print()
        else:
            print("\n● Keep grinding! See you next time. 💪\n")

    def render_help(self) -> None:
        """Render help information (copy-friendly, no border)."""
        help_text = """
**Commands:**
- `/resume` - Resume a previous conversation
- `dashboard` - Refresh dashboard
- `quit` or `exit` - End the session
- `help` - Show this help

**Quick Actions:**
- "I want to learn [pattern]"
- "Give me a problem"
- "I need a hint"
- "Review my code"
- "What should I work on?"
"""
        if self.console:
            self.console.print()
            self.console.print("[bold cyan]●[/bold cyan] Help")
            self.console.print()
            self.console.print(Markdown(help_text))
            self.console.print()
        else:
            print(help_text)

    def render_thinking(self) -> None:
        """Show thinking indicator (Claude Code style)."""
        if self.console:
            self.console.print("[dim italic]∴ Thinking...[/dim italic]")
        else:
            print("∴ Thinking...")

    def render_reasoning(self, content: str) -> None:
        """Show AI reasoning text as it thinks (Claude Code style)."""
        if not content or not content.strip():
            return
        if self.console:
            self.console.print(f"[dim italic]{content}[/dim italic]")
        else:
            print(f"  {content}")

    def render_session_picker(self, sessions: list[dict]) -> None:
        """Render a numbered list of resumable sessions."""
        if self.console:
            content = Text()
            for i, s in enumerate(sessions, 1):
                # Time ago
                updated_at = datetime.fromisoformat(s["updated_at"])
                time_ago = format_time_ago(updated_at)

                # Preview (truncated first message)
                preview = truncate_preview(s.get("first_message", ""), 50)

                # Pattern/quest context
                context_parts = []
                if s.get("current_pattern"):
                    pattern_name = get_pattern_name(s["current_pattern"])
                    context_parts.append(f"Pattern: {pattern_name}")
                if s.get("current_quest"):
                    context_parts.append(f"Quest: {s['current_quest']}")
                if not context_parts:
                    context_parts.append("General")
                context_parts.append(f"{s['message_count']} messages")
                context = " • ".join(context_parts)

                # Format entry
                content.append(f"  {i}. ", style="bold cyan")
                content.append(f"[{time_ago}] ", style="dim")
                content.append(f'"{preview}"\n', style="white")
                content.append(f"     {context}\n\n", style="dim")

            self.console.print(
                Panel(
                    content,
                    title="[bold cyan]📋 Recent Sessions[/bold cyan]",
                    border_style="cyan",
                    box=box.ROUNDED,
                )
            )
        else:
            # Fallback plain text
            print("\n📋 Recent Sessions:\n")
            for i, s in enumerate(sessions, 1):
                updated_at = datetime.fromisoformat(s["updated_at"])
                time_ago = format_time_ago(updated_at)
                preview = truncate_preview(s.get("first_message", ""), 50)
                print(f'  {i}. [{time_ago}] "{preview}"')
                print(f"     {s['message_count']} messages\n")

    async def get_session_selection(self, max_index: int) -> int | None:
        """Get user's session selection.

        Args:
            max_index: Maximum valid selection (1-based)

        Returns:
            0-based index of selection, or None if cancelled
        """
        prompt = f"Select session (1-{max_index}) or 'c' to cancel: "

        if self.console:
            self.console.print(f"[dim]{prompt}[/dim]", end="")
        else:
            print(prompt, end="")

        # Use simple input (not multiline prompt)
        try:
            response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            return None

        if not response or response == "c":
            return None

        try:
            selection = int(response)
            if 1 <= selection <= max_index:
                return selection - 1  # Convert to 0-based
            if self.console:
                self.console.print("[red]Invalid selection.[/red]")
            else:
                print("Invalid selection.")
            return None
        except ValueError:
            if self.console:
                self.console.print("[red]Invalid input.[/red]")
            else:
                print("Invalid input.")
            return None

    def render_conversation_history(self, messages: list[dict]) -> None:
        """Render FULL conversation history after resume (copy-friendly)."""
        if not messages:
            return

        if self.console:
            from rich.rule import Rule

            self.console.print()
            self.console.print(Rule("[dim]Resumed Conversation[/dim]", style="dim"))
            self.console.print()
            for msg in messages:
                role = msg["role"]
                text = msg["content"]

                if role == "user":
                    self.console.print(f"[bold yellow]▌[/bold yellow] {text}")
                else:
                    # Use Markdown rendering for assistant messages (same as render_message)
                    try:
                        md = Markdown(text)
                        self.console.print("[white]●[/white] ", end="")
                        self.console.print(md)
                    except Exception:
                        self.console.print(f"[white]●[/white] {text}")
                self.console.print()
            self.console.print(Rule(style="dim"))
            self.console.print()
        else:
            print("\n─── Resumed Conversation ───\n")
            for msg in messages:
                prefix = "▌" if msg["role"] == "user" else "●"
                print(f"{prefix} {msg['content']}\n")
            print("───\n")
