"""Main agent loop for DSA Coach.

This is the entry point for the interactive coaching experience.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from ..storage.db import Database
from ..storage.migrations import check_migration_needed, migrate_from_json
from .agent import CoachAgent
from .sdk_agent import create_coach_agent
from .terminal import TerminalUI, format_time_ago

# Feature flag for using SDK agent (set via env or default True)
USE_SDK_AGENT = os.environ.get("DSA_COACH_USE_SDK", "1").lower() in ("1", "true", "yes")

# Exit commands
EXIT_COMMANDS = {"quit", "exit", "bye", "q"}
HELP_COMMANDS = {"help", "?", "h"}
STATUS_COMMANDS = {"status", "progress", "me"}
DASHBOARD_COMMANDS = {"dashboard", "dash", "d"}
PATTERN_COMMANDS = {"patterns", "list"}
RESUME_COMMANDS = {"resume", "/resume"}


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

        # Initialize agent (SDK or legacy based on feature flag)
        if USE_SDK_AGENT:
            agent = create_coach_agent(db, use_sdk=True)
        else:
            agent = CoachAgent(db)
        await agent.initialize()

        # Show dashboard
        if agent.dashboard:
            ui.render_dashboard(agent.dashboard)

        # Show welcome message
        greeting = await agent.get_greeting()
        ui.render_welcome(greeting)

        # Start session timer (visible in bottom toolbar)
        ui.start_session_timer()

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

                # Handle /resume command
                if command.lstrip("/") == "resume":
                    # Get current session ID to exclude from list
                    current_session_id = None
                    if agent.session.session:
                        current_session_id = agent.session.session.id

                    # List available sessions (excluding current)
                    sessions = await db.list_sessions(
                        limit=10,
                        exclude_session_id=current_session_id,
                    )

                    if not sessions:
                        ui.render_info("No previous sessions to resume.")
                        continue

                    # Show picker
                    ui.render_session_picker(sessions)
                    selection = await ui.get_session_selection(len(sessions))

                    if selection is None:
                        ui.render_info("Resume cancelled.")
                        continue

                    # Resume selected session
                    session_data = sessions[selection]
                    resumed = await agent.session.resume_by_id(session_data["id"])

                    if not resumed:
                        ui.render_error("Failed to resume session.")
                        continue

                    # CRITICAL: Refresh agent context after resume
                    await agent._refresh_student_context()
                    await agent._refresh_dashboard()

                    # Show FULL conversation history
                    all_messages = agent.session.get_display_messages()
                    if all_messages:
                        ui.render_conversation_history(all_messages)

                    # Show dashboard with updated state
                    if agent.dashboard:
                        ui.render_dashboard(agent.dashboard)

                    time_ago = format_time_ago(
                        datetime.fromisoformat(session_data["updated_at"])
                    )
                    ui.render_success(f"Resumed session from {time_ago}")
                    continue

                # Echo user message
                ui.render_message("user", user_input)

                # Process with agent
                ui.render_thinking()
                response = await agent.run(
                    user_input,
                    on_reasoning=ui.render_reasoning,
                )

                # Update token usage in UI for toolbar display
                if response.token_usage:
                    ui.update_token_usage(response.token_usage)

                # Show tool activity
                for tc in response.tool_calls_made:
                    ui.render_tool_activity(tc["name"])

                # Show tool errors prominently
                for te in response.tool_errors:
                    ui.render_tool_error(te["tool"], te["error"])

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
