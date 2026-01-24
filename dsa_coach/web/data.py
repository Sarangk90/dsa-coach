"""Data loading and transformation for the dashboard.

This module handles all database queries and data transformations
needed by the Streamlit dashboard.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from dsa_coach.storage.models import QuestCompletion
from dsa_coach.storage.sync import SyncDatabase


def load_quests_json() -> dict:
    """Load quests.json data."""
    quests_path = Path(__file__).parent.parent.parent / "quests.json"
    with quests_path.open() as f:
        return json.load(f)


def load_slice_problem_ids() -> dict[str, set[str]]:
    """Load problem IDs organized by slice tag.

    Returns:
        Dict mapping slice tag (e.g., 'slice-1') to set of problem IDs.
    """
    quests = load_quests_json()
    slices: dict[str, set[str]] = {
        "slice-1": set(),
        "slice-2": set(),
        "slice-3": set(),
    }

    for pattern in quests.get("curriculum", {}).get("fast_track", []):
        for concept in pattern.get("concepts", []):
            for problem in concept.get("practice_problems", []):
                tags = problem.get("tags", [])
                problem_id = problem.get("problem_id", "")
                for slice_tag in ["slice-1", "slice-2", "slice-3"]:
                    if slice_tag in tags:
                        slices[slice_tag].add(problem_id)

    return slices


def load_all_problems() -> list[dict]:
    """Load all problems from quests.json with metadata."""
    quests = load_quests_json()
    problems = []

    for pattern in quests.get("curriculum", {}).get("fast_track", []):
        pattern_id = pattern.get("pattern_id", "")
        pattern_name = pattern.get("pattern_name", "")

        for concept in pattern.get("concepts", []):
            for problem in concept.get("practice_problems", []):
                tags = problem.get("tags", [])

                # Determine slice
                slice_num = 0
                for i in [1, 2, 3]:
                    if f"slice-{i}" in tags:
                        slice_num = i
                        break

                problems.append(
                    {
                        "problem_id": problem.get("problem_id", ""),
                        "problem_name": problem.get("problem_name", ""),
                        "pattern_id": pattern_id,
                        "pattern_name": pattern_name,
                        "difficulty": problem.get("difficulty", "medium"),
                        "leetcode_url": problem.get("leetcode_url", ""),
                        "tags": tags,
                        "slice": slice_num,
                        "is_google_l6": "google-l6" in tags,
                    }
                )

    return problems


def get_foundation_progress(db: SyncDatabase, user_id: str = "default") -> dict:
    """Get progress on foundation (non-slice) problems.

    Foundation problems are those completed that don't have slice tags.
    """
    completed = db.get_completed_quests(user_id)
    slice_ids = set()
    for s in load_slice_problem_ids().values():
        slice_ids.update(s)

    foundation_completions = [c for c in completed if c.quest_id not in slice_ids]

    # Get unique patterns touched
    patterns_touched = list({c.pattern_id for c in foundation_completions})

    return {
        "completed": len(foundation_completions),
        "problems": foundation_completions,
        "patterns_touched": patterns_touched,
    }


def get_slice_progress(db: SyncDatabase, user_id: str = "default") -> list[dict]:
    """Calculate progress for each slice (1, 2, 3)."""
    completed_ids = {c.quest_id for c in db.get_completed_quests(user_id)}
    slices_map = load_slice_problem_ids()
    all_problems = load_all_problems()

    slice_names = {1: "Foundation", 2: "Expansion", 3: "Mastery"}
    readiness_pcts = {1: 70, 2: 85, 3: 93}

    slices = []
    for slice_num in [1, 2, 3]:
        slice_tag = f"slice-{slice_num}"
        slice_problem_ids = slices_map.get(slice_tag, set())

        # Get full problem data for this slice
        slice_problems = [
            p for p in all_problems if p["problem_id"] in slice_problem_ids
        ]

        # Add completion status to each problem
        for p in slice_problems:
            p["completed"] = p["problem_id"] in completed_ids

        done_count = sum(1 for p in slice_problems if p["completed"])

        slices.append(
            {
                "slice": slice_num,
                "name": slice_names[slice_num],
                "readiness_pct": readiness_pcts[slice_num],
                "total": len(slice_problems),
                "completed": done_count,
                "problems": slice_problems,
            }
        )

    return slices


def get_pattern_progress_data(db: SyncDatabase, user_id: str = "default") -> list[dict]:
    """Get pattern progress with progress score and problem counts."""
    patterns = db.get_all_pattern_progress(user_id)
    all_problems = load_all_problems()
    completed_ids = {c.quest_id for c in db.get_completed_quests(user_id)}

    # Count problems per pattern
    pattern_totals: dict[str, int] = defaultdict(int)
    pattern_completed: dict[str, int] = defaultdict(int)
    for p in all_problems:
        pattern_totals[p["pattern_id"]] += 1
        if p["problem_id"] in completed_ids:
            pattern_completed[p["pattern_id"]] += 1

    # Build result with all patterns that have problems
    result = []
    pattern_dict = {p.pattern_id: p for p in patterns}

    # Get unique pattern_ids from problems
    pattern_ids = {p["pattern_id"] for p in all_problems}

    for pid in sorted(pattern_ids):
        pattern_prog = pattern_dict.get(pid)
        current_progress = pattern_prog.progress if pattern_prog else 0
        mastered = pattern_prog.mastered if pattern_prog else False

        # Determine status
        completed = pattern_completed.get(pid, 0)
        total = pattern_totals.get(pid, 0)

        if mastered:
            status = "MASTERED"
        elif current_progress >= 80:
            status = "Strong"
        elif completed > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        # Flag critical gaps (0% on important patterns)
        is_critical_gap = (
            current_progress == 0
            and total > 0
            and pid in ["dynamic_programming", "graphs", "trees", "backtracking"]
        )

        result.append(
            {
                "pattern_id": pid,
                "pattern_name": pid.replace("_", " ").title(),
                "progress": current_progress,
                "completed": completed,
                "total": total,
                "mastered": mastered,
                "status": status,
                "is_critical_gap": is_critical_gap,
            }
        )

    # Sort by progress ascending (weakest first)
    result.sort(key=lambda x: (x["progress"], x["pattern_id"]))

    return result


def get_velocity_metrics(db: SyncDatabase, user_id: str = "default") -> dict:
    """Calculate velocity metrics from completion timestamps."""
    completions = db.get_completed_quests(user_id)

    if not completions:
        return {
            "weekly": {},
            "daily": {},
            "avg_per_week": 0.0,
            "best_week": 0,
            "power_day": None,
            "calendar_data": [],
        }

    # Group by ISO week (year, week)
    weekly: dict[tuple[int, int], int] = defaultdict(int)
    # Group by day of week
    daily: dict[str, int] = defaultdict(int)
    # Group by date for calendar
    by_date: dict[date, int] = defaultdict(int)

    for c in completions:
        dt = c.completed_at
        iso = dt.isocalendar()
        weekly[(iso.year, iso.week)] += 1
        daily[dt.strftime("%a")] += 1
        by_date[dt.date()] += 1

    # Calculate averages
    weeks_list = sorted(weekly.keys())
    if len(weeks_list) > 1:
        # Calculate average excluding current week if it's partial
        avg = sum(weekly.values()) / len(weeks_list)
    else:
        avg = sum(weekly.values())

    best_week = max(weekly.values()) if weekly else 0
    power_day = max(daily, key=daily.get) if daily else None

    # Format weekly data for display
    weekly_display = {}
    for (year, week), count in sorted(weekly.items(), reverse=True)[:8]:
        # Get the Monday of that week for display
        week_start = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w").date()
        week_label = f"Week of {week_start.strftime('%b %d')}"
        weekly_display[week_label] = count

    # Build calendar data (last 42 days for 6 weeks)
    calendar_data = []
    today = date.today()
    for i in range(41, -1, -1):
        d = today - timedelta(days=i)
        calendar_data.append(
            {
                "date": d,
                "count": by_date.get(d, 0),
                "weekday": d.strftime("%a"),
                "iso_week": d.isocalendar().week,
            }
        )

    return {
        "weekly": weekly_display,
        "daily": dict(daily),
        "avg_per_week": round(avg, 1),
        "best_week": best_week,
        "power_day": power_day,
        "calendar_data": calendar_data,
        "by_date": {str(k): v for k, v in by_date.items()},
    }


def calculate_streak(db: SyncDatabase, user_id: str = "default") -> int:
    """Calculate current streak in consecutive days."""
    completions = db.get_completed_quests(user_id)
    if not completions:
        return 0

    dates = sorted({c.completed_at.date() for c in completions}, reverse=True)

    # Check if there's activity today or yesterday
    today = date.today()
    if not dates or dates[0] < today - timedelta(days=1):
        return 0

    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break

    return streak


def get_all_problems_with_status(
    db: SyncDatabase, user_id: str = "default"
) -> list[dict]:
    """Get all problems with their completion status."""
    all_problems = load_all_problems()
    completions = db.get_completed_quests(user_id)

    # Build lookup for completion data
    completion_map: dict[str, QuestCompletion] = {c.quest_id: c for c in completions}

    for p in all_problems:
        completion = completion_map.get(p["problem_id"])
        if completion:
            p["status"] = "Done"
            p["completed_at"] = completion.completed_at
            p["time_minutes"] = completion.time_minutes
            p["hints_used"] = completion.hints_used
        else:
            p["status"] = "Todo"
            p["completed_at"] = None
            p["time_minutes"] = None
            p["hints_used"] = None

    return all_problems


def get_due_reviews_data(db: SyncDatabase, user_id: str = "default") -> list[dict]:
    """Get quests due for review with details."""
    due = db.get_due_reviews(user_id)
    result = []

    for c in due:
        days_since = (date.today() - c.completed_at.date()).days
        result.append(
            {
                "quest_id": c.quest_id,
                "pattern_id": c.pattern_id,
                "completed_at": c.completed_at,
                "days_since": days_since,
                "review_count": c.review_count,
            }
        )

    return result


def get_dashboard_data(user_id: str = "default") -> dict:
    """Main aggregator function that returns all dashboard data."""
    with SyncDatabase() as db:
        foundation = get_foundation_progress(db, user_id)
        slices = get_slice_progress(db, user_id)
        patterns = get_pattern_progress_data(db, user_id)
        velocity = get_velocity_metrics(db, user_id)
        problems = get_all_problems_with_status(db, user_id)
        due_reviews = get_due_reviews_data(db, user_id)
        streak = calculate_streak(db, user_id)

        # Calculate totals for Google L6 slices
        total_slice_problems = sum(s["total"] for s in slices)
        total_slice_completed = sum(s["completed"] for s in slices)

        return {
            "foundation": foundation,
            "slices": slices,
            "patterns": patterns,
            "velocity": velocity,
            "problems": problems,
            "due_reviews": due_reviews,
            "streak": streak,
            "total_slice_problems": total_slice_problems,
            "total_slice_completed": total_slice_completed,
        }


def estimate_completion_weeks(remaining: int, pace: float) -> float | None:
    """Estimate weeks to completion at given pace."""
    if pace <= 0:
        return None
    return round(remaining / pace, 1)
