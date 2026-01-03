"""Tests for CoachAgent."""

import pytest
import pytest_asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from dsa_coach.storage.db import Database
from dsa_coach.agent.agent import CoachAgent, AgentResponse
from dsa_coach.ai.client import LLMResponse, ToolCall


@pytest_asyncio.fixture
async def test_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    db = Database(db_path)
    await db.connect()
    
    yield db
    
    await db.close()
    db_path.unlink(missing_ok=True)


@pytest_asyncio.fixture
async def agent(test_db):
    """Create a CoachAgent for testing."""
    agent = CoachAgent(test_db)
    await agent.initialize()
    return agent


@pytest.mark.asyncio
async def test_agent_initialization(test_db):
    """Test agent initializes correctly."""
    agent = CoachAgent(test_db)
    await agent.initialize()
    
    assert agent.session.session is not None
    assert agent.tools is not None


@pytest.mark.asyncio
async def test_get_greeting_new_user(agent):
    """Test greeting for a new user."""
    greeting = await agent.get_greeting()
    
    assert greeting is not None
    assert len(greeting) > 0


@pytest.mark.asyncio
async def test_get_system_prompt(agent):
    """Test system prompt generation."""
    prompt = agent.get_system_prompt()
    
    assert "DSA Coach" in prompt
    assert "tools" in prompt.lower()


@pytest.mark.asyncio
async def test_get_tools_for_llm(agent):
    """Test tool definitions for LLM."""
    tools = agent.get_tools_for_llm()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    
    # Check tool structure
    for tool in tools:
        assert "name" in tool
        assert "description" in tool


@pytest.mark.asyncio
async def test_run_with_mocked_llm(agent):
    """Test running agent with mocked LLM response."""
    mock_response = LLMResponse(
        content="Hello! How can I help you today?",
        tool_calls=[],
        stop_reason="end_turn",
    )
    
    with patch(
        "dsa_coach.agent.agent.get_ai_response_with_tools",
        new=AsyncMock(return_value=mock_response),
    ):
        response = await agent.run("Hello!")
    
    assert isinstance(response, AgentResponse)
    assert response.content == "Hello! How can I help you today?"
    assert len(response.tool_calls_made) == 0


@pytest.mark.asyncio
async def test_run_with_tool_call(agent):
    """Test running agent with tool calls."""
    # First response has a tool call
    tool_call_response = LLMResponse(
        content="",
        tool_calls=[
            ToolCall(
                id="call_123",
                name="list_patterns",
                arguments={},
            )
        ],
        stop_reason="tool_use",
    )
    
    # Second response after tool execution
    final_response = LLMResponse(
        content="Here are the available patterns...",
        tool_calls=[],
        stop_reason="end_turn",
    )
    
    # Mock the LLM to return tool call first, then final response
    mock_llm = AsyncMock(side_effect=[tool_call_response, final_response])
    
    with patch(
        "dsa_coach.agent.agent.get_ai_response_with_tools",
        new=mock_llm,
    ):
        response = await agent.run("What patterns are available?")
    
    assert isinstance(response, AgentResponse)
    assert len(response.tool_calls_made) == 1
    assert response.tool_calls_made[0]["name"] == "list_patterns"


@pytest.mark.asyncio
async def test_dashboard_property(agent):
    """Test dashboard state is available."""
    # Dashboard should be populated after initialization
    assert agent.dashboard is not None
    assert "profile" in agent.dashboard

