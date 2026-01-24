"""Tests for complete_quest idempotency.

These tests ensure that completing the same quest multiple times
does not inflate progress counters or progress scores.
"""

from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.storage.models import QuestCompletion
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
    first_progress = pattern_after_first.progress

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

    assert pattern_after_second.progress == first_progress, (
        f"Pattern progress increased from {first_progress} "
        f"to {pattern_after_second.progress} on re-completion!"
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
        "arrays_hashing_top_k_frequent_elements",
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
            hints_used=0,  # +15 progress each
            user_id=user_id,
        )

    # Get actual records
    completions = await test_db.get_completed_quests(user_id, pattern_id)
    actual_count = len(completions)

    # Get derived stats (with quests_total for scaled progress)
    # arrays_hashing has 6 quests
    quests_total = 6
    derived = await test_db.get_derived_pattern_stats(
        user_id, pattern_id, quests_total=quests_total
    )

    # Derived quests_completed should match actual records
    assert derived["quests_completed"] == actual_count, (
        f"Derived quests_completed ({derived['quests_completed']}) != "
        f"actual records ({actual_count})"
    )

    # Confidence uses scaled formula: (earned_points / max_points) * 100
    # 3 quests * 15 points = 45 earned, max = 6 * 15 = 90
    # (45 / 90) * 100 = 50
    expected_progress = round((actual_count * 15 / (quests_total * 15)) * 100)
    assert derived["progress"] == expected_progress, (
        f"Derived progress ({derived['progress']}) != expected ({expected_progress})"
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
async def test_progress_with_hints_calculates_correctly(test_db: Database):
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

    # Get derived stats (pass quests_total for scaled progress calculation)
    # arrays_hashing has 6 quests, max_points = 6 * 15 = 90
    quests_total = 6
    derived = await test_db.get_derived_pattern_stats(
        user_id, pattern_id, quests_total=quests_total
    )

    # Earned points: 15 (no hints) + 10 (with hints) = 25
    # Confidence formula: round((25 / 90) * 100) = 28
    expected_progress = 28
    assert derived["progress"] == expected_progress, (
        f"Expected progress {expected_progress}, got {derived['progress']}"
    )


@pytest.mark.asyncio
async def test_progress_scales_with_pattern_size(test_db: Database):
    """Confidence should scale proportionally to pattern size.

    Small patterns (1 problem) can reach 100%.
    Large patterns require proportional completions.
    """
    user_id = "test_user"
    pattern_id = "test_pattern"

    # Simulate a small pattern with 1 problem
    # Completing it with no hints should give 100%
    completion = QuestCompletion(
        id=f"{user_id}_test_quest_1",
        user_id=user_id,
        quest_id="test_quest_1",
        pattern_id=pattern_id,
        completed_at=datetime.now(),
        time_minutes=30,
        hints_used=0,
        success=True,
    )
    await test_db.upsert_quest_completion(completion)

    # Small pattern (1 quest): 15 earned / 15 max = 100%
    derived_small = await test_db.get_derived_pattern_stats(
        user_id, pattern_id, quests_total=1
    )
    assert derived_small["progress"] == 100, (
        f"Small pattern (1 quest) should reach 100%, got {derived_small['progress']}"
    )
    assert derived_small["mastered"] is True

    # Same earned points, but larger pattern (10 quests): 15 / 150 = 10%
    derived_large = await test_db.get_derived_pattern_stats(
        user_id, pattern_id, quests_total=10
    )
    assert derived_large["progress"] == 10, (
        f"Large pattern (10 quests) should be 10%, got {derived_large['progress']}"
    )
    assert derived_large["mastered"] is False


@pytest.mark.asyncio
async def test_progress_caps_at_100_percent(test_db: Database):
    """Confidence should never exceed 100% even with extra completions."""
    user_id = "test_user"
    pattern_id = "overflow_pattern"

    # Complete 3 quests in a pattern with only 2 quests
    for i in range(3):
        completion = QuestCompletion(
            id=f"{user_id}_overflow_quest_{i}",
            user_id=user_id,
            quest_id=f"overflow_quest_{i}",
            pattern_id=pattern_id,
            completed_at=datetime.now(),
            time_minutes=30,
            hints_used=0,
            success=True,
        )
        await test_db.upsert_quest_completion(completion)

    # 45 earned points / 30 max points = 150% -> capped at 100%
    derived = await test_db.get_derived_pattern_stats(
        user_id, pattern_id, quests_total=2
    )
    assert derived["progress"] == 100, (
        f"Confidence should cap at 100%, got {derived['progress']}"
    )
