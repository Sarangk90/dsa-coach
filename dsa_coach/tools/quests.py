"""Quest tools for DSA Coach agent.

Tools for managing quest assignment, completion, and hints.
"""

import contextlib
import json
import webbrowser
from datetime import datetime
from pathlib import Path

from ..storage.db import Database
from ..storage.models import PatternProgress, QuestCompletion
from .registry import ToolResult, tool

# Cache for quests.json data
_quests_cache: dict | None = None


def _load_quests() -> dict:
    """Load and cache quests.json data."""
    global _quests_cache
    if _quests_cache is None:
        quests_path = Path(__file__).parent.parent.parent / "quests.json"
        with quests_path.open() as f:
            _quests_cache = json.load(f)
    return _quests_cache


def _count_total_quests_for_pattern(pattern_id: str) -> int:
    """Count total practice problems for a given pattern (V2 only)."""
    quests = _load_quests()

    assert "curriculum" in quests, "Expected V2 quest structure with 'curriculum' key"

    # Check nested curriculum structure
    for mode in ["fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                return sum(
                    len(concept.get("practice_problems", []))
                    for concept in pattern.get("concepts", [])
                )

    return 0


def _find_quest(quest_id: str) -> dict | None:
    """Find a quest/problem by ID (V2 only)."""
    quests = _load_quests()

    assert "curriculum" in quests, "Expected V2 quest structure with 'curriculum' key"

    # Check nested curriculum structure
    for mode in ["fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(mode, [])
        for pattern in curriculum:
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    if problem.get("problem_id") == quest_id:
                        # Return enriched quest data
                        return {
                            **problem,
                            "id": problem.get("problem_id"),
                            "title": problem.get("problem_name"),
                            "pattern_id": pattern.get("pattern_id"),
                            "pattern_name": pattern.get("pattern_name"),
                            "pattern": pattern.get("pattern_id"),
                            "concept_id": concept.get("concept_id"),
                            "concept_name": concept.get("concept_name"),
                            "link": problem.get("url"),
                        }

    return None


@tool(
    name="get_quests_for_pattern",
    description="Get all available quests for a specific pattern, with completion status.",
    category="quests",
)
async def get_quests_for_pattern(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Get all quests associated with a pattern (V2 only).

    :param pattern_id: The pattern identifier (e.g., 'ft_04')
    :return: List of quests with completion status
    """
    quests = _load_quests()
    pattern_quests = []

    assert "curriculum" in quests, "Expected V2 quest structure with 'curriculum' key"

    # Check nested curriculum structure
    for mode in ["fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                for concept in pattern.get("concepts", []):
                    for problem in concept.get("practice_problems", []):
                        pattern_quests.append(
                            {
                                "id": problem.get("problem_id"),
                                "title": problem.get("problem_name"),
                                "difficulty": problem.get("difficulty", "medium"),
                                "link": problem.get("url", ""),
                            }
                        )

    # Get completion status
    completed = await db.get_completed_quests(user_id, pattern_id)
    completed_ids = {c.quest_id for c in completed}

    for quest in pattern_quests:
        quest["completed"] = quest["id"] in completed_ids

    return ToolResult(
        success=True,
        data=pattern_quests,
        message=f"Found {len(pattern_quests)} quests for {pattern_id}",
    )


@tool(
    name="get_current_quest",
    description="Get the user's currently assigned quest, if any.",
    category="quests",
)
async def get_current_quest(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Get the current active quest for the user.

    :return: Current quest details or null if none assigned
    """
    session = await db.get_latest_session(user_id)
    if not session or not session.current_quest:
        return ToolResult(
            success=True,
            data=None,
            message="No quest currently assigned",
        )

    quest = _find_quest(session.current_quest)
    if not quest:
        return ToolResult(
            success=True,
            data=None,
            message="Quest not found",
        )

    return ToolResult(
        success=True,
        data={
            "id": quest["id"],
            "title": quest.get("title", quest["id"]),
            "difficulty": quest.get("difficulty", "medium"),
            "pattern": quest.get("pattern", "unknown"),
            "link": quest.get("link", ""),
            "template": quest.get("template", ""),
        },
    )


@tool(
    name="assign_quest",
    description="Assign a new quest to the user. This sets the current quest, creates a solution file, and optionally opens the problem in the browser.",
    category="quests",
)
async def assign_quest(
    db: Database,
    quest_id: str,
    open_browser: bool = True,
    user_id: str = "default",
) -> ToolResult:
    """
    Assign a quest to the user.

    :param quest_id: The quest identifier to assign
    :param open_browser: Whether to open the LeetCode problem in browser
    :return: Quest details and solution file path
    """
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    # Update session with current quest
    session = await db.get_latest_session(user_id)
    if session:
        session.current_quest = quest_id
        session.current_pattern = quest.get("pattern")
        await db.update_session(session)
    else:
        session = await db.create_session(
            user_id=user_id,
            session_type="practice",
            current_quest=quest_id,
            current_pattern=quest.get("pattern"),
        )

    # Create solution file
    solutions_dir = Path(__file__).parent.parent.parent / "solutions"
    pattern = quest.get("pattern", "unknown")
    target_dir = solutions_dir / pattern
    target_dir.mkdir(parents=True, exist_ok=True)

    solution_file = target_dir / f"{quest_id}.py"
    if not solution_file.exists():
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

    # Open in browser if requested
    if open_browser and quest.get("link"):
        with contextlib.suppress(Exception):
            webbrowser.open(quest["link"])

    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("title", quest_id),
            "difficulty": quest.get("difficulty", "medium"),
            "pattern": quest.get("pattern", "unknown"),
            "link": quest.get("link", ""),
            "solution_file": str(solution_file),
            "hints_available": list(quest.get("hints", {}).keys()),
        },
        message=f"Quest assigned: {quest.get('title', quest_id)}",
    )


