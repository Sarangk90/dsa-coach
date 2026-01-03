from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UI:
    """Small wrapper around rich vs plain printing.

    We keep the interface intentionally tiny to avoid leaking rich details
    throughout the codebase.
    """

    rich_available: bool
    console: object | None

    def print_styled(self, text: str, style: str = "") -> None:
        if self.rich_available and self.console is not None:
            # type: ignore[union-attr]
            self.console.print(text, style=style)
        else:
            print(text)

    def print_panel(self, title: str, content: str, style: str = "blue") -> None:
        if self.rich_available and self.console is not None:
            from rich.panel import Panel

            # type: ignore[union-attr]
            self.console.print(Panel(content, title=title, border_style=style))
        else:
            print(f"\n{'=' * 50}")
            print(f" {title}")
            print(f"{'=' * 50}")
            print(content)
            print(f"{'=' * 50}\n")
