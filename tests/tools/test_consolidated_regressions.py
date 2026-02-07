"""High-value regression tests for consolidated workflow tools."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.storage.models import PatternProgress, QuestCompletion
from dsa_coach.tools import progress_review as progress_review_mod
from dsa_coach.tools import session_quest as session_quest_mod
from dsa_coach.tools.consolidated import (
    get_hint,
    get_teaching_context,
    manage_solution,
    record_learning,
    record_review,
    start_quest,
)
from dsa_coach.tools.quest_helpers import _get_all_quests_for_pattern


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    """Create a fresh test database."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_start_quest_updates_existing_session_instead_of_creating_new(
    test_db: Database,
):
    user_id = "test_user"
    existing = await test_db.create_session(user_id=user_id, session_type="general")

    result = await start_quest(
        db=test_db,
        quest_id="arrays_hashing_two_sum",
        open_browser=False,
        user_id=user_id,
    )

    assert result.success
    latest = await test_db.get_latest_session(user_id)
    assert latest is not None
    assert latest.id == existing.id
    assert latest.current_quest == result.data["quest_id"]
    assert latest.current_pattern == result.data["pattern_id"]


@pytest.mark.asyncio
async def test_start_quest_pattern_mode_reports_all_completed(test_db: Database):
    user_id = "test_user"
    pattern_id = "arrays_hashing"
    all_quests = _get_all_quests_for_pattern(pattern_id)
    assert all_quests, "Expected seeded curriculum to include arrays_hashing quests"

    for quest in all_quests:
        completion = QuestCompletion(
            id=f"{user_id}_{quest['id']}",
            user_id=user_id,
            quest_id=quest["id"],
            pattern_id=pattern_id,
            completed_at=datetime.now(),
            success=True,
        )
        await test_db.upsert_quest_completion(completion)

    result = await start_quest(
        db=test_db,
        pattern_id=pattern_id,
        open_browser=False,
        user_id=user_id,
    )

    assert result.success
    assert result.data is None
    assert "All quests for pattern 'arrays_hashing' are completed" in result.message


@pytest.mark.asyncio
async def test_get_hint_auto_uses_progress_and_missing_level_falls_back(
    test_db: Database,
    monkeypatch,
):
    user_id = "test_user"
    await test_db.create_session(
        user_id=user_id,
        session_type="practice",
        current_quest="mock_quest_with_hints",
        current_pattern="arrays_hashing",
    )

    # Use deterministic hint payload independent of curriculum content.
    monkeypatch_quest = {
        "id": "mock_quest_with_hints",
        "pattern": "arrays_hashing",
        "hints": {
            "low": "Start with brute force.",
            "medium": "Try a hash map.",
            "high": "Use one-pass hash map.",
        },
    }

    def fake_find_quest(_quest_id: str, _mode: str = "fast_track") -> dict | None:
        return monkeypatch_quest

    monkeypatch.setattr(session_quest_mod, "_find_quest", fake_find_quest)

    await test_db.upsert_pattern_progress(
        PatternProgress(
            id=f"{user_id}_arrays_hashing",
            user_id=user_id,
            pattern_id="arrays_hashing",
            progress=80,
            quests_total=6,
        )
    )

    auto = await get_hint(db=test_db, level="auto", user_id=user_id)
    assert auto.success
    assert auto.data["level"] == "high"

    fallback = await get_hint(db=test_db, level="definitely_missing", user_id=user_id)
    assert fallback.success
    assert fallback.data["level"] in fallback.data["available_levels"]
    assert fallback.data["level"] != "definitely_missing"


@pytest.mark.asyncio
async def test_get_hint_returns_clear_error_when_no_hints_available(test_db: Database):
    user_id = "test_user"
    start = await start_quest(
        db=test_db,
        quest_id="arrays_hashing_two_sum",
        open_browser=False,
        user_id=user_id,
    )
    assert start.success

    result = await get_hint(db=test_db, level="auto", user_id=user_id)
    assert result.success is False
    assert result.error == "No hints available for this quest"


