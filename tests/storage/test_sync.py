"""Regression tests for synchronous DB wrapper used by dashboard/UI code."""

from __future__ import annotations

from datetime import datetime

from dsa_coach.storage.models import PatternProgress, QuestCompletion
from dsa_coach.storage.sync import SyncDatabase


def test_sync_database_profile_session_and_pattern_roundtrip(tmp_path):
    db_path = tmp_path / "sync_roundtrip.db"

    with SyncDatabase(db_path) as db:
        profile = db.get_or_create_profile("u1")
        assert profile.id == "u1"

        profile.name = "Regression User"
        profile.quests_completed = 7
        db.update_profile(profile)

        updated = db.get_or_create_profile("u1")
        assert updated.name == "Regression User"
        assert updated.quests_completed == 7

        session = db.create_session(
            user_id="u1",
            session_type="practice",
            current_pattern="arrays_hashing",
            current_quest="arrays_hashing_two_sum",
        )
        latest = db.get_latest_session("u1")
        assert latest is not None
        assert latest.id == session.id
        assert latest.current_quest == "arrays_hashing_two_sum"

        pattern = PatternProgress(
            id="u1_arrays_hashing",
            user_id="u1",
            pattern_id="arrays_hashing",
            progress=35,
            quests_completed=2,
            quests_total=6,
        )
        db.upsert_pattern_progress(pattern)

        stored = db.get_pattern_progress("u1", "arrays_hashing")
        assert stored is not None
        assert stored.progress == 35
        assert stored.quests_completed == 2


def test_sync_database_derived_stats_reviews_and_weekly_activity(tmp_path):
    db_path = tmp_path / "sync_stats.db"

    with SyncDatabase(db_path) as db:
        completion = QuestCompletion(
            id="u2_q1",
            user_id="u2",
            quest_id="q1",
            pattern_id="arrays_hashing",
            completed_at=datetime.now(),
            hints_used=0,
            success=True,
        )
        db.upsert_quest_completion(completion)

        fetched = db.get_quest_completion("u2", "q1")
        assert fetched is not None
        assert fetched.pattern_id == "arrays_hashing"

        completed = db.get_completed_quests("u2", "arrays_hashing")
        assert len(completed) == 1

        derived = db.get_derived_pattern_stats("u2", "arrays_hashing", quests_total=2)
        assert derived["quests_completed"] == 1
        assert derived["progress"] == 50

        assert db.get_total_quests_completed("u2") == 1

        db.upsert_daily_log(
            user_id="u2",
            problems_delta=1,
            time_delta_mins=25,
            hints_delta=0,
            pattern_worked="arrays_hashing",
        )
        weekly = db.get_weekly_activity("u2")
        assert weekly["sessions"] >= 1
        assert weekly["problems_solved"] >= 1
        assert "arrays_hashing" in weekly["patterns"]


def test_sync_database_teaching_and_mistake_tracking(tmp_path):
    db_path = tmp_path / "sync_teaching.db"

    with SyncDatabase(db_path) as db:
        db.record_teaching(
            user_id="u3",
            pattern_id="graphs",
            concept="bfs",
            student_response="confused",
        )
        db.record_teaching(
            user_id="u3",
            pattern_id="graphs",
            concept="bfs",
            student_response="understood",
        )

        history = db.get_teaching_history("u3", "graphs")
        assert len(history) == 1
        assert history[0]["concept"] == "bfs"
        assert history[0]["explanation_count"] == 2

        db.add_mistake(
            user_id="u3",
            quest_id="qg1",
            pattern_id="graphs",
            mistake_type="edge_case",
            description="missed empty graph",
        )
        recent = db.get_recent_mistakes("u3", limit=5)
        assert len(recent) >= 1
        assert recent[0]["pattern_id"] == "graphs"
