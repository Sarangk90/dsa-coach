"""SDK-integrated CoachAgent using claude-agent-sdk.

This module provides a new agent implementation that uses the Claude Agent SDK
for more robust tool orchestration, hooks, and session management.

The SDKCoachAgent wraps the consolidated tools and provides:
- Native SDK tool registration
- PostToolUse hooks for deterministic follow-ups
- Workflow state management
- Better context handling
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from claude_agent_sdk import (
    ClaudeSDKClient,
    HookContext,
)

from ..ai.client import PREFERRED_PROVIDER, TokenUsage
from ..ai.prompts import build_student_context, get_agent_system_prompt
from ..storage.db import Database
from ..tools.registry import ToolRegistry, ToolResult
from .session import SessionManager
from .workflows import SessionMode, WorkflowManager, WorkflowState


@dataclass
class SDKAgentResponse:
    """Response from the SDK agent to the user."""

    content: str
    tool_calls_made: list[dict] = field(default_factory=list)
    tool_errors: list[dict] = field(default_factory=list)
    state_updated: bool = False
    error: str | None = None
    token_usage: TokenUsage | None = None
    workflow_state: WorkflowState | None = None


class SDKCoachAgent:
    """
    AI-powered DSA coaching agent using Claude Agent SDK.

    This agent uses the consolidated tools and provides:
    - Workflow state management via WorkflowManager
    - PostToolUse hooks for deterministic actions
    - Native SDK tool orchestration
    """

    def __init__(
        self,
        db: Database,
        user_id: str = "default",
        max_tool_iterations: int = 5,
    ):
        self.db = db
        self.user_id = user_id
        self.max_tool_iterations = max_tool_iterations

        self.tools = ToolRegistry()
        self.session = SessionManager(db, user_id)
        self.workflow = WorkflowManager()

        self._dashboard_state: dict | None = None
        self._student_context: str | None = None
        self._token_usage: TokenUsage | None = None
        self._sdk_client: ClaudeSDKClient | None = None

    async def initialize(self) -> None:
        """Initialize the agent, starting or resuming a session."""
        await self.session.start_or_resume()
        await self._refresh_student_context()

        # Initialize token usage tracking
        context_limit = 200_000 if PREFERRED_PROVIDER == "anthropic" else 128_000
        self._token_usage = TokenUsage(context_limit=context_limit)

        # Restore workflow state from session metadata if available
        db_session = await self.db.get_latest_session(self.user_id)
        if db_session and db_session.metadata:
            with contextlib.suppress(Exception):
                self.workflow.state = WorkflowState.from_dict(db_session.metadata)

    async def _refresh_student_context(self) -> None:
        """Refresh the comprehensive student context for system prompt."""
        try:
            self._student_context = await build_student_context(self.db, self.user_id)
        except Exception:
            self._student_context = None

    async def _refresh_dashboard(self) -> None:
        """Refresh the dashboard state for context."""
        from ..tools.consolidated import get_dashboard

        result = await get_dashboard(self.db, self.user_id)
        if result.success:
            self._dashboard_state = result.data

    def get_system_prompt(self) -> str:
        """Get the system prompt with student context."""
        return get_agent_system_prompt(
            dashboard_state=self._dashboard_state,
            student_context=self._student_context,
        )

    def get_tools_for_llm(self) -> list[dict]:
        """Get tool definitions for the SDK agent."""
        return self.tools.to_anthropic_tools()

    async def _create_post_tool_hook(
        self,
    ) -> Callable[[dict, str | None, HookContext], Any]:
        """Create a PostToolUse hook for deterministic follow-ups."""

        async def post_tool_hook(
            input_data: dict[str, Any],
            tool_use_id: str | None,
            context: HookContext,
        ) -> dict[str, Any]:
            """Hook that runs after each tool completes."""
            tool_name = input_data.get("tool_name", "")
            tool_response = input_data.get("tool_response", {})

            # Update workflow state based on tool
            if tool_name == "start_quest":
                data = tool_response.get("content", {})
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        data = {}

                if data.get("quest_id"):
                    self.workflow.start_quest(
                        quest_id=data.get("quest_id", ""),
                        pattern_id=data.get("pattern_id", ""),
                        progress=0,  # Will be updated from DB
                    )

            elif tool_name == "complete_quest":
                self.workflow.complete_quest()

            elif tool_name == "diagnose_understanding":
                data = tool_response.get("content", {})
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        data = {}

                if data.get("pattern_id"):
                    self.workflow.start_learning(
                        pattern_id=data.get("pattern_id", ""),
                        progress=0,
                    )

            # Persist workflow state to session
            try:
                db_session = await self.db.get_latest_session(self.user_id)
                if db_session:
                    db_session.metadata = self.workflow.state.to_dict()
                    await self.db.update_session(db_session)
            except Exception:
                pass  # Don't fail on state persistence

            return {}

        return post_tool_hook

    async def run(
        self,
        user_message: str,
        on_reasoning: Callable[[str], None] | None = None,
    ) -> SDKAgentResponse:
        """
        Process a user message and return a response.

        Uses the existing infrastructure but with workflow state tracking.

        Args:
            user_message: The user's input
            on_reasoning: Optional callback to show reasoning text

        Returns:
            SDKAgentResponse with content and metadata
        """
        # Increment message count
        self.workflow.increment_message_count()

        # Record user message
        await self.session.add_user_message(user_message)

        # Build messages for LLM (handles thinking block formatting)
        messages = self.session.get_messages_for_llm()

        # Get LLM response using existing infrastructure
        from ..ai.client import (
            format_tool_result_for_anthropic,
            get_ai_response_with_tools,
        )

        # Thinking stays enabled; session formatting handles replay requirements.
        try:
            response = await get_ai_response_with_tools(
                messages=messages,
                system_prompt=self.get_system_prompt(),
                tools=self.get_tools_for_llm(),
                # enable_thinking=None uses default (THINKING_BUDGET)
            )
        except Exception as e:
            return SDKAgentResponse(
                content="I'm having trouble connecting to the AI service. Please check your API keys.",
                error=str(e),
                token_usage=self._token_usage,
                workflow_state=self.workflow.state,
            )

        # Update token usage
        if self._token_usage:
            self._token_usage.set_from_response(response)

        # Handle tool calls
        tool_calls_made = []
        all_tool_errors = []
        iterations = 0

        # Surface extended thinking content (Anthropic only)
        if response.thinking and on_reasoning:
            on_reasoning(response.thinking)

        if response.has_tool_calls and response.content and on_reasoning:
            on_reasoning(response.content)

        while response.has_tool_calls and iterations < self.max_tool_iterations:
            iterations += 1

            # Execute tool calls with workflow hooks
            tool_results, tool_errors = await self._execute_tool_calls_with_hooks(
                response.tool_calls
            )
            tool_calls_made.extend(
                [{"name": tc.name, "args": tc.arguments} for tc in response.tool_calls]
            )
            all_tool_errors.extend(tool_errors)

            # Build messages with tool results
            # Include thinking block WITH signature for proper replay
            assistant_content = []
            if response.thinking and response.thinking_signature:
                assistant_content.append(
                    {
                        "type": "thinking",
                        "thinking": response.thinking,
                        "signature": response.thinking_signature,
                    }
                )
            if response.content:
                assistant_content.append({"type": "text", "text": response.content})
            for tc in response.tool_calls:
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    }
                )

            messages.append({"role": "assistant", "content": assistant_content})
            tool_result_content = format_tool_result_for_anthropic(tool_results)
            messages.append({"role": "user", "content": tool_result_content})

            # Get next LLM response - KEEP thinking enabled (we have proper signatures now)
            try:
                response = await get_ai_response_with_tools(
                    messages=messages,
                    system_prompt=self.get_system_prompt(),
                    tools=self.get_tools_for_llm(),
                    # enable_thinking=None uses default (THINKING_BUDGET)
                )
            except Exception as e:
                return SDKAgentResponse(
                    content="An error occurred while processing. Please try again.",
                    tool_calls_made=tool_calls_made,
                    error=str(e),
                    token_usage=self._token_usage,
                    workflow_state=self.workflow.state,
                )

            if self._token_usage:
                self._token_usage.set_from_response(response)

            # Surface extended thinking content (Anthropic only)
            if response.thinking and on_reasoning:
                on_reasoning(response.thinking)

            if response.has_tool_calls and response.content and on_reasoning:
                on_reasoning(response.content)

        # Record final assistant response (with thinking + signature for replay)
        if response.content:
            await self.session.add_assistant_message(
                response.content,
                thinking=response.thinking,
                thinking_signature=response.thinking_signature,
            )

        # Refresh student context after tool calls
        if tool_calls_made:
            await self._refresh_student_context()

        content = response.content
        if not content and tool_calls_made:
            content = "I've updated your progress. What would you like to do next?"

        return SDKAgentResponse(
            content=content,
            tool_calls_made=tool_calls_made,
            tool_errors=all_tool_errors,
            state_updated=bool(tool_calls_made),
            token_usage=self._token_usage,
            workflow_state=self.workflow.state,
        )

    async def _execute_tool_calls_with_hooks(
        self, tool_calls: list
    ) -> tuple[list, list[dict]]:
        """Execute tool calls with workflow hooks.

        This wraps the standard tool execution with hooks that update
        workflow state after each tool completes.
        """
        from ..ai.client import ToolResult as LLMToolResult

        results = []
        errors_for_ui = []

        for tc in tool_calls:
            await self.session.add_tool_call(tc.name, tc.arguments)

            kwargs = {**tc.arguments, "db": self.db, "user_id": self.user_id}

            try:
                result = await self.tools.execute(tc.name, **kwargs)

                # Format result for LLM
                if result.success:
                    if result.data is not None:
                        content = json.dumps(result.data, indent=2, default=str)
                    else:
                        content = result.message or "Success"
                else:
                    content = f"Error: {result.error or result.message}"
                    errors_for_ui.append(
                        {
                            "tool": tc.name,
                            "error": result.error or result.message or "Unknown error",
                        }
                    )

                results.append(
                    LLMToolResult(
                        tool_use_id=tc.id,
                        content=content,
                        is_error=not result.success,
                    )
                )

                await self.session.add_tool_result(
                    tc.name, content, is_error=not result.success
                )

                # === WORKFLOW HOOK: Update state based on tool ===
                await self._apply_workflow_hook(tc.name, result)

            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                errors_for_ui.append({"tool": tc.name, "error": str(e)})
                results.append(
                    LLMToolResult(
                        tool_use_id=tc.id,
                        content=error_msg,
                        is_error=True,
                    )
                )
                await self.session.add_tool_result(tc.name, error_msg, is_error=True)

        return results, errors_for_ui

    async def _apply_workflow_hook(self, tool_name: str, result: ToolResult) -> None:
        """Apply workflow state changes based on tool execution."""
        if not result.success or not result.data:
            return

        data = result.data

        if tool_name == "start_quest":
            self.workflow.start_quest(
                quest_id=data.get("quest_id", ""),
                pattern_id=data.get("pattern_id", ""),
                progress=0,
            )

        elif tool_name == "complete_quest":
            self.workflow.complete_quest()

        elif tool_name == "diagnose_understanding":
            self.workflow.start_learning(
                pattern_id=data.get("pattern_id", ""),
                progress=0,
            )

        elif tool_name == "get_progress_summary":
            due_count = data.get("due_reviews_count", 0)
            if due_count > 0 and self.workflow.state.mode == SessionMode.GREETING:
                self.workflow.start_review()

        # Persist workflow state
        try:
            db_session = await self.db.get_latest_session(self.user_id)
            if db_session:
                db_session.metadata = self.workflow.state.to_dict()
                await self.db.update_session(db_session)
        except Exception:
            pass

    async def get_greeting(self) -> str:
        """Get a contextual greeting for a new session."""
        await self._refresh_dashboard()

        if not self._dashboard_state:
            return "Welcome to DSA Coach! What would you like to work on today?"

        data = self._dashboard_state
        profile = data.get("profile", {})
        alerts = data.get("alerts", [])
        current = data.get("current_quest")

        greeting_parts = []

        name = profile.get("name", "there")
        greeting_parts.append(f"Hey {name}! Ready to level up?")

        if current:
            greeting_parts.append(
                f"You were working on '{current['title']}' ({current['pattern_name']}). "
                "Want to continue?"
            )

        for alert in alerts[:2]:
            if alert["type"] == "review":
                greeting_parts.append(f"Note: {alert['message']}")

        if not current and not alerts:
            weak_patterns = data.get("weak_patterns", [])
            if weak_patterns:
                weak = weak_patterns[0]
                greeting_parts.append(
                    f"Based on your progress, I'd suggest focusing on {weak['pattern_name']} "
                    f"(currently at {weak['progress']}% progress)."
                )
            else:
                greeting_parts.append("What pattern would you like to focus on today?")

        return " ".join(greeting_parts)

    @property
    def dashboard(self) -> dict | None:
        """Get the current dashboard state."""
        return self._dashboard_state

    @property
    def current_mode(self) -> SessionMode:
        """Get the current workflow mode."""
        return self.workflow.state.mode