@pytest.mark.asyncio
async def test_record_review_handles_missing_and_spacing_updates(test_db: Database):
    missing = await record_review(db=test_db, quest_id="not_real", user_id="u")
    assert missing.success is False
    assert "not found in completions" in missing.error

    user_id = "test_user"
    quest_id = "arrays_hashing_two_sum"
    await test_db.upsert_quest_completion(
        QuestCompletion(
            id=f"{user_id}_{quest_id}",
            user_id=user_id,
            quest_id=quest_id,
            pattern_id="arrays_hashing",
            completed_at=datetime.now(),
            review_count=0,
            next_review_in=1,
        )
    )

    success_review = await record_review(
        db=test_db,
        quest_id=quest_id,
        success=True,
        user_id=user_id,
    )
    assert success_review.success
    assert success_review.data["review_count"] == 1
    assert success_review.data["next_review_in_days"] == 3

    failed_review = await record_review(
        db=test_db,
        quest_id=quest_id,
        success=False,
        user_id=user_id,
    )
    assert failed_review.success
    assert failed_review.data["review_count"] == 2
    assert failed_review.data["next_review_in_days"] == 1


@pytest.mark.asyncio
async def test_manage_solution_round_trip_and_required_argument_checks(
    test_db: Database, tmp_path: Path, monkeypatch
):
    solutions_dir = tmp_path / "solutions"
    monkeypatch.setattr(
        progress_review_mod, "_get_solutions_dir", lambda: solutions_dir
    )

    listed_empty = await manage_solution(db=test_db, action="list")
    assert listed_empty.success
    assert listed_empty.data == []

    missing_quest = await manage_solution(db=test_db, action="create", quest_id=None)
    assert missing_quest.success is False
    assert "quest_id is required" in missing_quest.error

    template = await manage_solution(
        db=test_db,
        action="template",
        quest_id="arrays_hashing_two_sum",
    )
    assert template.success
    assert template.data["quest_id"] == "arrays_hashing_two_sum"

    created = await manage_solution(
        db=test_db,
        action="create",
        quest_id="arrays_hashing_two_sum",
    )
    assert created.success
    assert created.data["existed"] is False
    created_path = Path(created.data["path"])
    assert created_path.exists()

    created_again = await manage_solution(
        db=test_db,
        action="create",
        quest_id="arrays_hashing_two_sum",
    )
    assert created_again.success
    assert created_again.data["existed"] is True

    read = await manage_solution(
        db=test_db,
        action="read",
        quest_id="arrays_hashing_two_sum",
    )
    assert read.success
    assert "DIVE Protocol" in read.data["content"]
    assert read.data["path"].endswith("arrays_hashing_two_sum.py")

    listed = await manage_solution(db=test_db, action="list")
    assert listed.success
    assert len(listed.data) == 1
    assert listed.data[0]["quest_id"] == "arrays_hashing_two_sum"


@pytest.mark.asyncio
async def test_record_learning_recurrence_and_teaching_advice_paths(test_db: Database):
    user_id = "test_user"
    pattern_id = "arrays_hashing"

    understood_missing_concept = await record_learning(
        db=test_db,
        type="concept_understood",
        pattern_id=pattern_id,
        concept=None,
        user_id=user_id,
    )
    assert understood_missing_concept.success is False
    assert "concept is required" in understood_missing_concept.error

    for i in range(3):
        result = await record_learning(
            db=test_db,
            type="mistake",
            pattern_id=pattern_id,
            quest_id="arrays_hashing_two_sum",
            mistake_type="off_by_one",
            description=f"mistake #{i + 1}",
            user_id=user_id,
        )

    assert result.success
    assert result.data["recurrence_count"] >= 3
    assert result.data["is_recurring"] is True
    assert "occurred" in (result.data["coaching_advice"] or "")

    taught_first = await record_learning(
        db=test_db,
        type="concept_taught",
        pattern_id=pattern_id,
        concept="hash collisions",
        student_response="confused",
        user_id=user_id,
    )
    taught_second = await record_learning(
        db=test_db,
        type="concept_taught",
        pattern_id=pattern_id,
        concept="hash collisions",
        student_response="confused",
        user_id=user_id,
    )

    assert taught_first.success
    assert taught_second.success
    assert taught_second.data["explanation_count"] == 2
    assert "Second explanation" in (taught_second.data["coaching_advice"] or "")

    context = await get_teaching_context(
        db=test_db, pattern_id=pattern_id, user_id=user_id
    )
    assert context.success
    confused = context.data["teaching_history"]["confused"]
    assert any(item["concept"] == "hash collisions" for item in confused)
    assert any(
        "Confused concepts to reteach" in area for area in context.data["focus_areas"]
    )
