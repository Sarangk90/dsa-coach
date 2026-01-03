#!/usr/bin/env python3
"""
Test Harness CLI for DSA Coach - Programmatic Testing Interface.

This script provides a JSON-based interface for automated testing of the coach agent.
It's designed to be driven by another program (like Cursor/Claude) for testing.

USAGE MODES:

1. Interactive JSON mode (stdin/stdout):
   python test_harness.py
   > {"action": "send", "message": "What should I work on?"}
   < {"type": "response", "content": "...", "tools_used": [...]}

2. Single command mode:
   python test_harness.py send "What should I work on?"
   python test_harness.py inspect patterns
   python test_harness.py snapshot

3. Script mode (run predefined test scenarios):
   python test_harness.py --scenario basic_conversation

ACTIONS:

  send <message>        Send a message to the agent
  inspect <entity>      Inspect database state (patterns, quests, mistakes, etc.)
  snapshot              Take a full database snapshot
  diff                  Compare current state to last snapshot
  hydrate               Populate with test data
  reset                 Clear all test data
  history               Show conversation history
  quit/exit             End the session

INSPECT ENTITIES:
  profile, patterns, quests, mistakes, milestones, teaching, concepts, session

EXAMPLES:

  # Send a message
  python test_harness.py send "I just completed the sliding window problem"

  # Check if a mistake was recorded
  python test_harness.py inspect mistakes

  # Run a test scenario
  python test_harness.py --scenario progress_tracking

  # Interactive mode for Claude/Cursor
  python test_harness.py --json
  {"action": "hydrate"}
  {"action": "send", "message": "What patterns am I weak at?"}
  {"action": "inspect", "entity": "patterns"}
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.harness.coach_harness import (
    CoachTestHarness,
    DatabaseSnapshot,
)

# =============================================================================
# JSON ENCODER
# =============================================================================


class HarnessJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime and Pydantic models."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)


def to_json(data: dict) -> str:
    """Convert data to JSON string."""
    return json.dumps(data, cls=HarnessJSONEncoder, indent=2)


# =============================================================================
# HARNESS RUNNER
# =============================================================================


class HarnessRunner:
    """Runs the test harness and handles commands."""

    def __init__(self, json_mode: bool = False):
        self.json_mode = json_mode
        self.harness: CoachTestHarness | None = None
        self._last_snapshot: DatabaseSnapshot | None = None

    async def setup(self) -> None:
        """Initialize the harness."""
        self.harness = CoachTestHarness(auto_hydrate=False)
        await self.harness.setup()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.harness:
            await self.harness.cleanup()

    def output(self, data: dict) -> None:
        """Output response data."""
        print(to_json(data), flush=True)

    async def handle_send(self, message: str) -> dict:
        """Handle a send message command."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}

        try:
            response = await self.harness.send(message)
            return {
                "type": "response",
                "content": response.content,
                "tools_used": response.tools_used,
                "tool_results": response.tool_results,
                "state_updated": response.state_updated,
                "error": response.error,
            }
        except Exception as e:
            return {"type": "error", "message": str(e)}

    async def handle_inspect(self, entity: str) -> dict:
        """Handle an inspect command."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}

        try:
            if entity == "profile":
                profile = await self.harness.inspect_profile()
                return {
                    "type": "inspect",
                    "entity": "profile",
                    "data": profile.model_dump(),
                }

            if entity == "patterns":
                patterns = await self.harness.inspect_patterns()
                return {
                    "type": "inspect",
                    "entity": "patterns",
                    "count": len(patterns),
                    "data": [p.model_dump() for p in patterns],
                }

            if entity == "quests":
                quests = await self.harness.inspect_quests()
                return {
                    "type": "inspect",
                    "entity": "quests",
                    "count": len(quests),
                    "data": [q.model_dump() for q in quests],
                }

            if entity == "mistakes":
                mistakes = await self.harness.inspect_mistakes()
                recurring = await self.harness.inspect_recurring_mistakes()
                return {
                    "type": "inspect",
                    "entity": "mistakes",
                    "count": len(mistakes),
                    "recurring": recurring,
                    "data": mistakes,  # Already dicts
                }

            if entity == "milestones":
                milestones = await self.harness.inspect_milestones()
                return {
                    "type": "inspect",
                    "entity": "milestones",
                    "count": len(milestones),
                    "data": milestones,  # Already dicts
                }

            if entity == "teaching":
                teaching = await self.harness.inspect_teaching_history()
                return {
                    "type": "inspect",
                    "entity": "teaching",
                    "count": len(teaching),
                    "data": teaching,  # Already dicts
                }

            if entity == "concepts":
                concepts = await self.harness.inspect_concepts()
                return {
                    "type": "inspect",
                    "entity": "concepts",
                    "count": len(concepts),
                    "data": [
                        c.model_dump() for c in concepts
                    ],  # These are Pydantic models
                }

            if entity == "session":
                session = await self.harness.inspect_current_session()
                return {"type": "inspect", "entity": "session", "data": session}

            if entity == "reviews":
                reviews = await self.harness.inspect_due_reviews()
                return {
                    "type": "inspect",
                    "entity": "reviews",
                    "count": len(reviews),
                    "data": [r.model_dump() for r in reviews],
                }

            if entity == "activity":
                activity = await self.harness.inspect_weekly_activity()
                return {"type": "inspect", "entity": "activity", "data": activity}

            return {
                "type": "error",
                "message": f"Unknown entity: {entity}. Valid: profile, patterns, quests, mistakes, milestones, teaching, concepts, session, reviews, activity",
            }

        except Exception as e:
            return {"type": "error", "message": str(e)}

    async def handle_snapshot(self) -> dict:
        """Take a database snapshot."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}

        try:
            snapshot = await self.harness.snapshot()
            self._last_snapshot = snapshot
            return {
                "type": "snapshot",
                "timestamp": snapshot.timestamp.isoformat(),
                "summary": {
                    "profile": snapshot.profile.name if snapshot.profile else None,
                    "patterns_count": len(snapshot.patterns),
                    "quests_count": len(snapshot.quests),
                    "mistakes_count": len(snapshot.mistakes),
                    "milestones_count": len(snapshot.milestones),
                },
            }
        except Exception as e:
            return {"type": "error", "message": str(e)}

    async def handle_diff(self) -> dict:
        """Compare current state to last snapshot."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}
        if not self._last_snapshot:
            return {
                "type": "error",
                "message": "No previous snapshot. Run 'snapshot' first.",
            }

        try:
            current = await self.harness.snapshot()
            diff = self.harness.diff_snapshot(self._last_snapshot, current)
            return {
                "type": "diff",
                "from_timestamp": self._last_snapshot.timestamp.isoformat(),
                "to_timestamp": current.timestamp.isoformat(),
                "changes": diff,
            }
        except Exception as e:
            return {"type": "error", "message": str(e)}

    async def handle_hydrate(self) -> dict:
        """Populate with test data."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}

        try:
            await self.harness.hydrate_test_data()
            # Re-initialize agent to pick up new data
            await self.harness.agent.initialize()
            return {
                "type": "success",
                "message": "Test data hydrated successfully",
            }
        except Exception as e:
            return {"type": "error", "message": str(e)}

    async def handle_history(self) -> dict:
        """Get conversation history."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}

        history = self.harness.get_conversation_history()
        return {
            "type": "history",
            "count": len(history),
            "messages": history,
        }

    async def handle_greeting(self) -> dict:
        """Get the agent's greeting."""
        if not self.harness:
            return {"type": "error", "message": "Harness not initialized"}

        try:
            greeting = await self.harness.get_greeting()
            return {"type": "greeting", "content": greeting}
        except Exception as e:
            return {"type": "error", "message": str(e)}

    async def process_command(self, command: dict | str) -> dict:
        """Process a command and return the result."""
        # Parse string commands
        if isinstance(command, str):
            parts = command.strip().split(maxsplit=1)
            if not parts:
                return {"type": "error", "message": "Empty command"}

            action = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if action == "send":
                return await self.handle_send(args)
            if action == "inspect":
                return await self.handle_inspect(args.strip())
            if action == "snapshot":
                return await self.handle_snapshot()
            if action == "diff":
                return await self.handle_diff()
            if action == "hydrate":
                return await self.handle_hydrate()
            if action == "history":
                return await self.handle_history()
            if action == "greeting":
                return await self.handle_greeting()
            if action in ("quit", "exit"):
                return {"type": "goodbye", "message": "Session ended"}
            if action == "help":
                return {
                    "type": "help",
                    "commands": [
                        "send <message> - Send a message to the agent",
                        "inspect <entity> - Inspect database state",
                        "snapshot - Take a database snapshot",
                        "diff - Compare to last snapshot",
                        "hydrate - Populate with test data",
                        "history - Show conversation history",
                        "greeting - Get agent greeting",
                        "quit/exit - End session",
                    ],
                    "entities": [
                        "profile",
                        "patterns",
                        "quests",
                        "mistakes",
                        "milestones",
                        "teaching",
                        "concepts",
                        "session",
                        "reviews",
                        "activity",
                    ],
                }
            return {"type": "error", "message": f"Unknown command: {action}"}

        # Handle dict commands (JSON mode)
        action = command.get("action", "").lower()

        if action == "send":
            return await self.handle_send(command.get("message", ""))
        if action == "inspect":
            return await self.handle_inspect(command.get("entity", ""))
        if action == "snapshot":
            return await self.handle_snapshot()
        if action == "diff":
            return await self.handle_diff()
        if action == "hydrate":
            return await self.handle_hydrate()
        if action == "history":
            return await self.handle_history()
        if action == "greeting":
            return await self.handle_greeting()
        if action in ("quit", "exit"):
            return {"type": "goodbye", "message": "Session ended"}
        return {"type": "error", "message": f"Unknown action: {action}"}


