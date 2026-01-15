"""Main CoachAgent class for DSA Coach.

The CoachAgent orchestrates the AI coaching experience,
handling user messages, tool calls, and state management.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from ..ai.client import (
    PREFERRED_PROVIDER,
    TokenUsage,
    ToolCall,
    format_tool_result_for_anthropic,
    get_ai_response_with_tools,
)
from ..ai.client import (
    ToolResult as LLMToolResult,
)
from ..ai.prompts import get_agent_system_prompt
from ..storage.db import Database
from ..tools import ToolRegistry
from .session import SessionManager


@dataclass
class AgentResponse:
    """Response from the agent to the user."""

    content: str
    tool_calls_made: list[dict] = field(default_factory=list)
    tool_errors: list[dict] = field(default_factory=list)  # {tool: str, error: str}
    state_updated: bool = False
    error: str | None = None
    token_usage: TokenUsage | None = None


class CoachAgent:
    """
    AI-powered DSA coaching agent.

    The agent:
    - Maintains conversation state via SessionManager
    - Executes tools to manage user progress
    - Provides adaptive mentorship based on user state
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

        self._dashboard_state: dict | None = None
        self._student_context: str | None = None
        self._token_usage: TokenUsage | None = None

    async def initialize(self) -> None:
        """Initialize the agent, starting or resuming a session."""
        await self.session.start_or_resume()
        await self._refresh_student_context()

        # Initialize token usage tracking with appropriate context limit
        # Claude Sonnet: 200k tokens, GPT-4o: 128k tokens
        context_limit = 200_000 if PREFERRED_PROVIDER == "anthropic" else 128_000
        self._token_usage = TokenUsage(context_limit=context_limit)

    async def _refresh_dashboard(self) -> None:
        """Refresh the dashboard state for context (legacy)."""
        from ..tools.external import get_dashboard_state

        result = await get_dashboard_state(self.db, self.user_id)
        if result.success:
            self._dashboard_state = result.data

    async def _refresh_student_context(self) -> None:
        """Refresh the comprehensive student context for system prompt."""
        from ..ai.prompts import build_student_context

        try:
            self._student_context = await build_student_context(self.db, self.user_id)
        except Exception:
            # Fallback to dashboard state if context build fails
            await self._refresh_dashboard()
            self._student_context = None

    def get_system_prompt(self) -> str:
        """Get the system prompt with student context."""
        return get_agent_system_prompt(
            dashboard_state=self._dashboard_state, student_context=self._student_context
        )

    def get_tools_for_llm(self) -> list[dict]:
        """Get tool definitions in Anthropic format."""
        return self.tools.to_anthropic_tools()

    async def run(
        self,
        user_message: str,
        on_reasoning: Callable[[str], None] | None = None,
    ) -> AgentResponse:
        """
        Process a user message and return a response.

        This may involve multiple LLM calls if tools are used.

        Args:
            user_message: The user's input
            on_reasoning: Optional callback to show reasoning text before tool calls

        Returns:
            AgentResponse with content and metadata
        """
        # Record user message
        await self.session.add_user_message(user_message)

        # Build messages for LLM
        messages = self.session.get_messages_for_llm()

        # Get LLM response (may include tool calls)
        try:
            response = await get_ai_response_with_tools(
                messages=messages,
                system_prompt=self.get_system_prompt(),
                tools=self.get_tools_for_llm(),
            )
        except Exception as e:
            return AgentResponse(
                content="I'm having trouble connecting to the AI service. Please check your API keys.",
                error=str(e),
                token_usage=self._token_usage,
            )

        # Update token usage from this response (shows latest call's usage)
        if self._token_usage:
            self._token_usage.set_from_response(response)

        # Handle tool calls in a loop
        tool_calls_made = []
        all_tool_errors = []
        iterations = 0

        # Show reasoning for initial response if it has tool calls
        if response.has_tool_calls and response.content and on_reasoning:
            on_reasoning(response.content)

        while response.has_tool_calls and iterations < self.max_tool_iterations:
            iterations += 1

            # Execute tool calls
            tool_results, tool_errors = await self._execute_tool_calls(
                response.tool_calls
            )
            tool_calls_made.extend(
                [{"name": tc.name, "args": tc.arguments} for tc in response.tool_calls]
            )
            all_tool_errors.extend(tool_errors)

            # Build messages with tool results
            # For Anthropic, we need to include the assistant's response with tool_use
            # followed by a user message with tool_result

            # Add assistant message with tool calls
            assistant_content = []
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

            # Add tool results
            tool_result_content = format_tool_result_for_anthropic(tool_results)
            messages.append({"role": "user", "content": tool_result_content})

            # Get next LLM response
            try:
                response = await get_ai_response_with_tools(
                    messages=messages,
                    system_prompt=self.get_system_prompt(),
                    tools=self.get_tools_for_llm(),
                )
            except Exception as e:
                return AgentResponse(
                    content="An error occurred while processing. Please try again.",
                    tool_calls_made=tool_calls_made,
                    error=str(e),
                    token_usage=self._token_usage,
                )

            # Update token usage from this response (shows latest call's usage)
            if self._token_usage:
                self._token_usage.set_from_response(response)

            # Show reasoning for new response if it has more tool calls
            if response.has_tool_calls and response.content and on_reasoning:
                on_reasoning(response.content)

        # Record final assistant response
        if response.content:
            await self.session.add_assistant_message(response.content)

        # Refresh student context after tool calls (state may have changed)
        if tool_calls_made:
            await self._refresh_student_context()

        # If no content after tool calls, add a helpful message
        content = response.content
        if not content and tool_calls_made:
            content = "I've updated your progress. What would you like to do next?"

        return AgentResponse(
            content=content,
            tool_calls_made=tool_calls_made,
            tool_errors=all_tool_errors,
            state_updated=bool(tool_calls_made),
            token_usage=self._token_usage,
        )

    async def _execute_tool_calls(
        self, tool_calls: list[ToolCall]
    ) -> tuple[list[LLMToolResult], list[dict]]:
        """Execute tool calls and return results with any errors.

        Returns:
            Tuple of (LLM results, list of errors for UI display)
            Each error is a dict with 'tool' and 'error' keys.
        """
        results = []
        errors_for_ui = []

        for tc in tool_calls:
            # Record tool call
            await self.session.add_tool_call(tc.name, tc.arguments, tc.id)

            # Execute tool
            # Inject db and user_id into tool args
            kwargs = {**tc.arguments, "db": self.db, "user_id": self.user_id}

            try:
                result = await self.tools.execute(tc.name, **kwargs)

                # Format result as string for LLM
                if result.success:
                    if result.data is not None:
                        content = json.dumps(result.data, indent=2, default=str)
                    else:
                        content = result.message or "Success"
                else:
                    content = f"Error: {result.error}"
                    # Track error for UI display
                    errors_for_ui.append(
                        {"tool": tc.name, "error": result.error or "Unknown error"}
                    )

                results.append(
                    LLMToolResult(
                        tool_use_id=tc.id,
                        content=content,
                        is_error=not result.success,
                    )
                )

                # Record tool result
                await self.session.add_tool_result(
                    tc.name, tc.id, content, is_error=not result.success
                )

            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                # Track error for UI display
                errors_for_ui.append({"tool": tc.name, "error": str(e)})
                results.append(
                    LLMToolResult(
                        tool_use_id=tc.id,
                        content=error_msg,
                        is_error=True,
                    )
                )
                await self.session.add_tool_result(
                    tc.name, tc.id, error_msg, is_error=True
                )

        return results, errors_for_ui

    async def get_greeting(self) -> str:
        """Get a contextual greeting for a new session."""
        # Use dashboard for greeting-specific data, but also refresh full context
        await self._refresh_dashboard()
        await self._refresh_student_context()

        if not self._dashboard_state:
            return "Welcome to DSA Coach! I'm your AI mentor for mastering algorithms and data structures. What would you like to work on today?"

        profile = self._dashboard_state.get("profile", {})
        alerts = self._dashboard_state.get("alerts", [])
        current = self._dashboard_state.get("current_quest")

        greeting_parts = []

        # Personalized greeting
        name = profile.get("name", "there")
        greeting_parts.append(f"Hey {name}! Ready to level up?")

        # Current quest reminder
        if current:
            greeting_parts.append(
                f"You were working on '{current['title']}' ({current['pattern']}). "
                "Want to continue?"
            )

        # Alerts
        for alert in alerts[:2]:
            if alert["type"] == "review":
                greeting_parts.append(f"📋 {alert['message']}")

        if not current and not alerts:
            greeting_parts.append("What pattern would you like to focus on today?")

        return " ".join(greeting_parts)

    @property
    def dashboard(self) -> dict | None:
        """Get the current dashboard state."""
        return self._dashboard_state
