"""Tests for quest tools."""

import pytest
import pytest_asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

from dsa_coach.storage.db import Database
from dsa_coach.tools.quests import (
    get_quests_for_pattern,
    get_current_quest,
    assign_quest,
    mark_quest_complete,
    get_hint,
)


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


@pytest.mark.asyncio
async def test_get_quests_for_pattern(test_db):
    """Test getting quests for a specific pattern."""
    result = await get_quests_for_pattern(test_db, "sliding_window")
    
    assert result.success
    assert result.data is not None
    
    # All quests should have the correct pattern
    for quest in result.data:
        assert "id" in quest
        assert "title" in quest
        assert "difficulty" in quest


@pytest.mark.asyncio
async def test_get_current_quest_none(test_db):
    """Test getting current quest when none assigned."""
    result = await get_current_quest(test_db)
    
    assert result.success
    assert result.data is None


@pytest.mark.asyncio
async def test_assign_quest(test_db):
    """Test assigning a quest."""
    # Don't open browser in tests
    with patch("webbrowser.open"):
        result = await assign_quest(
            test_db, 
            "two_sum", 
            open_browser=False,
        )
    
    assert result.success
    assert result.data is not None
    assert result.data["quest_id"] == "two_sum"
    assert "solution_file" in result.data


@pytest.mark.asyncio
async def test_assign_quest_not_found(test_db):
    """Test assigning non-existent quest."""
    result = await assign_quest(test_db, "nonexistent_quest", open_browser=False)
    
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_mark_quest_complete_no_current(test_db):
    """Test marking complete when no quest assigned."""
    result = await mark_quest_complete(test_db)
    
    assert not result.success
    assert "No quest" in result.error


@pytest.mark.asyncio
async def test_mark_quest_complete_flow(test_db):
    """Test the full assign -> complete flow."""
    # Assign a quest
    with patch("webbrowser.open"):
        await assign_quest(test_db, "two_sum", open_browser=False)
    
    # Mark complete
    result = await mark_quest_complete(test_db, success=True, hints_used=0)
    
    assert result.success
    assert result.data is not None
    assert result.data["xp_earned"] > 0
    assert result.data["pattern"] == "hash_map"


@pytest.mark.asyncio
async def test_get_hint_no_current(test_db):
    """Test getting hint when no quest assigned."""
    result = await get_hint(test_db)
    
    assert not result.success
    assert "No quest" in result.error


@pytest.mark.asyncio
async def test_get_hint_with_quest(test_db):
    """Test getting hint for assigned quest."""
    # Assign a quest
    with patch("webbrowser.open"):
        await assign_quest(test_db, "two_sum", open_browser=False)
    
    # Get hint
    result = await get_hint(test_db, level="low")
    
    assert result.success
    assert result.data is not None
    assert "hint" in result.data
    assert result.data["level"] == "low"

