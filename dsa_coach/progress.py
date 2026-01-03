"""Progress management for DSA Coach.

**DEPRECATED**: This module is deprecated and will be removed in a future version.
All progress data is now stored in SQLite (coach.db) via dsa_coach.storage.sync.SyncDatabase.

The functions in this module are only kept for backward compatibility with tests.
Please use SyncDatabase for all new code.

Usage:
    from dsa_coach.storage.sync import SyncDatabase
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        # etc.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import Any

from . import paths
from .storage import load_json, save_json


def _deprecation_warning(func_name: str) -> None:
    """Emit deprecation warning for progress.py functions."""
    warnings.warn(
        f"{func_name}() is deprecated. Use SyncDatabase instead. "
        "See dsa_coach.storage.sync for the new API.",
        DeprecationWarning,
        stacklevel=3
    )


def get_default_progress() -> dict[str, Any]:
    """Return default progress structure."""
    now = datetime.now().isoformat()
    return {
        "profile": {
            "name": "",
            "started": now,
            "last_session": now,
            "current_quest": None,
            "quest_start_time": None,
            # V2 fields
            "active_mode": "fast_track",
            "current_pattern_id": None,
            "current_concept_id": None,
        },
        "pattern_proficiency": {
            "sliding_window": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "two_pointers": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "prefix_sum": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "hash_map": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "fast_slow_pointers": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "stack": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "linked_list": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "heap": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "merge_intervals": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "backtracking": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "dynamic_programming": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "bfs": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "dfs": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "topological_sort": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "dijkstra": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "binary_search": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "union_find": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "cyclic_sort": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
            "two_heaps": {"attempts": 0, "successes": 0, "avg_time_mins": None, "confidence": 0.0},
        },
        "completed_quests": {},  # {quest_id: {completed_at, last_practiced, times_reviewed}}
        "mistakes_log": [],
        "spaced_repetition_queue": [],
        "total_time_mins": 0,
        # V2 fields
        "patterns_completed": [],
        "patterns_in_progress": [],
        "problems_solved": {},  # {problem_id: {completed_at, attempts, time_spent_mins}}
        "time_spent_hours": {
            "total": 0.0,
            "by_pattern": {}
        },
        "daily_study_log": [],
        "milestones_achieved": [],
        "last_study_date": None,
    }


def load_progress() -> dict[str, Any]:
    """Load progress, create default if not exists; apply safe migrations.

    DEPRECATED: Use SyncDatabase instead.
    """
    _deprecation_warning("load_progress")
    progress = load_json(paths.PROGRESS_FILE)
    if not progress:
        progress = get_default_progress()

    # Migrate old list format to new dict format for completed_quests
    if isinstance(progress.get("completed_quests"), list):
        old_list = progress["completed_quests"]
        now = datetime.now().isoformat()
        progress["completed_quests"] = {
            quest_id: {"completed_at": now, "last_practiced": now, "times_reviewed": 0} for quest_id in old_list
        }
        save_json(paths.PROGRESS_FILE, progress)

    # Migration to V2 schema - add new fields if missing
    profile = progress.setdefault("profile", {})
    if "active_mode" not in profile:
        profile["active_mode"] = "fast_track"
    if "current_pattern_id" not in profile:
        profile["current_pattern_id"] = None
    if "current_concept_id" not in profile:
        profile["current_concept_id"] = None
    
    if "patterns_completed" not in progress:
        progress["patterns_completed"] = []
    if "patterns_in_progress" not in progress:
        progress["patterns_in_progress"] = []
    if "problems_solved" not in progress:
        progress["problems_solved"] = {}
    if "time_spent_hours" not in progress:
        progress["time_spent_hours"] = {"total": 0.0, "by_pattern": {}}
    if "daily_study_log" not in progress:
        progress["daily_study_log"] = []
    if "milestones_achieved" not in progress:
        progress["milestones_achieved"] = []
    if "last_study_date" not in progress:
        progress["last_study_date"] = None

    return progress


def save_progress(progress: dict[str, Any]) -> None:
    """Save progress to file.

    DEPRECATED: Use SyncDatabase instead.
    """
    _deprecation_warning("save_progress")
    save_json(paths.PROGRESS_FILE, progress)


def get_confidence(pattern: str, progress: dict[str, Any]) -> float:
    """Get confidence score for a pattern (0-100).

    DEPRECATED: Use SyncDatabase.get_pattern_progress() instead.
    """
    _deprecation_warning("get_confidence")
    prof = progress["pattern_proficiency"].get(pattern, {})
    attempts = prof.get("attempts", 0)
    successes = prof.get("successes", 0)

    if attempts == 0:
        return 0.0

    success_rate = successes / attempts
    experience_factor = min(attempts / 5, 1.0)  # Max out at 5 attempts
    confidence = success_rate * 70 + experience_factor * 30
    return round(confidence, 1)