# =============================================================================
# TEST SCENARIOS
# =============================================================================


async def run_scenario(scenario: str) -> None:
    """Run a predefined test scenario."""
    runner = HarnessRunner(json_mode=True)

    scenarios = {
        "basic_conversation": [
            {"action": "hydrate"},
            {"action": "greeting"},
            {"action": "send", "message": "What should I work on next?"},
            {"action": "send", "message": "Tell me about sliding window pattern"},
            {"action": "inspect", "entity": "patterns"},
        ],
        "progress_tracking": [
            {"action": "hydrate"},
            {"action": "snapshot"},
            {
                "action": "send",
                "message": "I just completed the Two Sum problem without any hints. It took me 20 minutes.",
            },
            {"action": "diff"},
            {"action": "inspect", "entity": "quests"},
        ],
        "mistake_recording": [
            {"action": "hydrate"},
            {"action": "snapshot"},
            {
                "action": "send",
                "message": "I made an off-by-one error in my sliding window solution. I forgot the window end is exclusive.",
            },
            {"action": "diff"},
            {"action": "inspect", "entity": "mistakes"},
        ],
        "teaching_flow": [
            {"action": "hydrate"},
            {
                "action": "send",
                "message": "I don't understand how to shrink the window in sliding window problems",
            },
            {"action": "inspect", "entity": "teaching"},
            {"action": "send", "message": "OK that makes more sense now, thanks!"},
            {"action": "inspect", "entity": "concepts"},
        ],
    }

    if scenario not in scenarios:
        print(f"Unknown scenario: {scenario}")
        print(f"Available: {', '.join(scenarios.keys())}")
        return

    print(f"\n{'=' * 60}")
    print(f"Running scenario: {scenario}")
    print(f"{'=' * 60}\n")

    await runner.setup()

    try:
        for step in scenarios[scenario]:
            print(f"\n>>> {json.dumps(step)}")
            result = await runner.process_command(step)
            runner.output(result)
    finally:
        await runner.cleanup()


