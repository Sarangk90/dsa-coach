"""Tests for teaching tools."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.tools.teaching import record_mistake


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
async def test_record_mistake_defaults_type(test_db):
    """Record mistake without explicit type defaults to 'other'."""
    result = await record_mistake(
        test_db,
        quest_id="ft_04_c1_p1",
        pattern_id="ft_04",
        description="Missed the shrinking window condition.",
    )

    assert result.success
    assert result.data is not None
    assert result.data["mistake_type"] == "other"