@tool(
    name="mark_quest_complete",
    description="Mark the current quest as complete and update progress. Call this when the user has finished solving a problem.",
    category="quests",
)
async def mark_quest_complete(
    db: Database,
    success: bool = True,
    time_minutes: int = None,
    hints_used: int = 0,
    user_id: str = "default",
) -> ToolResult:
    """
    Mark the current quest as complete.

    :param success: Whether the quest was solved successfully
    :param time_minutes: Time taken in minutes (optional)
    :param hints_used: Number of hints used
    :return: Updated progress and confidence
    """
    # Get current quest from session
    session = await db.get_latest_session(user_id)
    if not session or not session.current_quest:
        return ToolResult(
            success=False,
            error="No quest currently assigned. Use assign_quest first.",
        )

    quest = _find_quest(session.current_quest)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{session.current_quest}' not found",
        )

    # Get profile and update
    profile = await db.get_or_create_profile(user_id)
    profile.quests_completed += 1
    await db.update_profile(profile)

    # Record quest completion
    pattern_id = quest.get("pattern", "unknown")
    completion = QuestCompletion(
        id=f"{user_id}_{session.current_quest}",
        user_id=user_id,
        quest_id=session.current_quest,
        pattern_id=pattern_id,
        completed_at=datetime.now(),
        time_minutes=time_minutes,
        hints_used=hints_used,
        success=success,
        last_reviewed=datetime.now(),
        next_review_in=1,  # Review tomorrow
    )
    await db.upsert_quest_completion(completion)

    # Update pattern progress
    pattern_progress = await db.get_pattern_progress(user_id, pattern_id)
    if not pattern_progress:
        # Calculate total quests for this pattern
        quests_total = _count_total_quests_for_pattern(pattern_id)

        pattern_progress = PatternProgress(
            id=f"{user_id}_{pattern_id}",
            user_id=user_id,
            pattern_id=pattern_id,
            quests_total=quests_total,
        )

    # Ensure quests_total is set (migration for old records)
    if pattern_progress.quests_total == 0:
        pattern_progress.quests_total = _count_total_quests_for_pattern(pattern_id)

    pattern_progress.quests_completed += 1
    pattern_progress.last_practiced = datetime.now()

    # Update confidence based on success and hints
    if success:
        confidence_gain = 15 if hints_used == 0 else 10
        pattern_progress.confidence = min(
            100, pattern_progress.confidence + confidence_gain
        )

    await db.upsert_pattern_progress(pattern_progress)

    # Clear current quest
    session.current_quest = None
    await db.update_session(session)

    return ToolResult(
        success=True,
        data={
            "quest_id": quest["id"],
            "title": quest.get("title", quest["id"]),
            "pattern": pattern_id,
            "pattern_confidence": pattern_progress.confidence,
            "quests_completed": profile.quests_completed,
        },
        message=f"Quest complete! Pattern confidence: {pattern_progress.confidence}%",
    )