# =============================================================================
# MAIN
# =============================================================================


async def run_interactive(json_mode: bool = False) -> None:
    """Run the harness in interactive mode."""
    runner = HarnessRunner(json_mode=json_mode)

    await runner.setup()
    runner.output({"type": "ready", "message": "Test harness initialized"})

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            # Parse input
            if json_mode or line.startswith("{"):
                try:
                    command = json.loads(line)
                except json.JSONDecodeError:
                    runner.output({"type": "error", "message": "Invalid JSON"})
                    continue
            else:
                command = line

            result = await runner.process_command(command)
            runner.output(result)

            if result.get("type") == "goodbye":
                break

    finally:
        await runner.cleanup()


async def run_single_command(args: argparse.Namespace) -> None:
    """Run a single command and exit."""
    runner = HarnessRunner(json_mode=True)
    await runner.setup()

    try:
        # Handle different command types
        if args.action == "send":
            result = await runner.handle_send(" ".join(args.args))
        elif args.action == "inspect":
            result = await runner.handle_inspect(args.args[0] if args.args else "")
        elif args.action == "snapshot":
            result = await runner.handle_snapshot()
        elif args.action == "hydrate":
            result = await runner.handle_hydrate()
        elif args.action == "greeting":
            result = await runner.handle_greeting()
        else:
            result = {"type": "error", "message": f"Unknown action: {args.action}"}

        runner.output(result)

    finally:
        await runner.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test harness for DSA Coach agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Use strict JSON mode for input/output",
    )

    parser.add_argument(
        "--scenario",
        "-s",
        help="Run a predefined test scenario",
        choices=[
            "basic_conversation",
            "progress_tracking",
            "mistake_recording",
            "teaching_flow",
        ],
    )

    parser.add_argument(
        "action",
        nargs="?",
        help="Action to perform (send, inspect, snapshot, hydrate, greeting)",
    )

    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for the action",
    )

    args = parser.parse_args()

    try:
        if args.scenario:
            asyncio.run(run_scenario(args.scenario))
        elif args.action:
            asyncio.run(run_single_command(args))
        else:
            asyncio.run(run_interactive(json_mode=args.json))
    except KeyboardInterrupt:
        print(json.dumps({"type": "interrupted"}), flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
