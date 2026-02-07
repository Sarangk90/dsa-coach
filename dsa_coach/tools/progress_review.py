"""Progress & Review tools (4): get_progress_summary, record_review, manage_solution, review_code."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from ..constants import REVIEW_INTERVALS
from ..curriculum import get_pattern_name, get_problem_name
from ..storage.db import Database
from .quest_helpers import (
    _find_quest,
    _get_solutions_dir,
    _normalize_quest_id,
)
from .registry import ToolResult, tool


@tool(
    name="get_progress_summary",
    description="Get comprehensive progress including recent activity and due reviews.",
    category="consolidated",
)
async def get_progress_summary(
    db: Database,
    days: int = 7,
    user_id: str = "default",
) -> ToolResult:
    """
    Get comprehensive progress summary.

    :param days: Number of days to look back for activity
    :return: Activity summary, due reviews, and patterns worked
    """
    # Get all completed quests
    completions = await db.get_completed_quests(user_id)

    # Filter to recent days
    cutoff = datetime.now() - timedelta(days=days)
    recent = [c for c in completions if c.completed_at >= cutoff]

    # Group by day
    by_day: dict[str, list[dict]] = {}
    for c in recent:
        day_key = c.completed_at.date().isoformat()
        if day_key not in by_day:
            by_day[day_key] = []
        by_day[day_key].append(
            {
                "quest_id": c.quest_id,
                "quest_name": get_problem_name(c.quest_id),
                "pattern": c.pattern_id,
                "pattern_name": get_pattern_name(c.pattern_id),
                "hints_used": c.hints_used,
                "time_minutes": c.time_minutes,
            }
        )

    # Get patterns worked
    patterns_worked = [
        {"pattern_id": p, "pattern_name": get_pattern_name(p)}
        for p in {c.pattern_id for c in recent}
    ]

    # Get due reviews
    due_reviews_list = await db.get_due_reviews(user_id)
    due_reviews = []
    for completion in due_reviews_list:
        due_reviews.append(
            {
                "quest_id": completion.quest_id,
                "quest_name": get_problem_name(completion.quest_id),
                "pattern": completion.pattern_id,
                "pattern_name": get_pattern_name(completion.pattern_id),
                "last_reviewed": completion.last_reviewed.isoformat()
                if completion.last_reviewed
                else None,
                "review_count": completion.review_count,
            }
        )

    # Get weekly stats
    weekly = await db.get_weekly_activity(user_id)

    return ToolResult(
        success=True,
        data={
            "period_days": days,
            "quests_completed": len(recent),
            "patterns_worked": patterns_worked,
            "active_days": len(by_day),
            "by_day": by_day,
            "due_reviews": due_reviews,
            "due_reviews_count": len(due_reviews),
            "weekly_stats": weekly,
        },
    )


@tool(
    name="record_review",
    description="Record a spaced repetition review was completed.",
    category="consolidated",
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
    quest_id = _normalize_quest_id(quest_id)

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
        idx = min(completion.review_count, len(REVIEW_INTERVALS) - 1)
        completion.next_review_in = REVIEW_INTERVALS[idx]
    else:
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


@tool(
    name="manage_solution",
    description="Create, read, list, or get template for solution files.",
    category="consolidated",
)
async def manage_solution(
    db: Database,
    action: Literal["create", "read", "list", "template"],
    quest_id: str | None = None,
) -> ToolResult:
    """
    Unified solution file management.

    :param action: What to do - create, read, list, or template
    :param quest_id: Quest ID (required for create/read/template)
    :return: Action result
    """
    solutions_dir = _get_solutions_dir()

    if action == "list":
        if not solutions_dir.exists():
            return ToolResult(
                success=True,
                data=[],
                message="No solutions directory found",
            )

        files = []
        for solution_file in sorted(solutions_dir.glob("**/*.py")):
            if solution_file.is_file():
                q_id = solution_file.stem
                parent_dir = solution_file.parent.name
                content = solution_file.read_text()

                files.append(
                    {
                        "quest_id": q_id,
                        "category": parent_dir,
                        "path": str(solution_file),
                        "lines": len(content.split("\n")),
                        "size_bytes": len(content.encode("utf-8")),
                    }
                )

        return ToolResult(
            success=True,
            data=files,
            message=f"Found {len(files)} solution files",
        )

    # Other actions require quest_id
    if not quest_id:
        return ToolResult(
            success=False,
            error=f"quest_id is required for action '{action}'",
        )

    quest_id = _normalize_quest_id(quest_id)
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    if action == "template":
        template = quest.get("template", "# No template provided\n")
        return ToolResult(
            success=True,
            data={
                "quest_id": quest_id,
                "title": quest.get("title", quest_id),
                "pattern": quest.get("pattern", "unknown"),
                "template": template,
            },
        )

    pattern = quest.get("pattern", "unknown")
    solution_file = solutions_dir / pattern / f"{quest_id}.py"

    # Fallback search for read
    if action == "read" and not solution_file.exists():
        found = list(solutions_dir.glob(f"**/{quest_id}.py"))
        if found:
            solution_file = found[0]

    if action == "read":
        if not solution_file.exists():
            return ToolResult(
                success=False,
                error=f"Solution file not found: {solution_file}",
            )

        content = solution_file.read_text()
        return ToolResult(
            success=True,
            data={
                "path": str(solution_file),
                "content": content,
                "lines": len(content.split("\n")),
                "size_bytes": len(content.encode("utf-8")),
            },
        )

    if action == "create":
        target_dir = solutions_dir / pattern
        target_dir.mkdir(parents=True, exist_ok=True)

        if solution_file.exists():
            return ToolResult(
                success=True,
                data={
                    "path": str(solution_file),
                    "existed": True,
                },
                message=f"Solution file already exists: {solution_file}",
            )

        template = quest.get(
            "template",
            f"# Solution for {quest.get('title', quest_id)}\n\n# Your code here\n",
        )
        header = f'''"""
{quest.get("title", quest_id)}
{"=" * len(quest.get("title", quest_id))}

