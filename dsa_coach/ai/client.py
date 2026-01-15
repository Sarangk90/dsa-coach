"""LLM client abstraction for AI mentorship.

Supports both synchronous and async calls, with tool calling for agent mode.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try to import API clients
OPENAI_AVAILABLE = False
ANTHROPIC_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PREFERRED_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # or "openai"

# Model settings
OPENAI_MODEL = "gpt-4o"
ANTHROPIC_MODEL = "claude-sonnet-4-5"  # Claude 3.5 Sonnet (latest)


@dataclass
class ToolCall:
    """Represents a tool call request from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool call."""

    tool_use_id: str
    content: str
    is_error: bool = False


@dataclass
class LLMResponse:
    """Response from an LLM, which may include tool calls."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    raw_response: Any = None
    # Token usage from API response
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def has_tool_calls(self) -> bool:
        """Check if response includes tool calls."""
        return len(self.tool_calls) > 0


@dataclass
class TokenUsage:
    """Track token usage for a single LLM call.

    Shows how much of the context window was used in the most recent call.
    The context window limit (200k for Claude, 128k for GPT-4o) applies
    per-call, not cumulatively.

    Attributes:
        input_tokens: Input tokens (prompt) for this call
        output_tokens: Output tokens (response) for this call
        cache_read_tokens: Tokens read from Anthropic prompt cache
        cache_creation_tokens: Tokens written to Anthropic prompt cache
        context_limit: Maximum context window for the model
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    context_limit: int = 200_000  # Default to Claude Sonnet

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed in this call (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def percentage_used(self) -> float:
        """Percentage of context window consumed by this call."""
        if self.context_limit == 0:
            return 0.0
        # Context window is primarily about input tokens (the prompt)
        # but we show total for visibility
        return (self.input_tokens / self.context_limit) * 100

    @property
    def is_warning_threshold(self) -> bool:
        """Check if usage is at or above 75% warning threshold."""
        return self.percentage_used >= 75.0

    def set_from_response(self, response: LLMResponse) -> None:
        """Set token usage from an LLM response (replaces, does not accumulate).

        Args:
            response: The LLM response containing token usage data
        """
        self.input_tokens = response.input_tokens
        self.output_tokens = response.output_tokens
        self.cache_read_tokens = response.cache_read_tokens
        self.cache_creation_tokens = response.cache_creation_tokens

    def format_display(self) -> str:
        """Format token usage for terminal display.

        Returns:
            Formatted string like "15,234/200,000 (7.6%)"
        """
        return f"{self.input_tokens:,}/{self.context_limit:,} ({self.percentage_used:.1f}%)"


def check_ai_available() -> tuple[bool, str]:
    """Check if AI features are available.

    Returns:
        Tuple of (is_available, message)
    """
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        return True, "Anthropic API available"
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        return True, "OpenAI API available"

    return (
        False,
        "No LLM provider available. Please:\n"
        "1. pip install openai anthropic python-dotenv\n"
        "2. Create .env file with OPENAI_API_KEY or ANTHROPIC_API_KEY",
    )


def call_openai(messages: list[dict], max_tokens: int = 1000) -> str:
    """Call OpenAI API.

    Args:
        messages: List of message dicts with role and content
        max_tokens: Maximum tokens in response

    Returns:
        Response text

    Raises:
        RuntimeError: If OpenAI is not available
    """
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        raise RuntimeError(
            "OpenAI not available. Install openai and set OPENAI_API_KEY."
        )

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=OPENAI_MODEL, messages=messages, max_tokens=max_tokens, temperature=0.7
    )

    return response.choices[0].message.content


def call_anthropic(messages: list[dict], system: str, max_tokens: int = 1000) -> str:
    """Call Anthropic API.

    Args:
        messages: List of message dicts (user/assistant only)
        system: System prompt
        max_tokens: Maximum tokens in response

    Returns:
        Response text

    Raises:
        RuntimeError: If Anthropic is not available
    """
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "Anthropic not available. Install anthropic and set ANTHROPIC_API_KEY."
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=ANTHROPIC_MODEL, max_tokens=max_tokens, system=system, messages=messages
    )

    return response.content[0].text


def get_ai_response(
    user_message: str,
    system_prompt: str,
    max_tokens: int = 1000,
    conversation_history: list[dict] | None = None,
) -> str:
    """Get AI response from configured LLM provider.

    Args:
        user_message: User's message
        system_prompt: System prompt for context
        max_tokens: Maximum tokens in response
        conversation_history: Optional previous messages for context

    Returns:
        AI response text

    Raises:
        RuntimeError: If no LLM provider is available
    """
    # Build messages list
    if conversation_history:
        messages = conversation_history + [{"role": "user", "content": user_message}]
    else:
        messages = [{"role": "user", "content": user_message}]

    # Try preferred provider first
    if PREFERRED_PROVIDER == "anthropic" and ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        return call_anthropic(
            messages=messages, system=system_prompt, max_tokens=max_tokens
        )
    if PREFERRED_PROVIDER == "openai" and OPENAI_AVAILABLE and OPENAI_API_KEY:
        # OpenAI needs system message in messages list
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        return call_openai(messages=openai_messages, max_tokens=max_tokens)

    # Fallback to whichever is available
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        return call_anthropic(
            messages=messages, system=system_prompt, max_tokens=max_tokens
        )
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        return call_openai(messages=openai_messages, max_tokens=max_tokens)

    raise RuntimeError(
        "No LLM provider available. Please:\n"
        "1. pip install openai anthropic python-dotenv\n"
        "2. Create .env file with OPENAI_API_KEY or ANTHROPIC_API_KEY"
    )


# ==================== Async API with Tool Calling ====================


async def call_anthropic_with_tools(
    messages: list[dict],
    system: str,
    tools: list[dict],
    max_tokens: int = 4096,
) -> LLMResponse:
    """
    Call Anthropic API with tool calling support.

    Args:
        messages: List of message dicts (user/assistant only)
        system: System prompt
        tools: List of tool definitions in Anthropic format
        max_tokens: Maximum tokens in response

    Returns:
        LLMResponse with content and/or tool calls
    """
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "Anthropic not available. Install anthropic and set ANTHROPIC_API_KEY."
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build request kwargs
    kwargs = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }

    if tools:
        kwargs["tools"] = tools

    response = client.messages.create(**kwargs)

    # Extract token usage from response
    usage = response.usage
    input_tokens = usage.input_tokens if usage else 0
    output_tokens = usage.output_tokens if usage else 0
    # Cache tokens are optional attributes (may not exist on older API versions)
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0 if usage else 0
    cache_creation = (
        getattr(usage, "cache_creation_input_tokens", 0) or 0 if usage else 0
    )

    # Parse response
    content = ""
    tool_calls = []

    for block in response.content:
        if block.type == "text":
            content += block.text
        elif block.type == "tool_use":
            tool_calls.append(
                ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                )
            )

    return LLMResponse(
        content=content,
        tool_calls=tool_calls,
        stop_reason=response.stop_reason,
        raw_response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_creation,
    )


async def call_openai_with_tools(
    messages: list[dict],
    tools: list[dict],
    max_tokens: int = 4096,
) -> LLMResponse:
    """
    Call OpenAI API with tool calling support.

    Args:
        messages: List of message dicts (including system)
        tools: List of tool definitions in OpenAI format
        max_tokens: Maximum tokens in response

    Returns:
        LLMResponse with content and/or tool calls
    """
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        raise RuntimeError(
            "OpenAI not available. Install openai and set OPENAI_API_KEY."
        )

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    kwargs = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    if tools:
        kwargs["tools"] = tools

    response = client.chat.completions.create(**kwargs)

    # Extract token usage from response
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    # OpenAI doesn't have prompt caching like Anthropic
    cache_read = 0
    cache_creation = 0

    # Parse response
    message = response.choices[0].message
    content = message.content or ""
    tool_calls = []

    if message.tool_calls:
        for tc in message.tool_calls:
            tool_calls.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
            )

    return LLMResponse(
        content=content,
        tool_calls=tool_calls,
        stop_reason=response.choices[0].finish_reason,
        raw_response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_creation,
    )


async def get_ai_response_with_tools(
    messages: list[dict],
    system_prompt: str,
    tools: list[dict],
    max_tokens: int = 4096,
) -> LLMResponse:
    """
    Get AI response with tool calling support.

    Args:
        messages: Conversation messages
        system_prompt: System prompt for context
        tools: List of tool definitions (will be converted to provider format)
        max_tokens: Maximum tokens in response

    Returns:
        LLMResponse with content and/or tool calls
    """
    # Try preferred provider first
    if PREFERRED_PROVIDER == "anthropic" and ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        return await call_anthropic_with_tools(
            messages=messages,
            system=system_prompt,
            tools=tools,
            max_tokens=max_tokens,
        )
    if PREFERRED_PROVIDER == "openai" and OPENAI_AVAILABLE and OPENAI_API_KEY:
        # OpenAI needs system message in messages list
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        # Convert tools to OpenAI format
        openai_tools = _convert_tools_to_openai(tools)
        return await call_openai_with_tools(
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=max_tokens,
        )

    # Fallback to whichever is available
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        return await call_anthropic_with_tools(
            messages=messages,
            system=system_prompt,
            tools=tools,
            max_tokens=max_tokens,
        )
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        openai_tools = _convert_tools_to_openai(tools)
        return await call_openai_with_tools(
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=max_tokens,
        )

    raise RuntimeError(
        "No LLM provider available. Please:\n"
        "1. pip install openai anthropic python-dotenv\n"
        "2. Create .env file with OPENAI_API_KEY or ANTHROPIC_API_KEY"
    )


def _convert_tools_to_openai(anthropic_tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool format to OpenAI function calling format."""
    openai_tools = []
    for tool in anthropic_tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get(
                        "input_schema", {"type": "object", "properties": {}}
                    ),
                },
            }
        )
    return openai_tools


def format_tool_result_for_anthropic(tool_results: list[ToolResult]) -> list[dict]:
    """Format tool results for Anthropic API."""
    content = []
    for result in tool_results:
        content.append(
            {
                "type": "tool_result",
                "tool_use_id": result.tool_use_id,
                "content": result.content,
                "is_error": result.is_error,
            }
        )
    return content


def format_tool_result_for_openai(tool_results: list[ToolResult]) -> list[dict]:
    """Format tool results for OpenAI API."""
    messages = []
    for result in tool_results:
        messages.append(
            {
                "role": "tool",
                "tool_call_id": result.tool_use_id,
                "content": result.content,
            }
        )
    return messages
