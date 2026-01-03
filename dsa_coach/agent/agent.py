"""Main CoachAgent class for DSA Coach.

The CoachAgent orchestrates the AI coaching experience,
handling user messages, tool calls, and state management.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..storage.db import Database
from ..tools import ToolRegistry
from ..tools.registry import ToolResult
from ..ai.client import (
    get_ai_response_with_tools,
    LLMResponse,
    ToolCall,
    ToolResult as LLMToolResult,
    format_tool_result_for_anthropic,
)
from ..ai.prompts import get_agent_system_prompt
from .session import SessionManager


@dataclass
class AgentResponse:
    """Response from the agent to the user."""
    
    content: str
    tool_calls_made: list[dict] = field(default_factory=list)
    state_updated: bool = False
    error: Optional[str] = None


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

        self._dashboard_state: Optional[dict] = None
        self._student_context: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the agent, starting or resuming a session."""
        await self.session.start_or_resume()
        await self._refresh_student_context()

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
            dashboard_state=self._dashboard_state,
            student_context=self._student_context
        )
    
    def get_tools_for_llm(self) -> list[dict]:
        """Get tool definitions in Anthropic format."""
        return self.tools.to_anthropic_tools()
    
    async def run(
        self,
        user_message: str,
        on_reasoning: Optional[Callable[[str], None]] = None,
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
            )
        
        # Handle tool calls in a loop
        tool_calls_made = []
        iterations = 0

        # Show reasoning for initial response if it has tool calls
        if response.has_tool_calls and response.content and on_reasoning:
            on_reasoning(response.content)

        while response.has_tool_calls and iterations < self.max_tool_iterations:
            iterations += 1

            # Execute tool calls
            tool_results = await self._execute_tool_calls(response.tool_calls)
            tool_calls_made.extend([
                {"name": tc.name, "args": tc.arguments}
                for tc in response.tool_calls
            ])
            
            # Build messages with tool results
            # For Anthropic, we need to include the assistant's response with tool_use
            # followed by a user message with tool_result
            
            # Add assistant message with tool calls
            assistant_content = []
            if response.content:
                assistant_content.append({"type": "text", "text": response.content})
            for tc in response.tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            
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
                )

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
            state_updated=bool(tool_calls_made),
        )
    
    async def _execute_tool_calls(
        self, tool_calls: list[ToolCall]
    ) -> list[LLMToolResult]:
        """Execute tool calls and return results."""
        results = []
        
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
                
                results.append(LLMToolResult(
                    tool_use_id=tc.id,
                    content=content,
                    is_error=not result.success,
                ))
                
                # Record tool result
                await self.session.add_tool_result(
                    tc.name, tc.id, content, is_error=not result.success
                )
                
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                results.append(LLMToolResult(
                    tool_use_id=tc.id,
                    content=error_msg,
                    is_error=True,
                ))
                await self.session.add_tool_result(
                    tc.name, tc.id, error_msg, is_error=True
                )
        
        return results
    
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
    def dashboard(self) -> Optional[dict]:
        """Get the current dashboard state."""
        return self._dashboard_state


