"""Tests for quest tools."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.tools.quests import (
    assign_quest,
    get_current_quest,
    get_hint,
    get_quests_for_pattern,
    mark_quest_complete,
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
        assert "problem_id" in quest or "id" in quest
        assert "problem_name" in quest or "title" in quest
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
    # Use a real quest ID (arrays_hashing_two_sum - Arrays & Hashing, Two Sum problem)
    with patch("webbrowser.open"):
        result = await assign_quest(
            test_db,
            "arrays_hashing_two_sum",
            open_browser=False,
        )

    assert result.success
    assert result.data is not None
    assert result.data["quest_id"] == "arrays_hashing_two_sum"
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
    # Assign a quest (arrays_hashing_two_sum is from Arrays & Hashing pattern)
    with patch("webbrowser.open"):
        await assign_quest(test_db, "arrays_hashing_two_sum", open_browser=False)

    # Mark complete
    result = await mark_quest_complete(test_db, success=True, hints_used=0)

    assert result.success
    assert result.data is not None
    # V2 removed XP system, just check it has pattern info
    assert "pattern" in result.data or "pattern_id" in result.data


@pytest.mark.asyncio
async def test_get_hint_no_current(test_db):
    """Test getting hint when no quest assigned."""
    result = await get_hint(test_db)

    assert not result.success
    assert "No quest" in result.error
