"""Tests for database migration utilities."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.storage.migrations import (
    check_migration_needed,
    migrate_from_json,
    migrate_remove_gamification_v3,
)


@pytest_asyncio.fixture
async def test_db():
    """Create a temporary database for migration tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path)
    await db.connect()

    yield db

    await db.close()
    db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_migrate_from_json_skips_when_file_missing(test_db, tmp_path):
    result = await migrate_from_json(
        test_db, progress_json_path=tmp_path / "missing.json"
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "progress.json not found"


@pytest.mark.asyncio
async def test_migrate_from_json_returns_error_for_invalid_json(test_db, tmp_path):
    progress_file = tmp_path / "progress.json"
    progress_file.write_text("{ this is invalid json")

    result = await migrate_from_json(test_db, progress_json_path=progress_file)

    assert result["status"] == "error"
    assert "Invalid JSON:" in result["reason"]


@pytest.mark.asyncio
async def test_migrate_from_json_migrates_profile_patterns_and_quests(
    test_db, tmp_path
):
    progress_file = tmp_path / "progress.json"
    progress_file.write_text(
        """
{
  "profile": {
    "name": "Migrated User",
    "created_at": "2026-01-01T10:00:00"
  },
  "pattern_confidence": {
    "sliding_window": 70,
    "two_pointers": 40
  },
  "completed_quests": {
    "two_sum": {
      "pattern": "hash_map",
      "completed_at": "2026-01-02T10:00:00",
      "hints_used": 1,
      "review_count": 2
    },
    "valid_parentheses": {
      "pattern": "stack",
      "completed_at": "2026-01-03T10:00:00",
      "hints_used": 0
    }
  }
}
""".strip()
    )

    result = await migrate_from_json(test_db, progress_json_path=progress_file)

    assert result["status"] == "success"
    assert result["profile_migrated"] is True
    assert result["patterns_migrated"] == 2
    assert result["quests_migrated"] == 2

    profile = await test_db.get_or_create_profile("default")
    assert profile.name == "Migrated User"
    assert profile.quests_completed == 2

    sw = await test_db.get_pattern_progress("default", "sliding_window")
    tp = await test_db.get_pattern_progress("default", "two_pointers")
    assert sw is not None and sw.progress == 70
    assert tp is not None and tp.progress == 40

    two_sum = await test_db.get_quest_completion("default", "two_sum")
    valid_parentheses = await test_db.get_quest_completion(
        "default", "valid_parentheses"
    )
    assert two_sum is not None and two_sum.pattern_id == "hash_map"
    assert valid_parentheses is not None and valid_parentheses.pattern_id == "stack"


@pytest.mark.asyncio
async def test_check_migration_needed_false_when_no_file(test_db, tmp_path):
    needed = await check_migration_needed(
        test_db, progress_json_path=tmp_path / "missing.json"
    )
    assert needed is False


@pytest.mark.asyncio
async def test_check_migration_needed_true_when_json_has_more_quests(test_db, tmp_path):
    profile = await test_db.get_or_create_profile("default")
    profile.quests_completed = 1
    await test_db.update_profile(profile)

    progress_file = tmp_path / "progress.json"
    progress_file.write_text(
        """
{
  "completed_quests": {
    "a": {"pattern": "x"},
    "b": {"pattern": "y"}
  }
}
""".strip()
    )

    needed = await check_migration_needed(test_db, progress_json_path=progress_file)
    assert needed is True


@pytest.mark.asyncio
async def test_check_migration_needed_true_with_empty_db_and_json_data(
    test_db, tmp_path
):
    progress_file = tmp_path / "progress.json"
    progress_file.write_text(
        """
{
  "profile": {"name": "New User"},
  "completed_quests": {}
}
""".strip()
    )

    needed = await check_migration_needed(test_db, progress_json_path=progress_file)
    assert needed is True


@pytest.mark.asyncio
async def test_check_migration_needed_false_on_json_parse_error_with_existing_data(
    test_db, tmp_path
):
    profile = await test_db.get_or_create_profile("default")
    profile.quests_completed = 2
    await test_db.update_profile(profile)

    progress_file = tmp_path / "progress.json"
    progress_file.write_text("not valid json")

    needed = await check_migration_needed(test_db, progress_json_path=progress_file)
    assert needed is False


@pytest.mark.asyncio
async def test_migrate_remove_gamification_v3_preserves_core_tables(test_db):
    profile = await test_db.get_or_create_profile("default")
    profile.name = "Before Migration"
    profile.quests_completed = 3
    await test_db.update_profile(profile)

    await test_db.conn.execute(
        """
        INSERT INTO quest_completions (
            id, user_id, quest_id, pattern_id, completed_at, hints_used, success, review_count, next_review_in
        ) VALUES (?, ?, ?, ?, datetime('now'), 0, 1, 0, 1)
        """,
        ("default_q1", "default", "q1", "arrays"),
    )
    await test_db.conn.commit()

    result = await migrate_remove_gamification_v3(test_db)

    assert result["status"] == "success"
    assert result["migration"] == "remove_gamification_v3"

    migrated_profile = await test_db.get_or_create_profile("default")
    assert migrated_profile.name == "Before Migration"
    assert migrated_profile.quests_completed == 3

    completion = await test_db.get_quest_completion("default", "q1")
    assert completion is not None
    assert completion.pattern_id == "arrays"

    async with test_db.conn.execute("PRAGMA index_list('quest_completions')") as cursor:
        indexes = [row["name"] async for row in cursor]

    assert "idx_quest_completions_user" in indexes
    assert "idx_quest_completions_pattern" in indexes
