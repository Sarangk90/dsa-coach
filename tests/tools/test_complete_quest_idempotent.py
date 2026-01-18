"""Tests for complete_quest idempotency.

These tests ensure that completing the same quest multiple times
does not inflate progress counters or confidence scores.
"""

from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.tools.consolidated import complete_quest, start_quest


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    """Create a fresh test database."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_complete_quest_only_counts_once(test_db: Database):
    """Completing the same quest twice should only increment counters once."""
    user_id = "test_user"

    # Start a quest
    start_result = await start_quest(
        db=test_db,
        quest_id="arrays_hashing_two_sum",
        open_browser=False,
        user_id=user_id,
    )
    assert start_result.success

    # Complete it first time
    first_complete = await complete_quest(
        db=test_db,
        success=True,
        time_minutes=30,
        hints_used=0,
        user_id=user_id,
    )
    assert first_complete.success
    assert first_complete.data.get("already_completed") is None

    # Get the counts after first completion
    profile_after_first = await test_db.get_or_create_profile(user_id)
    pattern_after_first = await test_db.get_pattern_progress(user_id, "arrays_hashing")

    first_quests_completed = profile_after_first.quests_completed
    first_pattern_quests = pattern_after_first.quests_completed
    first_confidence = pattern_after_first.confidence

    # Start the same quest again
    await start_quest(
        db=test_db,
        quest_id="arrays_hashing_two_sum",
        open_browser=False,
        user_id=user_id,
    )

    # Complete it a SECOND time
    second_complete = await complete_quest(
        db=test_db,
        success=True,
        time_minutes=20,
        hints_used=0,
        user_id=user_id,
    )

    # Second completion should succeed but indicate already completed
    assert second_complete.success
    assert second_complete.data.get("already_completed") is True

    # Verify counters DID NOT increment
    profile_after_second = await test_db.get_or_create_profile(user_id)
    pattern_after_second = await test_db.get_pattern_progress(user_id, "arrays_hashing")

    assert profile_after_second.quests_completed == first_quests_completed, (
        f"Profile quests_completed increased from {first_quests_completed} "
        f"to {profile_after_second.quests_completed} on re-completion!"
    )

    assert pattern_after_second.quests_completed == first_pattern_quests, (
        f"Pattern quests_completed increased from {first_pattern_quests} "
        f"to {pattern_after_second.quests_completed} on re-completion!"
    )

    assert pattern_after_second.confidence == first_confidence, (
        f"Pattern confidence increased from {first_confidence} "
        f"to {pattern_after_second.confidence} on re-completion!"
    )


@pytest.mark.asyncio
async def test_complete_quest_requires_active_quest(test_db: Database):
    """Completing without an active quest should fail gracefully."""
    user_id = "test_user"

    # Try to complete without starting a quest
    result = await complete_quest(
        db=test_db,
        success=True,
        time_minutes=30,
        hints_used=0,
        user_id=user_id,
    )

    assert result.success is False
    assert "No quest currently assigned" in result.error


@pytest.mark.asyncio
async def test_quest_completion_records_are_unique(test_db: Database):
    """Only one completion record should exist per quest."""
    user_id = "test_user"

    # Complete the same quest 3 times
    for _ in range(3):
        await start_quest(
            db=test_db,
            quest_id="arrays_hashing_two_sum",
            open_browser=False,
            user_id=user_id,
        )
        await complete_quest(
            db=test_db,
            success=True,
            time_minutes=30,
            hints_used=0,
            user_id=user_id,
        )

    # There should only be ONE completion record
    completions = await test_db.get_completed_quests(user_id, "arrays_hashing")
    two_sum_completions = [
        c for c in completions if c.quest_id == "arrays_hashing_two_sum"
    ]

    assert len(two_sum_completions) == 1, (
        f"Expected 1 completion record, found {len(two_sum_completions)}"
    )


@pytest.mark.asyncio
async def test_derived_stats_match_actual_records(test_db: Database):
    """Derived stats should exactly match the count of actual completion records."""
    user_id = "test_user"
    pattern_id = "arrays_hashing"

    # Complete 3 different quests
    quests = [
        "arrays_hashing_two_sum",
        "arrays_hashing_group_anagrams",
        "arrays_hashing_top_k_frequent",
    ]

    for quest_id in quests:
        await start_quest(
            db=test_db,
            quest_id=quest_id,
            open_browser=False,
            user_id=user_id,
        )
        await complete_quest(
            db=test_db,
            success=True,
            time_minutes=30,
            hints_used=0,  # +15 confidence each
            user_id=user_id,
        )

    # Get actual records
    completions = await test_db.get_completed_quests(user_id, pattern_id)
    actual_count = len(completions)

    # Get derived stats
    derived = await test_db.get_derived_pattern_stats(user_id, pattern_id)

    # Derived quests_completed should match actual records
    assert derived["quests_completed"] == actual_count, (
        f"Derived quests_completed ({derived['quests_completed']}) != "
        f"actual records ({actual_count})"
    )

    # Confidence should be 3 * 15 = 45 (capped at 100)
    expected_confidence = min(100, actual_count * 15)
    assert derived["confidence"] == expected_confidence, (
        f"Derived confidence ({derived['confidence']}) != "
        f"expected ({expected_confidence})"
    )


@pytest.mark.asyncio
async def test_total_quests_completed_matches_records(test_db: Database):
    """Total quests completed should match actual completion records."""
    user_id = "test_user"

    # Complete quests across different patterns
    quests = [
        "arrays_hashing_two_sum",
        "sliding_window_longest_substring",
        "two_pointers_3sum",
    ]

    for quest_id in quests:
        await start_quest(
            db=test_db,
            quest_id=quest_id,
            open_browser=False,
            user_id=user_id,
        )
        await complete_quest(
            db=test_db,
            success=True,
            time_minutes=30,
            hints_used=0,
            user_id=user_id,
        )

    # Get actual records (all patterns)
    all_completions = await test_db.get_completed_quests(user_id)
    actual_total = len(all_completions)

    # Get derived total
    derived_total = await test_db.get_total_quests_completed(user_id)

    assert derived_total == actual_total, (
        f"Derived total ({derived_total}) != actual total ({actual_total})"
    )


@pytest.mark.asyncio
async def test_confidence_with_hints_calculates_correctly(test_db: Database):
    """Confidence calculation should account for hints used."""
    user_id = "test_user"
    pattern_id = "arrays_hashing"

    # Complete with no hints (+15)
    await start_quest(
        db=test_db,
        quest_id="arrays_hashing_two_sum",
        open_browser=False,
        user_id=user_id,
    )
    await complete_quest(
        db=test_db,
        success=True,
        time_minutes=30,
        hints_used=0,
        user_id=user_id,
    )

    # Complete with hints (+10)
    await start_quest(
        db=test_db,
        quest_id="arrays_hashing_group_anagrams",
        open_browser=False,
        user_id=user_id,
    )
    await complete_quest(
        db=test_db,
        success=True,
        time_minutes=30,
        hints_used=2,
        user_id=user_id,
    )

    # Get derived stats
    derived = await test_db.get_derived_pattern_stats(user_id, pattern_id)

    # Should be 15 + 10 = 25
    assert derived["confidence"] == 25, (
        f"Expected confidence 25, got {derived['confidence']}"
    )
