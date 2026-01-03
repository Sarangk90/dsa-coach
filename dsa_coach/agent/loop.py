"""Main agent loop for DSA Coach.

This is the entry point for the interactive coaching experience.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from ..storage.db import Database
from ..storage.migrations import check_migration_needed, migrate_from_json
from .agent import CoachAgent
from .terminal import TerminalUI

# Exit commands
EXIT_COMMANDS = {"quit", "exit", "bye", "q"}
HELP_COMMANDS = {"help", "?", "h"}
STATUS_COMMANDS = {"status", "progress", "me"}
DASHBOARD_COMMANDS = {"dashboard", "dash", "d"}
PATTERN_COMMANDS = {"patterns", "list"}


async def run_agent_loop(db_path: Path | None = None) -> None:
    """
    Run the main agent loop.

    This is the primary entry point for the interactive coaching experience.

    Args:
        db_path: Optional path to the SQLite database
    """
    ui = TerminalUI()

    # Clear screen and show header
    ui.clear()
    ui.print_header()

    # Initialize database
    db = Database(db_path) if db_path else Database()

    try:
        await db.connect()

        # Check for migration from JSON
        if await check_migration_needed(db):
            ui.render_info("Migrating existing progress to new format...")
            result = await migrate_from_json(db)
            if result.get("status") == "success":
                ui.render_success("Progress migrated successfully!")
            elif result.get("status") == "error":
                ui.render_error(f"Migration error: {result.get('reason')}")

        # Initialize agent
        agent = CoachAgent(db)
        await agent.initialize()

        # Show dashboard
        if agent.dashboard:
            ui.render_dashboard(agent.dashboard)

        # Show welcome message
        greeting = await agent.get_greeting()
        ui.render_welcome(greeting)

        # Show input hint
        ui.render_info(
            "💡 Ctrl+J for newlines, Enter to send, Ctrl+D to exit. Type 'help' for commands."
        )

        # Main loop
        while True:
            try:
                # Get user input (supports multiline with prompt_toolkit)
                try:
                    user_input = await ui.get_input()
                except EOFError:
                    # Ctrl+D → exit
                    break

                # Handle cancelled input (Ctrl+C)
                if user_input is None:
                    ui.render_info("Message cancelled.")
                    continue

                if not user_input.strip():
                    continue

                # Check for special commands
                command = user_input.strip().lower()

                if command in EXIT_COMMANDS:
                    break

                if command in HELP_COMMANDS:
                    ui.render_help()
                    continue

                if command in DASHBOARD_COMMANDS:
                    await agent._refresh_dashboard()
                    if agent.dashboard:
                        ui.render_dashboard(agent.dashboard)
                    continue

                # Echo user message
                ui.render_message("user", user_input)

                # Process with agent
                ui.render_thinking()
                response = await agent.run(
                    user_input,
                    on_reasoning=ui.render_reasoning,
                )

                # Show tool activity
                for tc in response.tool_calls_made:
                    ui.render_tool_activity(tc["name"])

                # Refresh dashboard if state changed
                if response.state_updated and agent.dashboard:
                    ui.render_dashboard(agent.dashboard)

                # Show response
                if response.content:
                    ui.render_message("assistant", response.content)

                if response.error:
                    ui.render_error(response.error)

            except KeyboardInterrupt:
                ui.render_info("\nUse 'quit' to exit or press Ctrl+D to force quit.")
                continue
            except Exception as e:
                ui.render_error(f"An error occurred: {str(e)}")

        # Goodbye
        ui.render_goodbye()

    finally:
        await db.close()


def main() -> None:
    """Entry point for the agent loop."""
    try:
        asyncio.run(run_agent_loop())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