Difficulty: {quest.get("difficulty", "medium").upper()}
Pattern: {quest.get("pattern", "unknown")}
Link: {quest.get("link", "")}

DIVE Protocol:
1. Decode: Understand the problem completely
2. Identify: Recognize the pattern
3. Visualize: Draw examples and edge cases
4. Execute: Write clean code
5. Evaluate: Test with examples
"""

{template}
'''
        solution_file.write_text(header)

        return ToolResult(
            success=True,
            data={
                "path": str(solution_file),
                "existed": False,
            },
            message=f"Created solution file: {solution_file}",
        )

    return ToolResult(
        success=False,
        error=f"Unknown action: {action}",
    )


@tool(
    name="review_code",
    description="Get context for reviewing submitted code against a quest.",
    category="consolidated",
)
async def review_code(
    db: Database,
    code: str,
    quest_id: str,
) -> ToolResult:
    """
    Get context for code review.

    :param code: The code to review
    :param quest_id: The quest the code is for
    :return: Review context
    """
    quest_id = _normalize_quest_id(quest_id)
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("title", quest_id),
            "pattern": quest.get("pattern", "unknown"),
            "difficulty": quest.get("difficulty", "medium"),
            "code_to_review": code,
            "review_aspects": [
                "Correctness: Does the solution handle all cases?",
                "Time Complexity: What's the Big-O?",
                "Space Complexity: How much extra memory?",
                "Edge Cases: Empty input, single element, duplicates, etc.",
                "Code Style: Readability, naming, structure",
                "Pattern Usage: Does it properly use the intended pattern?",
            ],
            "hints": quest.get("hints", {}),
        },
        message="Ready for code review. Use the context to provide feedback.",
    )
