"""Progress tools for DSA Coach agent.

Tools for managing user profile, learning history, and spaced repetition.
"""

from datetime import datetime, timedelta
from typing import Optional

from .registry import tool, ToolResult
from ..storage.db import Database
from ..curriculum import get_problem_name, get_pattern_name


@tool(
    name="get_user_profile",
    description="Get the user's profile including quests completed and overall stats.",
    category="progress",
)
async def get_user_profile(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Get complete user profile.

    :return: User profile with learning stats
    """
    profile = await db.get_or_create_profile(user_id)

    return ToolResult(
        success=True,
        data={
            "name": profile.name,
            "quests_completed": profile.quests_completed,
            "member_since": profile.created_at.isoformat(),
            "last_active": profile.last_active.isoformat(),
        },
    )


@tool(
    name="get_session_state",
    description="Get the current session state including active quest and pattern.",
    category="progress",
)
async def get_session_state(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Get current session state.
    
    :return: Session info including current quest and pattern
    """
    session = await db.get_latest_session(user_id)
    if not session:
        return ToolResult(
            success=True,
            data={
                "session_id": None,
                "current_quest": None,
                "current_pattern": None,
                "session_type": None,
            },
            message="No active session",
        )
    
    return ToolResult(
        success=True,
        data={
            "session_id": session.id,
            "current_quest": session.current_quest,
            "current_pattern": session.current_pattern,
            "session_type": session.session_type,
            "started_at": session.created_at.isoformat(),
            "last_activity": session.updated_at.isoformat(),
        },
    )


@tool(
    name="get_learning_history",
    description="Get recent learning activity including completed quests and patterns worked on.",
    category="progress",
)
async def get_learning_history(
    db: Database,
    days: int = 7,
    user_id: str = "default",
) -> ToolResult:
    """
    Get learning history for recent days.
    
    :param days: Number of days to look back
    :return: List of completed quests and activity summary
    """
    # Get all completed quests
    completions = await db.get_completed_quests(user_id)
    
    # Filter to recent days
    cutoff = datetime.now() - timedelta(days=days)
    recent = [c for c in completions if c.completed_at >= cutoff]
    
    # Group by day
    by_day = {}
    for c in recent:
        day_key = c.completed_at.date().isoformat()
        if day_key not in by_day:
            by_day[day_key] = []
        by_day[day_key].append({
            "quest_id": c.quest_id,
            "quest_name": get_problem_name(c.quest_id),
            "pattern": c.pattern_id,
            "pattern_name": get_pattern_name(c.pattern_id),
            "hints_used": c.hints_used,
            "time_minutes": c.time_minutes,
        })

    # Calculate summary
    patterns_worked = [
        {"pattern_id": p, "pattern_name": get_pattern_name(p)}
        for p in set(c.pattern_id for c in recent)
    ]

    return ToolResult(
        success=True,
        data={
            "period_days": days,
            "quests_completed": len(recent),
            "patterns_worked": patterns_worked,
            "active_days": len(by_day),
            "by_day": by_day,
        },
    )


@tool(
    name="get_due_reviews",
    description="Get quests that are due for spaced repetition review today.",
    category="progress",
)
async def get_due_reviews(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Get quests due for review based on spaced repetition schedule.
    
    :return: List of quests due for review
    """
    due = await db.get_due_reviews(user_id)

    reviews = []
    for completion in due:
        reviews.append({
            "quest_id": completion.quest_id,
            "quest_name": get_problem_name(completion.quest_id),
            "pattern": completion.pattern_id,
            "pattern_name": get_pattern_name(completion.pattern_id),
            "last_reviewed": completion.last_reviewed.isoformat() if completion.last_reviewed else None,
            "review_count": completion.review_count,
            "original_completion": completion.completed_at.isoformat(),
        })

    return ToolResult(
        success=True,
        data=reviews,
        message=f"{len(reviews)} quests due for review" if reviews else "No reviews due today!",
    )


@tool(
    name="record_review",
    description="Record that a quest was reviewed as part of spaced repetition.",
    category="progress",
)
async def record_review(
    db: Database,
    quest_id: str,
    success: bool = True,
    user_id: str = "default",
) -> ToolResult:
    """
    Record a spaced repetition review.
    
    :param quest_id: The quest that was reviewed
    :param success: Whether the review was successful
    :return: Updated review schedule
    """
    completion = await db.get_quest_completion(user_id, quest_id)
    if not completion:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found in completions",
        )
    
    completion.review_count += 1
    completion.last_reviewed = datetime.now()
    
    # Calculate next review interval (spaced repetition)
    if success:
        # Increase interval: 1 -> 3 -> 7 -> 14 -> 30
        intervals = [1, 3, 7, 14, 30]
        idx = min(completion.review_count, len(intervals) - 1)
        completion.next_review_in = intervals[idx]
    else:
        # Reset to shorter interval
        completion.next_review_in = 1
    
    await db.upsert_quest_completion(completion)
    
    next_review_date = datetime.now() + timedelta(days=completion.next_review_in)
    
    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "review_count": completion.review_count,
            "next_review_in_days": completion.next_review_in,
            "next_review_date": next_review_date.date().isoformat(),
        },
        message=f"Review recorded. Next review in {completion.next_review_in} days.",
    )


# Note: update_streak function removed - no longer tracking streaks


