"""Session & Quest tools (4): get_dashboard, start_quest, complete_quest, get_hint."""

from __future__ import annotations

import contextlib
import webbrowser
from datetime import datetime

from ..constants import MASTERY_THRESHOLD, NOTE_SUGGESTION_THRESHOLD
from ..curriculum import get_pattern_name
from ..logging_config import ToolLogger
from ..storage.db import Database
from ..storage.models import PatternProgress, QuestCompletion
from .quest_helpers import (
    _count_total_quests_for_pattern,
    _find_quest,
    _find_similar_quests,
    _get_all_quests_for_pattern,
    _get_solutions_dir,
    _normalize_pattern_id,
    _normalize_quest_id,
    _recommend_next_quest,
    should_create_note,
)
from .registry import ToolResult, tool


@tool(
    name="get_dashboard",
    description="Get comprehensive session state including profile, current quest, weak patterns, and due reviews. Use at session start.",
    category="consolidated",
)
async def get_dashboard(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Comprehensive dashboard for session start.

    Returns:
        - profile: User profile with stats
        - current_quest: Currently assigned quest (if any)
        - weak_patterns: Top 5 patterns needing work
        - due_reviews_count: Number of quests due for spaced repetition
        - alerts: Important notifications (reviews due, etc.)
    """
    # Get profile
    profile = await db.get_or_create_profile(user_id)

    # Get session state
    session = await db.get_latest_session(user_id)
    current_quest = None
    if session and session.current_quest:
        quest = _find_quest(session.current_quest)
        if quest:
            current_quest = {
                "id": session.current_quest,
                "title": quest.get("title", session.current_quest),
                "pattern_id": quest.get("pattern", "unknown"),
                "pattern_name": quest.get("pattern_name", "Unknown"),
                "difficulty": quest.get("difficulty", "medium"),
            }

    # Get weak patterns (sorted by progress, lowest first)
    all_progress = await db.get_all_pattern_progress(user_id)
    weak_patterns = sorted(all_progress, key=lambda p: p.progress)[:5]

    # Get due reviews
    due_reviews = await db.get_due_reviews(user_id)

    # Build alerts
    alerts = []
    if due_reviews:
        alerts.append(
            {
                "type": "review",
                "message": f"{len(due_reviews)} quests due for review",
                "priority": "high" if len(due_reviews) >= 3 else "medium",
            }
        )

    # Get total quests completed (derived from quest_completions - source of truth)
    total_quests_completed = await db.get_total_quests_completed(user_id)

    return ToolResult(
        success=True,
        data={
            "profile": {
                "name": profile.name,
                "quests_completed": total_quests_completed,
                "member_since": profile.created_at.isoformat(),
                "last_active": profile.last_active.isoformat(),
            },
            "current_quest": current_quest,
            "weak_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_name": get_pattern_name(p.pattern_id),
                    "progress": p.progress,
                    "quests_completed": p.quests_completed,
                    "quests_total": p.quests_total,
                }
                for p in weak_patterns
            ],
            "due_reviews_count": len(due_reviews),
            "alerts": alerts,
        },
    )


@tool(
    name="start_quest",
    description="Assign a quest to work on. Optionally specify quest_id or pattern_id; if neither, gets intelligent recommendation. Creates solution file and opens browser.",
    category="consolidated",
)
async def start_quest(
    db: Database,
    quest_id: str | None = None,
    pattern_id: str | None = None,
    open_browser: bool = True,
    user_id: str = "default",
) -> ToolResult:
    """
    Smart quest assignment.

    - If quest_id: assign that specific quest
    - If pattern_id: get next uncompleted for that pattern
    - If neither: use intelligent recommendation algorithm

    :param quest_id: Specific quest to assign
    :param pattern_id: Pattern to get next quest for
    :param open_browser: Whether to open LeetCode in browser
    :return: Quest details and solution file path
    """
    log = ToolLogger("start_quest")
    log.start(quest_id=quest_id, pattern_id=pattern_id)

    # Determine which quest to assign
    if quest_id:
        # Normalize and find specific quest
        quest_id = _normalize_quest_id(quest_id)
        quest = _find_quest(quest_id)
        if not quest:
            # Try to find similar quests to suggest
            suggestions = _find_similar_quests(quest_id)
            error_msg = f"Quest '{quest_id}' not found in curriculum."
            if suggestions:
                error_msg += f" Did you mean: {', '.join(suggestions[:3])}?"
            log.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
            )
    elif pattern_id:
        # Get next uncompleted for pattern
        pattern_id = _normalize_pattern_id(pattern_id)
        all_quests = _get_all_quests_for_pattern(pattern_id)
        if not all_quests:
            return ToolResult(
                success=False,
                error=f"No quests found for pattern '{pattern_id}'",
            )

        completed = await db.get_completed_quests(user_id, pattern_id)
        completed_ids = {c.quest_id for c in completed}

        quest = None
        for q in all_quests:
            if q["id"] not in completed_ids:
                quest = _find_quest(q["id"])
                break

        if not quest:
            return ToolResult(
                success=True,
                data=None,
                message=f"All quests for pattern '{pattern_id}' are completed!",
            )
        quest_id = quest["id"]
    else:
        # Use DB-native recommendation logic.
        quest = await _recommend_next_quest(db, user_id)
        if not quest:
            return ToolResult(
                success=False,
                error="No quests available. Either all complete or prerequisites not met.",
            )
        quest_id = quest["id"]

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
    solutions_dir = _get_solutions_dir()
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

    log.success(f"quest={quest_id} pattern={quest.get('pattern')}")
    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("title", quest_id),
            "difficulty": quest.get("difficulty", "medium"),
            "pattern_id": quest.get("pattern", "unknown"),
            "pattern_name": quest.get("pattern_name", "Unknown"),
            "link": quest.get("link", ""),
            "solution_file": str(solution_file),
            "hints_available": list(quest.get("hints", {}).keys()),
        },
        message=f"Quest assigned: {quest.get('title', quest_id)}",
    )


@tool(
    name="complete_quest",
    description="Mark current quest as complete. Automatically logs activity, checks for milestones, and suggests note creation if appropriate.",
    category="consolidated",
)
async def complete_quest(
    db: Database,
    success: bool = True,
    time_minutes: int | None = None,
    hints_used: int = 0,
    user_id: str = "default",
) -> ToolResult:
    """
    Complete current quest with INTERNAL hooks.

    Hooks (deterministic, always execute):
    1. log_session_activity - Always logs problems solved
    2. check_milestone - Awards milestone if progress >= 80
    3. check_note_creation - Suggests note if progress >= 70

    :param success: Whether the quest was solved successfully
    :param time_minutes: Time taken in minutes (optional)
    :param hints_used: Number of hints used
    :return: Updated progress, milestone info, and note suggestions
    """
    log = ToolLogger("complete_quest")
    log.start(success=success, time_minutes=time_minutes, hints_used=hints_used)

    # Get current quest from session
    session = await db.get_latest_session(user_id)

    if not session or not session.current_quest:
        error_msg = "No quest currently assigned. Use start_quest first."
        log.error(error_msg)
        return ToolResult(
            success=False,
            error=error_msg,
        )

    quest = _find_quest(session.current_quest)
    if not quest:
        error_msg = f"Quest '{session.current_quest}' not found in curriculum"
        log.error(error_msg)
        return ToolResult(
            success=False,
            error=error_msg,
        )

    quest_id = session.current_quest
    pattern_id = quest.get("pattern", "unknown")

    # Check if this quest was already completed (re-completion check)
    existing_completion = await db.get_quest_completion(user_id, quest_id)
    is_new_completion = existing_completion is None

    if not is_new_completion:
        # Quest already completed - reject with clear message
        log.logger.info(
            f"RE_COMPLETION_REJECTED | quest={quest_id} "
            f"original_completion={existing_completion.completed_at.isoformat()}"
        )
        # Clear current quest since they're "done" with it
        session.current_quest = None
        await db.update_session(session)

        return ToolResult(
            success=True,  # Not an error, just already done
            data={
                "quest_id": quest_id,
                "already_completed": True,
                "original_completion": existing_completion.completed_at.isoformat(),
                "message": "This quest was already completed. Progress unchanged.",
            },
            message=f"Quest '{quest.get('title', quest_id)}' was already completed on "
            f"{existing_completion.completed_at.strftime('%Y-%m-%d')}. "
            "No changes made to progress.",
        )

    # NEW COMPLETION - Insert the quest completion record (SOURCE OF TRUTH)
    # Counters (quests_completed, progress) are now DERIVED from this table
    completion = QuestCompletion(
        id=f"{user_id}_{quest_id}",
        user_id=user_id,
        quest_id=quest_id,
        pattern_id=pattern_id,
        completed_at=datetime.now(),
        time_minutes=time_minutes,
        hints_used=hints_used,
        success=success,
        last_reviewed=datetime.now(),
        next_review_in=1,  # Review tomorrow
    )
    await db.upsert_quest_completion(completion)

    # Get or calculate quests_total for proper progress scaling
    pattern_progress = await db.get_pattern_progress(user_id, pattern_id)
    if pattern_progress and pattern_progress.quests_total > 0:
        quests_total = pattern_progress.quests_total
    else:
        quests_total = _count_total_quests_for_pattern(pattern_id)

    # Get derived stats from quest_completions (single source of truth)
    # Pass quests_total for proper progress scaling
    derived_stats = await db.get_derived_pattern_stats(
        user_id, pattern_id, quests_total=quests_total
    )
    derived_progress = derived_stats["progress"]
    derived_quests_completed = derived_stats["quests_completed"]

    # Update pattern_progress for non-derived fields (last_practiced, mastered, quests_total)
    if not pattern_progress:
        pattern_progress = PatternProgress(
            id=f"{user_id}_{pattern_id}",
            user_id=user_id,
            pattern_id=pattern_id,
            quests_total=quests_total,
        )

    if pattern_progress.quests_total == 0:
        pattern_progress.quests_total = quests_total

    # Update timestamp (not a counter, still needed)
    pattern_progress.last_practiced = datetime.now()
    # Sync derived values into pattern_progress for fast reads.
    pattern_progress.quests_completed = derived_quests_completed
    pattern_progress.progress = derived_progress

    await db.upsert_pattern_progress(pattern_progress)

    # Clear current quest
    session.current_quest = None
    await db.update_session(session)

    # ============================================
    # HOOK 1: Log Session Activity (ALWAYS)
    # ============================================
    log.hook_executed("log_session_activity", f"problems=1 time={time_minutes}m")
    await db.upsert_daily_log(
        user_id=user_id,
        problems_delta=1,
        time_delta_mins=time_minutes or 0,
        hints_delta=hints_used,
        pattern_worked=pattern_id,
    )

    # ============================================
    # HOOK 2: Check Milestone (CONDITIONAL)
    # ============================================
    milestone_awarded = None
    if derived_progress >= MASTERY_THRESHOLD and not pattern_progress.mastered:
        pattern_progress.mastered = True
        await db.upsert_pattern_progress(pattern_progress)

        pattern_name = get_pattern_name(pattern_id)
        milestone_id = await db.add_milestone(
            user_id=user_id,
            milestone_type="pattern_mastered",
            description=f"Mastered {pattern_name}!",
            pattern_id=pattern_id,
        )
        milestone_awarded = {
            "type": "pattern_mastered",
            "id": milestone_id,
            "description": f"Mastered {pattern_name}!",
        }
        log.hook_executed(
            "check_milestone", f"AWARDED pattern_mastered for {pattern_id}"
        )
    else:
        log.hook_executed("check_milestone", f"skipped (progress={derived_progress})")

    # ============================================
    # HOOK 3: Check Note Creation (CONDITIONAL)
    # ============================================
    note_suggestion = None
    if derived_progress >= NOTE_SUGGESTION_THRESHOLD:
        should_create, reason = should_create_note(
            pattern_id,
            derived_progress,
            session_messages=0,
            progress_gain=0,
        )
        if should_create:
            note_suggestion = {
                "pattern_id": pattern_id,
                "reason": reason,
                "action": "Consider creating a pattern note to solidify learning",
            }
            log.hook_executed("check_note_creation", f"suggested for {pattern_id}")
        else:
            log.hook_executed("check_note_creation", f"skipped: {reason}")
    else:
        log.hook_executed(
            "check_note_creation",
            f"skipped (progress < {NOTE_SUGGESTION_THRESHOLD})",
        )

    # Get total quests completed (derived from quest_completions table)
    total_quests_completed = await db.get_total_quests_completed(user_id)

    log.success(f"quest={quest_id} progress={derived_progress}%")
    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("title", quest_id),
            "pattern_id": pattern_id,
            "pattern_progress": derived_progress,
            "quests_completed": total_quests_completed,
            # Hook results
            "activity_logged": True,
            "milestone_awarded": milestone_awarded,
            "note_suggestion": note_suggestion,
        },
        message=f"Quest complete! Pattern progress: {derived_progress}%",
    )


@tool(
    name="get_hint",
    description="Get adaptive hint for current quest based on progress level.",
    category="consolidated",
)
async def get_hint(
    db: Database,
    level: str = "auto",
    user_id: str = "default",
) -> ToolResult:
    """
    Get a hint for the current quest.

    :param level: Hint level - 'low', 'medium', 'high', or 'auto' (based on progress)
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
        pattern_progress = await db.get_pattern_progress(user_id, pattern_id)
        current_progress = pattern_progress.progress if pattern_progress else 0

        if current_progress >= NOTE_SUGGESTION_THRESHOLD:
            level = "high"
        elif current_progress >= 40:
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
