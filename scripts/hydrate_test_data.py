#!/usr/bin/env python3
"""
Test Data Hydration Script for DSA Coach

This script populates the database with realistic test data for testing
various scenarios. Test data is isolated from your real progress by using
a separate user ID.

Features:
1. User Isolation - Test data uses "test" user, real data uses "default"
2. Idempotent - Can be run multiple times safely
3. Consistent - Data relationships are maintained
4. Realistic - Mimics real user behavior patterns
5. Comprehensive - Covers all tables and scenarios

Usage:
    # Hydrate test data (default: user_id="test")
    python scripts/hydrate_test_data.py

    # Reset and re-hydrate test data
    python scripts/hydrate_test_data.py --reset

    # Clear test data only (no hydration)
    python scripts/hydrate_test_data.py --clear-only

    # Use a custom user ID
    python scripts/hydrate_test_data.py --user my_test_user

Note: CLI commands (coach.py) use "default" user by default.
      Test data under "test" user won't interfere with your real progress.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dsa_coach.storage.models import (
    ConceptUnderstanding,
    PatternProgress,
    QuestCompletion,
    UserProfile,
)
from dsa_coach.storage.sync import SyncDatabase

# =============================================================================
# TEST DATA DEFINITIONS
# =============================================================================

# Base timestamp for consistent relative dates
NOW = datetime.now()


def days_ago(n: int) -> datetime:
    """Helper to get datetime N days ago."""
    return NOW - timedelta(days=n)


def hours_ago(n: int) -> datetime:
    """Helper to get datetime N hours ago."""
    return NOW - timedelta(hours=n)


# User Profile
USER_PROFILE = {
    "id": "default",
    "name": "Alex Chen",
    "quests_completed": 12,
    "created_at": days_ago(14),
    "last_active": hours_ago(2),
}

# Pattern Progress - Various stages of mastery
PATTERN_PROGRESS = [
    # Mastered pattern - high progress, all quests done
    {
        "id": "default_arrays_hashing",
        "user_id": "default",
        "pattern_id": "arrays_hashing",
        "progress": 85,
        "quests_completed": 6,
        "quests_total": 6,
        "concepts_understood": [
            "hash_map_fundamentals",
            "collision_handling",
            "two_sum_pattern",
        ],
        "last_practiced": days_ago(3),
        "next_review": days_ago(-4),  # Due in 4 days
        "mastered": True,
    },
    # Strong pattern - good progress, most quests done
    {
        "id": "default_two_pointers",
        "user_id": "default",
        "pattern_id": "two_pointers",
        "progress": 65,
        "quests_completed": 4,
        "quests_total": 5,
        "concepts_understood": ["two_pointer_technique", "opposite_ends"],
        "last_practiced": days_ago(1),
        "next_review": days_ago(-1),  # Due tomorrow
        "mastered": False,
    },
    # Learning pattern - medium progress
    {
        "id": "default_sliding_window",
        "user_id": "default",
        "pattern_id": "sliding_window",
        "progress": 45,
        "quests_completed": 2,
        "quests_total": 4,
        "concepts_understood": ["window_basics"],
        "last_practiced": days_ago(2),
        "next_review": None,
        "mastered": False,
    },
    # Weak pattern - low progress, just started
    {
        "id": "default_binary_search",
        "user_id": "default",
        "pattern_id": "binary_search",
        "progress": 20,
        "quests_completed": 1,
        "quests_total": 5,
        "concepts_understood": [],
        "last_practiced": days_ago(5),
        "next_review": days_ago(2),  # Overdue by 2 days!
        "mastered": False,
    },
    # New pattern - not started
    {
        "id": "default_recursion",
        "user_id": "default",
        "pattern_id": "recursion",
        "progress": 0,
        "quests_completed": 0,
        "quests_total": 4,
        "concepts_understood": [],
        "last_practiced": None,
        "next_review": None,
        "mastered": False,
    },
]

# Quest Completions - Various scenarios
QUEST_COMPLETIONS = [
    # arrays_hashing - All completed (mastered pattern)
    {
        "id": "default_arrays_hashing_two_sum",
        "user_id": "default",
        "quest_id": "arrays_hashing_two_sum",
        "pattern_id": "arrays_hashing",
        "completed_at": days_ago(10),
        "time_minutes": 25,
        "hints_used": 2,
        "success": True,
        "review_count": 2,
        "last_reviewed": days_ago(3),
        "next_review_in": 7,
    },
    {
        "id": "default_arrays_hashing_group_anagrams",
        "user_id": "default",
        "quest_id": "arrays_hashing_group_anagrams",
        "pattern_id": "arrays_hashing",
        "completed_at": days_ago(9),
        "time_minutes": 20,
        "hints_used": 1,
        "success": True,
        "review_count": 1,
        "last_reviewed": days_ago(5),
        "next_review_in": 7,
    },
    {
        "id": "default_arrays_hashing_subarray_sum_equals_k",
        "user_id": "default",
        "quest_id": "arrays_hashing_subarray_sum_equals_k",
        "pattern_id": "arrays_hashing",
        "completed_at": days_ago(8),
        "time_minutes": 30,
        "hints_used": 0,  # No hints - good!
        "success": True,
        "review_count": 1,
        "last_reviewed": days_ago(4),
        "next_review_in": 14,
    },
    # two_pointers - Most completed
    {
        "id": "default_two_pointers_3sum",
        "user_id": "default",
        "quest_id": "two_pointers_3sum",
        "pattern_id": "two_pointers",
        "completed_at": days_ago(6),
        "time_minutes": 35,
        "hints_used": 1,
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 1,  # Due for first review!
    },
    {
        "id": "default_two_pointers_container_with_most_water",
        "user_id": "default",
        "quest_id": "two_pointers_container_with_most_water",
        "pattern_id": "two_pointers",
        "completed_at": days_ago(5),
        "time_minutes": 28,
        "hints_used": 0,
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 1,
    },
    {
        "id": "default_two_pointers_linked_list_cycle",
        "user_id": "default",
        "quest_id": "two_pointers_linked_list_cycle",
        "pattern_id": "two_pointers",
        "completed_at": days_ago(3),
        "time_minutes": 40,
        "hints_used": 2,
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 3,
    },
    {
        "id": "default_two_pointers_find_duplicate_number",
        "user_id": "default",
        "quest_id": "two_pointers_find_duplicate_number",
        "pattern_id": "two_pointers",
        "completed_at": days_ago(1),
        "time_minutes": 22,
        "hints_used": 0,
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 1,
    },
    # sliding_window - Some completed
    {
        "id": "default_sliding_window_longest_substring_without_repeating",
        "user_id": "default",
        "quest_id": "sliding_window_longest_substring_without_repeating",
        "pattern_id": "sliding_window",
        "completed_at": days_ago(4),
        "time_minutes": 45,
        "hints_used": 3,  # Needed help
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 1,
    },
    {
        "id": "default_sliding_window_minimum_window_substring",
        "user_id": "default",
        "quest_id": "sliding_window_minimum_window_substring",
        "pattern_id": "sliding_window",
        "completed_at": days_ago(2),
        "time_minutes": 38,
        "hints_used": 2,
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 1,
    },
    # binary_search - Just one completed (weak pattern)
    {
        "id": "default_binary_search_basic",
        "user_id": "default",
        "quest_id": "binary_search_basic",
        "pattern_id": "binary_search",
        "completed_at": days_ago(7),
        "time_minutes": 50,
        "hints_used": 3,
        "success": True,
        "review_count": 0,
        "last_reviewed": None,
        "next_review_in": 1,  # Overdue!
    },
]

# Daily Logs - Last 7 days of activity
DAILY_LOGS = [
    {
        "date": days_ago(0).strftime("%Y-%m-%d"),
        "problems_solved": 1,
        "time_spent_mins": 35,
        "hints_used": 0,
        "patterns_worked": ["two_pointers"],
    },
    {
        "date": days_ago(1).strftime("%Y-%m-%d"),
        "problems_solved": 2,
        "time_spent_mins": 60,
        "hints_used": 1,
        "patterns_worked": ["two_pointers", "sliding_window"],
    },
    {
        "date": days_ago(2).strftime("%Y-%m-%d"),
        "problems_solved": 1,
        "time_spent_mins": 40,
        "hints_used": 2,
        "patterns_worked": ["sliding_window"],
    },
    {
        "date": days_ago(3).strftime("%Y-%m-%d"),
        "problems_solved": 1,
        "time_spent_mins": 45,
        "hints_used": 1,
        "patterns_worked": ["two_pointers"],
    },
    {
        "date": days_ago(4).strftime("%Y-%m-%d"),
        "problems_solved": 1,
        "time_spent_mins": 50,
        "hints_used": 3,
        "patterns_worked": ["sliding_window"],
    },
    {
        "date": days_ago(5).strftime("%Y-%m-%d"),
        "problems_solved": 2,
        "time_spent_mins": 55,
        "hints_used": 0,
        "patterns_worked": ["two_pointers"],
    },
    {
        "date": days_ago(6).strftime("%Y-%m-%d"),
        "problems_solved": 1,
        "time_spent_mins": 35,
        "hints_used": 1,
        "patterns_worked": ["two_pointers"],
    },
]

# Milestones - Achievements
MILESTONES = [
    {
        "user_id": "default",
        "milestone_type": "pattern_mastered",
        "pattern_id": "arrays_hashing",
        "quest_id": None,
        "description": "Mastered Arrays & Hashing pattern",
        "achieved_at": days_ago(3),
    },
    {
        "user_id": "default",
        "milestone_type": "streak",
        "pattern_id": None,
        "quest_id": None,
        "description": "7-day practice streak",
        "achieved_at": days_ago(1),
    },
    {
        "user_id": "default",
        "milestone_type": "no_hints",
        "pattern_id": "two_pointers",
        "quest_id": "two_pointers_container_with_most_water",
        "description": "Solved Two Pointers problem without hints",
        "achieved_at": days_ago(5),
    },
    {
        "user_id": "default",
        "milestone_type": "first_quest",
        "pattern_id": "arrays_hashing",
        "quest_id": "arrays_hashing_two_sum",
        "description": "Completed first quest",
        "achieved_at": days_ago(10),
    },
]

# Mistakes - For pattern recognition
MISTAKES = [
    {
        "user_id": "default",
        "quest_id": "sliding_window_longest_substring_without_repeating",
        "pattern_id": "sliding_window",
        "mistake_type": "off_by_one",
        "description": "Window boundary was inclusive instead of exclusive",
        "lesson_learned": "Always clarify if boundaries are inclusive or exclusive",
        "logged_at": days_ago(4),
        "recurrence_count": 2,
    },
    {
        "user_id": "default",
        "quest_id": "sliding_window_minimum_window_substring",
        "pattern_id": "sliding_window",
        "mistake_type": "off_by_one",
        "description": "Forgot to handle window size 0 case",
        "lesson_learned": "Check edge case: what if window is empty?",
        "logged_at": days_ago(2),
        "recurrence_count": 2,  # Same mistake type - recurring!
    },
    {
        "user_id": "default",
        "quest_id": "binary_search_basic",
        "pattern_id": "binary_search",
        "mistake_type": "wrong_pattern",
        "description": "Tried linear search instead of binary search",
        "lesson_learned": "When array is sorted, consider binary search first",
        "logged_at": days_ago(7),
        "recurrence_count": 1,
    },
    {
        "user_id": "default",
        "quest_id": "two_pointers_linked_list_cycle",
        "pattern_id": "two_pointers",
        "mistake_type": "edge_case",
        "description": "Didn't handle duplicate elements in array",
        "lesson_learned": "Ask: can input have duplicates? How to handle them?",
        "logged_at": days_ago(3),
        "recurrence_count": 1,
    },
]

# Teaching History - What concepts have been explained
TEACHING_HISTORY = [
    {
        "user_id": "default",
        "pattern_id": "arrays_hashing",
        "concept": "hash_map_fundamentals",
        "explanation_count": 1,
        "last_explained": days_ago(10),
        "student_response": "understood",
    },
    {
        "user_id": "default",
        "pattern_id": "arrays_hashing",
        "concept": "collision_handling",
        "explanation_count": 2,  # Needed re-explanation
        "last_explained": days_ago(8),
        "student_response": "understood",
    },
    {
        "user_id": "default",
        "pattern_id": "sliding_window",
        "concept": "window_basics",
        "explanation_count": 1,
        "last_explained": days_ago(4),
        "student_response": "partially",  # Still learning
    },
    {
        "user_id": "default",
        "pattern_id": "sliding_window",
        "concept": "window_shrink_condition",
        "explanation_count": 3,  # Struggling with this
        "last_explained": days_ago(2),
        "student_response": "confused",
    },
    {
        "user_id": "default",
        "pattern_id": "two_pointers",
        "concept": "two_pointer_technique",
        "explanation_count": 1,
        "last_explained": days_ago(6),
        "student_response": "understood",
    },
]

# Concept Understanding
CONCEPT_UNDERSTANDING = [
    {
        "user_id": "default",
        "pattern_id": "arrays_hashing",
        "concept": "hash_map_fundamentals",
        "understood": True,
        "diagnosed_at": days_ago(10),
        "taught_at": days_ago(10),
    },
    {
        "user_id": "default",
        "pattern_id": "arrays_hashing",
        "concept": "collision_handling",
        "understood": True,
        "diagnosed_at": days_ago(9),
        "taught_at": days_ago(8),
    },
    {
        "user_id": "default",
        "pattern_id": "sliding_window",
        "concept": "window_basics",
        "understood": True,
        "diagnosed_at": days_ago(4),
        "taught_at": days_ago(4),
    },
    {
        "user_id": "default",
        "pattern_id": "sliding_window",
        "concept": "window_shrink_condition",
        "understood": False,  # Still struggling
        "diagnosed_at": days_ago(4),
        "taught_at": days_ago(2),
    },
    {
        "user_id": "default",
        "pattern_id": "two_pointers",
        "concept": "two_pointer_technique",
        "understood": True,
        "diagnosed_at": days_ago(6),
        "taught_at": days_ago(6),
    },
]


# =============================================================================
# HYDRATION FUNCTIONS
# =============================================================================


def reset_database() -> None:
    """Clear all data from the database using direct SQL."""
    print("🗑️  Resetting database...")

    import sqlite3

    from dsa_coach.paths import BASE_DIR

    db_path = BASE_DIR / "coach.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete in order to respect foreign key constraints
    tables = [
        "messages",
        "teaching_history",
        "mistakes",
        "milestones",
        "daily_logs",
        "concept_understanding",
        "quest_completions",
        "sessions",
        "pattern_progress",
        "user_profiles",
    ]

    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"   Cleared {table}")
        except Exception as e:
            print(f"   Warning: Could not clear {table}: {e}")

    conn.commit()
    conn.close()


def hydrate_user_profile(db: SyncDatabase, user_id: str = "test") -> None:
    """Create the test user profile."""
    print("👤 Hydrating user profile...")

    profile = UserProfile(
        id=user_id,
        name=USER_PROFILE["name"],
        quests_completed=USER_PROFILE["quests_completed"],
        created_at=USER_PROFILE["created_at"],
        last_active=USER_PROFILE["last_active"],
    )
    db.update_profile(profile)
    print(f"   Created profile: {profile.name} ({user_id})")


def hydrate_pattern_progress(db: SyncDatabase, user_id: str = "test") -> None:
    """Create pattern progress records."""
    print("📊 Hydrating pattern progress...")

    for pp in PATTERN_PROGRESS:
        progress = PatternProgress(
            id=f"{user_id}_{pp['pattern_id']}",
            user_id=user_id,
            pattern_id=pp["pattern_id"],
            progress=pp["progress"],
            quests_completed=pp["quests_completed"],
            quests_total=pp["quests_total"],
            concepts_understood=pp["concepts_understood"],
            last_practiced=pp["last_practiced"],
            next_review=pp["next_review"],
            mastered=pp["mastered"],
        )
        db.upsert_pattern_progress(progress)
        status = "MASTERED" if pp["mastered"] else f"{pp['progress']}%"
        print(f"   {pp['pattern_id']}: {status}")


def hydrate_quest_completions(db: SyncDatabase, user_id: str = "test") -> None:
    """Create quest completion records."""
    print("✅ Hydrating quest completions...")

    for qc in QUEST_COMPLETIONS:
        completion = QuestCompletion(
            id=f"{user_id}_{qc['quest_id']}",
            user_id=user_id,
            quest_id=qc["quest_id"],
            pattern_id=qc["pattern_id"],
            completed_at=qc["completed_at"],
            time_minutes=qc["time_minutes"],
            hints_used=qc["hints_used"],
            success=qc["success"],
            review_count=qc["review_count"],
            last_reviewed=qc["last_reviewed"],
            next_review_in=qc["next_review_in"],
        )
        db.upsert_quest_completion(completion)
        print(f"   {qc['quest_id']}")


def hydrate_daily_logs(db: SyncDatabase, user_id: str = "test") -> None:
    """Create daily log entries."""
    import sqlite3

    from dsa_coach.paths import BASE_DIR

    print("📅 Hydrating daily logs...")

    db_path = BASE_DIR / "coach.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for log in DAILY_LOGS:
        log_id = f"{user_id}_{log['date']}"
        patterns_json = json.dumps(log["patterns_worked"])
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_logs
            (id, user_id, date, problems_solved, time_spent_mins, hints_used, patterns_worked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                user_id,
                log["date"],
                log["problems_solved"],
                log["time_spent_mins"],
                log["hints_used"],
                patterns_json,
            ),
        )
        print(
            f"   {log['date']}: {log['problems_solved']} problems, "
            f"{log['time_spent_mins']}min"
        )

    conn.commit()
    conn.close()


def hydrate_milestones(db: SyncDatabase, user_id: str = "test") -> None:
    """Create milestone records."""
    print("🏆 Hydrating milestones...")

    for m in MILESTONES:
        db.add_milestone(
            user_id=user_id,
            milestone_type=m["milestone_type"],
            pattern_id=m["pattern_id"],
            quest_id=m["quest_id"],
            description=m["description"],
        )
        print(f"   {m['milestone_type']}: {m['description'][:40]}...")


def hydrate_mistakes(db: SyncDatabase, user_id: str = "test") -> None:
    """Create mistake records."""
    print("📝 Hydrating mistakes...")

    for m in MISTAKES:
        # Call add_mistake multiple times for recurrence
        for _ in range(m.get("recurrence_count", 1)):
            db.add_mistake(
                user_id=user_id,
                quest_id=m["quest_id"],
                pattern_id=m["pattern_id"],
                mistake_type=m["mistake_type"],
                description=m["description"],
                lesson_learned=m.get("lesson_learned"),
            )
        recur = f" (x{m['recurrence_count']})" if m["recurrence_count"] > 1 else ""
        print(f"   {m['mistake_type']}{recur}: {m['description'][:40]}...")


def hydrate_teaching_history(db: SyncDatabase, user_id: str = "test") -> None:
    """Create teaching history records."""
    print("📚 Hydrating teaching history...")

    for th in TEACHING_HISTORY:
        db.record_teaching(
            user_id=user_id,
            pattern_id=th["pattern_id"],
            concept=th["concept"],
            student_response=th["student_response"],
        )
        status_icon = {"understood": "✓", "partially": "~", "confused": "✗"}.get(
            th["student_response"], "?"
        )
        print(f"   {status_icon} {th['pattern_id']}/{th['concept']}")


def hydrate_concept_understanding(db: SyncDatabase, user_id: str = "test") -> None:
    """Create concept understanding records."""
    print("🧠 Hydrating concept understanding...")

    for cu in CONCEPT_UNDERSTANDING:
        concept_obj = ConceptUnderstanding(
            id=f"{user_id}_{cu['pattern_id']}_{cu['concept']}",
            user_id=user_id,
            pattern_id=cu["pattern_id"],
            concept=cu["concept"],
            understood=cu["understood"],
        )
        db.upsert_concept_understanding(concept_obj)
        status = "✓" if cu["understood"] else "✗"
        print(f"   {status} {cu['pattern_id']}/{cu['concept']}")


def hydrate_session(db: SyncDatabase, user_id: str = "test") -> None:
    """Create a current session (no active quest)."""
    print("🎯 Hydrating session...")

    session = db.create_session(
        user_id=user_id,
        session_type="practice",
        current_pattern=None,
        current_quest=None,
    )
    print(f"   Created session: {session.id[:8]}... (no active quest)")


def verify_data(db: SyncDatabase, user_id: str = "test") -> None:
    """Verify the hydrated data."""
    print("\n" + "=" * 60)
    print(f"🔍 VERIFICATION (user_id={user_id})")
    print("=" * 60)

    # Profile
    profile = db.get_or_create_profile(user_id)
    print(f"\n👤 Profile: {profile.name}")
    print(f"   Quests completed: {profile.quests_completed}")

    # Pattern progress
    patterns = db.get_all_pattern_progress(user_id)
    print(f"\n📊 Pattern Progress: {len(patterns)} patterns")
    for p in patterns:
        status = "MASTERED" if p.mastered else f"{p.progress}%"
        print(
            f"   {p.pattern_id}: {status} ({p.quests_completed}/{p.quests_total} quests)"
        )

    # Quest completions
    completions = db.get_completed_quests(user_id)
    print(f"\n✅ Quest Completions: {len(completions)} quests")

    # Due reviews
    due = db.get_due_reviews(user_id)
    print(f"\n⏰ Due for Review: {len(due)} quests")
    for d in due[:3]:
        print(f"   {d.quest_id}")

    # Mistakes
    mistakes = db.get_recent_mistakes(user_id, limit=10)
    recurring = db.get_recurring_mistake_types(user_id)
    print(f"\n📝 Mistakes: {len(mistakes)} total, {len(recurring)} recurring types")
    for r in recurring:
        print(f"   {r['type']}: {r['count']}x")

    # Weekly activity
    weekly = db.get_weekly_activity(user_id)
    if weekly:
        print("\n📅 This Week:")
        print(f"   Problems: {weekly.get('problems_solved', 0)}")
        print(f"   Time: {weekly.get('time_spent_mins', 0)} minutes")
        print(f"   Hints: {weekly.get('hints_used', 0)}")

    # Milestones
    milestones = db.get_recent_milestones(user_id, days=30)
    print(f"\n🏆 Recent Milestones: {len(milestones)}")

    # build_progress_compat test
    compat = db.build_progress_compat(user_id)
    print("\n🔄 build_progress_compat():")
    print(f"   patterns_completed: {compat['patterns_completed']}")
    print(f"   patterns_in_progress: {compat['patterns_in_progress']}")
    print(f"   problems_solved: {len(compat['problems_solved'])} quests")


# =============================================================================
# MAIN
# =============================================================================


def clear_user_data(user_id: str) -> None:
    """Clear all data for a specific user (preserves other users)."""
    print(f"🗑️  Clearing data for user: {user_id}")

    import sqlite3

    from dsa_coach.paths import BASE_DIR

    db_path = BASE_DIR / "coach.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete messages first (linked to sessions via session_id)
    try:
        cursor.execute(
            """
            DELETE FROM messages WHERE session_id IN (
                SELECT id FROM sessions WHERE user_id = ?
            )
        """,
            (user_id,),
        )
        if cursor.rowcount > 0:
            print(f"   Cleared {cursor.rowcount} rows from messages")
    except Exception as e:
        print(f"   Warning: Could not clear messages: {e}")

    # Tables with user_id column (sessions before pattern_progress due to FK)
    tables_with_user_id = [
        "teaching_history",
        "mistakes",
        "milestones",
        "daily_logs",
        "concept_understanding",
        "quest_completions",
        "sessions",
        "pattern_progress",
    ]

    for table in tables_with_user_id:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"   Cleared {deleted} rows from {table}")
        except Exception as e:
            print(f"   Warning: Could not clear {table}: {e}")

    # user_profiles uses 'id' not 'user_id'
    try:
        cursor.execute("DELETE FROM user_profiles WHERE id = ?", (user_id,))
        if cursor.rowcount > 0:
            print(f"   Cleared {cursor.rowcount} rows from user_profiles")
    except Exception as e:
        print(f"   Warning: Could not clear user_profiles: {e}")

    conn.commit()
    conn.close()
    print(f"   Done! User '{user_id}' data cleared.")


def main():
    parser = argparse.ArgumentParser(
        description="Hydrate test data into DSA Coach database"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing data first (for specified user only)",
    )
    parser.add_argument(
        "--user",
        default="test",
        help="User ID for test data (default: 'test'). Use 'default' to affect your real data.",
    )
    parser.add_argument(
        "--clear-only", action="store_true", help="Only clear data, don't hydrate"
    )
    args = parser.parse_args()

    user_id = args.user

    print("=" * 60)
    print("🚀 DSA Coach Test Data Hydration")
    print(f"   User ID: {user_id}")
    print("=" * 60)

    # Clear user data if requested
    if args.reset or args.clear_only:
        clear_user_data(user_id)
        print()

    if args.clear_only:
        print("Clear-only mode. Exiting.")
        return

    with SyncDatabase() as db:
        # Hydrate all tables
        hydrate_user_profile(db, user_id)
        hydrate_pattern_progress(db, user_id)
        hydrate_quest_completions(db, user_id)
        hydrate_daily_logs(db, user_id)
        hydrate_milestones(db, user_id)
        hydrate_mistakes(db, user_id)
        hydrate_teaching_history(db, user_id)
        hydrate_concept_understanding(db, user_id)
        hydrate_session(db, user_id)

        # Verify
        verify_data(db, user_id)

    print("\n" + "=" * 60)
    print("✅ Test data hydration complete!")
    print("=" * 60)
    print("\nYou can now test:")
    print("  python coach.py status")
    print("  python coach.py next")
    print("  python coach.py recall")
    print("  python coach.py mistakes")
    print("  python coach.py summary")


if __name__ == "__main__":
    main()