@tool(
    name="get_hint",
    description="Get a hint for the current quest. Hints are adaptive based on confidence level (low=detailed, medium=conceptual, high=minimal).",
    category="quests",
)
async def get_hint(
    db: Database,
    level: str = "auto",
    user_id: str = "default",
) -> ToolResult:
    """
    Get a hint for the current quest.

    :param level: Hint level - 'low', 'medium', 'high', or 'auto' (based on confidence)
    :return: Hint text and metadata
    """
    # Get current quest
    session = await db.get_latest_session(user_id)
    if not session or not session.current_quest:
        return ToolResult(
            success=False,
            error="No quest currently assigned",
        )

    quest = _find_quest(session.current_quest)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{session.current_quest}' not found",
        )

    hints = quest.get("hints", {})
    if not hints:
        return ToolResult(
            success=False,
            error="No hints available for this quest",
        )

    # Determine hint level
    if level == "auto":
        pattern_id = quest.get("pattern", "unknown")
        progress = await db.get_pattern_progress(user_id, pattern_id)
        confidence = progress.confidence if progress else 0

        if confidence >= 70:
            level = "high"
        elif confidence >= 40:
            level = "medium"
        else:
            level = "low"

    hint_text = hints.get(level)
    if not hint_text:
        # Fall back to any available hint
        level = list(hints.keys())[0]
        hint_text = hints[level]

    return ToolResult(
        success=True,
        data={
            "quest_id": session.current_quest,
            "level": level,
            "hint": hint_text,
            "available_levels": list(hints.keys()),
        },
        message=f"Hint ({level}): {hint_text[:50]}...",
    )


@tool(
    name="get_next_recommended_quest",
    description="Get the next recommended quest based on user progress, patterns, and learning path. Use this to determine what problem the user should solve next.",
    category="quests",
)
async def get_next_recommended_quest(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Get the next recommended quest using intelligent selection logic.

    This tool uses the curriculum's selection algorithm to find the optimal
    next quest based on:
    - Spaced repetition schedule
    - Pattern prerequisites and unlocking
    - Weakest patterns (lowest time investment)
    - Sequential progression

    :return: Next quest details or error if no quests available
    """
    # Import here to avoid circular dependency
    from ..selection import get_next_quest

    # Build progress_compat dict from database using centralized method
    progress_compat = await db.build_progress_compat(user_id)

    # Get next quest using V2 selection logic
    quest = get_next_quest(progress_compat)

    if not quest:
        return ToolResult(
            success=False,
            error="No quests available. Either all quests are complete or prerequisites not met.",
        )

    # Return quest details
    quest_id = quest.get("problem_id", quest.get("id"))
    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("problem_name", quest.get("title")),
            "pattern_id": quest.get("pattern_id", quest.get("pattern")),
            "pattern_name": quest.get("pattern_name", "Unknown"),
            "concept_id": quest.get("concept_id"),
            "concept_name": quest.get("concept_name"),
            "difficulty": quest.get("difficulty", "medium"),
            "estimated_time_minutes": quest.get("estimated_time_minutes", 45),
            "url": quest.get("url", quest.get("link", "")),
            "reason_for_selection": quest.get("reason_for_selection", ""),
            "solution_approaches": quest.get("solution_approaches", []),
        },
        message=f"Next recommended quest: {quest.get('problem_name', quest.get('title'))} ({quest.get('pattern_name', 'Unknown')} pattern)",
    )
