"""Consolidated workflow-level tools for DSA Coach agent.

This module contains 15 high-level tools that replace the original 41 atomic tools.
Each tool is designed for workflow-level operations with internal hooks for
deterministic follow-up actions (logging, milestones, note suggestions).

Tool Categories:
- Session & Quest (4): get_dashboard, start_quest, complete_quest, get_hint
- Pattern (2): list_patterns, get_pattern_details
- Learning (3): diagnose_understanding, record_learning, get_teaching_context
- Progress (2): get_progress_summary, record_review
- Code (2): manage_solution, review_code
- Notes (2): create_note, update_note
"""

from __future__ import annotations

import contextlib
import json
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from ..curriculum import get_pattern_name, get_problem_name
from ..id_mappings import get_new_pattern_id, get_new_problem_id, is_old_format_id
from ..logging_config import ToolLogger
from ..obsidian import (
    generate_pattern_note,
    generate_problem_note,
    get_filename_for_pattern,
    get_filename_for_problem,
    note_exists,
    write_note,
)
from ..obsidian import update_note as update_note_internal
from ..obsidian.analyzer import should_create_note
from ..obsidian.writer import get_vault_path
from ..storage.db import Database
from ..storage.models import ConceptUnderstanding, PatternProgress, QuestCompletion
from .registry import ToolResult, tool

# ============================================
# HELPERS
# ============================================

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


def _normalize_pattern_id(pattern_id: str) -> str:
    """Normalize pattern ID, converting old ft_* format to new slugs if needed."""
    if is_old_format_id(pattern_id):
        return get_new_pattern_id(pattern_id)
    return pattern_id


def _normalize_quest_id(quest_id: str) -> str:
    """Normalize quest/problem ID, converting old ft_* format to new slugs if needed."""
    if is_old_format_id(quest_id):
        return get_new_problem_id(quest_id)
    return quest_id


def _find_quest(quest_id: str, mode: str = "fast_track") -> dict | None:
    """Find a quest/problem by ID or name."""
    quests = _load_quests()

    # First pass: exact ID match
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    if problem.get("problem_id") == quest_id:
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

    # Second pass: fuzzy name match
    quest_id_lower = quest_id.lower().replace("_", " ").replace("-", " ")
    best_match = None
    best_match_len = 0

    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    problem_name = problem.get("problem_name", "").lower()
                    if problem_name and problem_name in quest_id_lower:
                        if len(problem_name) > best_match_len:
                            best_match_len = len(problem_name)
                            best_match = {
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

    return best_match


def _find_similar_quests(quest_id: str, max_results: int = 5) -> list[str]:
    """Find quest IDs similar to the given ID (for suggestions)."""
    quests = _load_quests()
    quest_id_lower = quest_id.lower()

    # Extract key words from the quest_id
    words = set(quest_id_lower.replace("_", " ").replace("-", " ").split())

    # Find quests with overlapping words
    matches = []
    for curriculum_mode in ["fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    problem_id = problem.get("problem_id", "")
                    problem_words = set(problem_id.lower().replace("_", " ").split())

                    # Count overlapping words
                    overlap = len(words & problem_words)
                    if overlap > 0:
                        matches.append((overlap, problem_id))

    # Sort by overlap count (descending) and return top matches
    matches.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in matches[:max_results]]


def _get_pattern_from_curriculum(
    pattern_id: str, mode: str = "fast_track"
) -> dict | None:
    """Get pattern details from V2 curriculum structure."""
    quests = _load_quests()
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                return pattern
    return None


def _get_curriculum(mode: str = "fast_track") -> list[dict]:
    """Get curriculum patterns for a specific mode."""
    return _load_quests().get("curriculum", {}).get(mode, [])


def _get_all_quests_for_pattern(
    pattern_id: str, mode: str = "fast_track"
) -> list[dict]:
    """Get all quests for a specific pattern."""
    pattern = _get_pattern_from_curriculum(pattern_id, mode)
    if not pattern:
        return []

    result = []
    for concept in pattern.get("concepts", []):
        for problem in concept.get("practice_problems", []):
            result.append(
                {
                    "id": problem.get("problem_id"),
                    "title": problem.get("problem_name"),
                    "difficulty": problem.get("difficulty", "medium"),
                    "link": problem.get("url", ""),
                    "pattern": pattern_id,
                    "concept_id": concept.get("concept_id"),
                    "concept_name": concept.get("concept_name"),
                }
            )
    return result


def _count_total_quests_for_pattern(pattern_id: str) -> int:
    """Count total practice problems for a given pattern."""
    quests = _load_quests()
    for mode in ["fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                return sum(
                    len(concept.get("practice_problems", []))
                    for concept in pattern.get("concepts", [])
                )
    return 0


def _is_pattern_unlocked(
    pattern: dict,
    completed_patterns: set[str],
    mode: str = "fast_track",
) -> bool:
    """Check if all prerequisites are satisfied."""
    prerequisites = pattern.get("prerequisites", [])
    if not prerequisites:
        return True

    for prereq_id in prerequisites:
        if prereq_id in completed_patterns:
            continue

        prereq_total = _count_total_quests_for_pattern(prereq_id)
        if prereq_total == 0:
            # Theory-only prerequisite patterns are considered satisfied.
            continue
        return False

    return True


async def _recommend_next_quest(
    db: Database,
    user_id: str,
    mode: str = "fast_track",
) -> dict | None:
    """Recommend the next quest using DB-native state."""
    completed = await db.get_completed_quests(user_id)
    completed_ids = {c.quest_id for c in completed}

    # Priority 1: due review patterns first.
    due_reviews = await db.get_due_reviews(user_id)
    for review in due_reviews:
        for candidate in _get_all_quests_for_pattern(review.pattern_id, mode):
            candidate_id = candidate.get("id")
            if candidate_id and candidate_id not in completed_ids:
                quest = _find_quest(candidate_id, mode)
                if quest:
                    return quest

    # Priority 2: weakest unlocked pattern (favor continuing in-progress patterns).
    all_progress = await db.get_all_pattern_progress(user_id)
    progress_map = {p.pattern_id: p for p in all_progress}
    completed_patterns = {p.pattern_id for p in all_progress if p.mastered}

    ranked_patterns = []
    for pattern in _get_curriculum(mode):
        pattern_id = pattern.get("pattern_id")
        if not pattern_id:
            continue
        if not _is_pattern_unlocked(pattern, completed_patterns, mode):
            continue
        progress = progress_map.get(pattern_id)
        has_started = progress is not None and progress.quests_completed > 0
        progress_value = progress.progress if progress is not None else 0
        sequence_order = pattern.get("sequence_order", 999)
        ranked_patterns.append(
            (0 if has_started else 1, progress_value, sequence_order, pattern_id)
        )

    for _, _, _, pattern_id in sorted(ranked_patterns):
        for candidate in _get_all_quests_for_pattern(pattern_id, mode):
            candidate_id = candidate.get("id")
            if candidate_id and candidate_id not in completed_ids:
                quest = _find_quest(candidate_id, mode)
                if quest:
                    return quest

    return None


def _get_pattern_concepts(pattern_id: str, mode: str = "fast_track") -> list[str]:
    """Get all concept names for a pattern."""
    quests = _load_quests()
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                return [
                    c.get("concept_name", c.get("concept_id", ""))
                    for c in pattern.get("concepts", [])
                ]
    return []


def _get_solutions_dir() -> Path:
    """Get the solutions directory path."""
    return Path(__file__).parent.parent.parent / "solutions"


# ============================================
# 1. SESSION & QUEST TOOLS (4)
# ============================================


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
    if derived_progress >= 80 and not pattern_progress.mastered:
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
    if derived_progress >= 70:
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
        log.hook_executed("check_note_creation", "skipped (progress < 70)")

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

        if current_progress >= 70:
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


# ============================================
# 2. PATTERN TOOLS (2)
# ============================================


@tool(
    name="list_patterns",
    description="List all patterns with progress. Use sort_by='progress' to find weak patterns.",
    category="consolidated",
)
async def list_patterns(
    db: Database,
    mode: str = "fast_track",
    sort_by: str = "sequence",
    user_id: str = "default",
) -> ToolResult:
    """
    List all available patterns with their learning status.

    :param mode: Curriculum mode - 'fast_track' or 'complete'
    :param sort_by: Sort order - 'sequence', 'progress', or 'last_practiced'
    :return: List of patterns with progress
    """
    quests = _load_quests()
    curriculum = quests.get("curriculum", {}).get(mode, [])

    result = []
    for pattern_data in curriculum:
        pattern_id = pattern_data.get("pattern_id")
        if not pattern_id:
            continue

        progress = await db.get_pattern_progress(user_id, pattern_id)
        all_quests = _get_all_quests_for_pattern(pattern_id, mode)

        result.append(
            {
                "pattern_id": pattern_id,
                "title": pattern_data.get(
                    "pattern_name", pattern_id.replace("_", " ").title()
                ),
                "description": f"{pattern_data.get('tier', 'foundation').title()} - {pattern_data.get('estimated_time_hours', 0)}h",
                "progress": progress.progress if progress else 0,
                "quests_completed": progress.quests_completed if progress else 0,
                "quests_total": len(all_quests),
                "mastered": progress.mastered if progress else False,
                "has_syllabus": bool(pattern_data.get("concepts")),
                "sequence_order": pattern_data.get("sequence_order", 999),
                "last_practiced": progress.last_practiced.isoformat()
                if progress and progress.last_practiced
                else None,
            }
        )

    # Sort based on requested order
    if sort_by == "progress":
        result.sort(key=lambda p: p["progress"])
    elif sort_by == "last_practiced":
        result.sort(key=lambda p: p["last_practiced"] or "1970-01-01", reverse=True)
    else:  # sequence
        result.sort(key=lambda p: p["sequence_order"])

    return ToolResult(
        success=True,
        data=result,
        message=f"Found {len(result)} patterns",
    )


@tool(
    name="get_pattern_details",
    description="Get detailed pattern view including syllabus, quests, concept understanding, and teaching history.",
    category="consolidated",
)
async def get_pattern_details(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
    mode: str = "fast_track",
) -> ToolResult:
    """
    Get comprehensive pattern information.

    :param pattern_id: The pattern identifier
    :return: Pattern details with syllabus, quests, understanding state, teaching history
    """
    pattern_id = _normalize_pattern_id(pattern_id)

    pattern_meta = _get_pattern_from_curriculum(pattern_id, mode)
    if not pattern_meta:
        return ToolResult(
            success=False,
            error=f"Pattern '{pattern_id}' not found",
        )

    # Get user's progress
    progress = await db.get_pattern_progress(user_id, pattern_id)

    # Get concept understanding
    concepts_understanding = await db.get_pattern_concepts(user_id, pattern_id)
    concepts_map = {c.concept: c.understood for c in concepts_understanding}

    # Get all quests for this pattern
    all_quests = _get_all_quests_for_pattern(pattern_id, mode)

    # Get quest completion status
    completed_quests = await db.get_completed_quests(user_id, pattern_id)
    completed_ids = {c.quest_id for c in completed_quests}

    # Build quests list
    practice_problems = []
    for quest in all_quests:
        practice_problems.append(
            {
                "id": quest["id"],
                "title": quest["title"],
                "difficulty": quest.get("difficulty", "medium"),
                "completed": quest["id"] in completed_ids,
                "concept": quest.get("concept_name", ""),
            }
        )

    # Build concepts list with understanding status
    concepts = []
    for concept_data in pattern_meta.get("concepts", []):
        concept_name = concept_data.get(
            "concept_name", concept_data.get("concept_id", "")
        )
        concepts.append(
            {
                "concept_id": concept_data.get("concept_id", ""),
                "concept_name": concept_name,
                "explanation_goal": concept_data.get("explanation_goal", ""),
                "understood": concepts_map.get(concept_name, False),
                "problems_count": len(concept_data.get("practice_problems", [])),
            }
        )

    # Get teaching history
    teaching_history = await db.get_teaching_history(user_id, pattern_id)

    # Get derived stats (source of truth)
    derived_stats = await db.get_derived_pattern_stats(user_id, pattern_id)

    result = {
        "pattern_id": pattern_id,
        "title": pattern_meta.get("pattern_name", pattern_id.replace("_", " ").title()),
        "description": f"{pattern_meta.get('tier', 'foundation').title()} pattern",
        "estimated_time_hours": pattern_meta.get("estimated_time_hours", 0),
        "prerequisites": pattern_meta.get("prerequisites", []),
        "concepts": concepts,
        "practice_problems": practice_problems,
        "all_quests_count": len(all_quests),
        "progress": {
            "progress": derived_stats["progress"],
            "quests_completed": derived_stats["quests_completed"],
            "concepts_understood": len([c for c in concepts if c["understood"]]),
            "concepts_total": len(concepts),
            "mastered": derived_stats["mastered"],
            "last_practiced": progress.last_practiced.isoformat()
            if progress and progress.last_practiced
            else None,
        },
        "teaching_history": teaching_history,
    }

    return ToolResult(success=True, data=result)


# ============================================
# 3. LEARNING TOOLS (3)
# ============================================


@tool(
    name="diagnose_understanding",
    description="Assess user's understanding of a pattern. Returns concepts with gaps and diagnosis prompts.",
    category="consolidated",
)
async def diagnose_understanding(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Assess pattern understanding and find gaps.

    :param pattern_id: The pattern to diagnose
    :return: Concepts, gaps, and diagnosis prompts
    """
    pattern_id = _normalize_pattern_id(pattern_id)

    concepts = _get_pattern_concepts(pattern_id)
    if not concepts:
        return ToolResult(
            success=False,
            error=f"No concepts defined for pattern '{pattern_id}'",
        )

    # Get current understanding state
    existing = await db.get_pattern_concepts(user_id, pattern_id)
    understood_map = {c.concept: c.understood for c in existing}

    concepts_state = []
    for concept in concepts:
        concepts_state.append(
            {
                "concept": concept,
                "understood": understood_map.get(concept, False),
                "needs_diagnosis": concept not in understood_map,
            }
        )

    # Find concepts that need diagnosis or are marked as not understood
    gaps = [c for c in concepts_state if not c["understood"]]

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "total_concepts": len(concepts),
            "understood_count": len([c for c in concepts_state if c["understood"]]),
            "concepts": concepts_state,
            "gaps": gaps,
            "diagnosis_prompts": [
                f"Can you explain {g['concept']} in your own words?" for g in gaps[:3]
            ],
        },
        message=f"Found {len(gaps)} concepts to assess for {pattern_id}",
    )


@tool(
    name="record_learning",
    description="Record any learning event: mistakes, concepts understood/taught, or milestones. Single unified tool for all learning tracking.",
    category="consolidated",
)
async def record_learning(
    db: Database,
    type: Literal["mistake", "concept_understood", "concept_taught", "milestone"],
    pattern_id: str,
    concept: str | None = None,
    quest_id: str | None = None,
    mistake_type: str | None = None,
    description: str | None = None,
    student_response: str | None = None,
    lesson_learned: str | None = None,
    milestone_type: str | None = None,
    user_id: str = "default",
) -> ToolResult:
    """
    Unified learning record.

    :param type: Type of learning event
    :param pattern_id: Pattern this relates to
    :param concept: Concept name (for concept_* types)
    :param quest_id: Quest where event occurred
    :param mistake_type: Type of mistake (off_by_one, edge_case, etc.)
    :param description: Human-readable description
    :param student_response: How student responded (understood, confused, etc.)
    :param lesson_learned: What was learned from mistake
    :param milestone_type: Type of milestone achievement
    :return: Recording confirmation with any relevant stats
    """
    log = ToolLogger("record_learning")
    log.start(
        type=type, pattern_id=pattern_id, concept=concept, mistake_type=mistake_type
    )

    pattern_id = _normalize_pattern_id(pattern_id)

    if type == "mistake":
        # Record a mistake
        valid_types = {
            "off_by_one",
            "edge_case",
            "wrong_pattern",
            "complexity",
            "syntax",
            "logic",
            "other",
        }
        if not mistake_type or mistake_type not in valid_types:
            mistake_type = "other"

        if not quest_id:
            # Try to get from current session
            session = await db.get_latest_session(user_id)
            quest_id = session.current_quest if session else "unknown"

        mistake_id = await db.add_mistake(
            user_id=user_id,
            quest_id=quest_id or "unknown",
            pattern_id=pattern_id,
            mistake_type=mistake_type,
            description=description or "Mistake recorded",
            lesson_learned=lesson_learned,
        )

        # Check for recurring patterns
        recurring = await db.get_recurring_mistake_types(user_id)
        recurrence_count = 1
        for m in recurring:
            # DB returns "type" not "mistake_type"
            if m.get("type") == mistake_type:
                recurrence_count = m["count"]
                break

        coaching_advice = None
        if recurrence_count >= 3:
            coaching_advice = f"This {mistake_type} mistake has occurred {recurrence_count} times. Consider focused practice on this area."

        return ToolResult(
            success=True,
            data={
                "type": "mistake",
                "pattern_id": pattern_id,
                "mistake_id": mistake_id,
                "mistake_type": mistake_type,
                "recurrence_count": recurrence_count,
                "is_recurring": recurrence_count > 1,
                "coaching_advice": coaching_advice,
            },
            message=f"Recorded {mistake_type} mistake"
            + (f" (occurred {recurrence_count}x)" if recurrence_count > 1 else ""),
        )

    if type == "concept_understood":
        # Record concept understanding
        if not concept:
            return ToolResult(
                success=False,
                error="concept is required for concept_understood type",
            )

        understanding = ConceptUnderstanding(
            id=f"{user_id}_{pattern_id}_{concept}",
            user_id=user_id,
            pattern_id=pattern_id,
            concept=concept,
            understood=True,
            diagnosed_at=datetime.now(),
            taught_at=datetime.now(),
            notes=description or "",
        )
        await db.upsert_concept_understanding(understanding)

        # Update pattern progress
        pattern_progress = await db.get_pattern_progress(user_id, pattern_id)
        if pattern_progress:
            all_concepts = await db.get_pattern_concepts(user_id, pattern_id)
            understood_list = [c.concept for c in all_concepts if c.understood]
            pattern_progress.concepts_understood = understood_list
            pattern_progress.concepts_total = len(_get_pattern_concepts(pattern_id))
            await db.upsert_pattern_progress(pattern_progress)

        return ToolResult(
            success=True,
            data={
                "type": "concept_understood",
                "pattern_id": pattern_id,
                "concept": concept,
                "recorded_at": datetime.now().isoformat(),
            },
            message=f"Recorded: '{concept}' - Understood",
        )

    if type == "concept_taught":
        # Record teaching interaction
        if not concept:
            return ToolResult(
                success=False,
                error="concept is required for concept_taught type",
            )

        valid_responses = {"understood", "confused", "partially", "unknown"}
        if not student_response or student_response not in valid_responses:
            student_response = "unknown"

        await db.record_teaching(
            user_id=user_id,
            pattern_id=pattern_id,
            concept=concept,
            student_response=student_response,
        )

        # Get updated teaching history
        history = await db.get_teaching_history(user_id, pattern_id)
        this_concept_history = None
        for h in history:
            if h["concept"] == concept:
                this_concept_history = h
                break

        explanation_count = (
            this_concept_history["explanation_count"] if this_concept_history else 1
        )

        coaching_advice = None
        if explanation_count >= 3:
            coaching_advice = "This concept has been explained 3+ times. Consider a different teaching approach."
        elif explanation_count == 2 and student_response in ("confused", "partially"):
            coaching_advice = "Second explanation with partial understanding. Try visual examples or analogies."

        return ToolResult(
            success=True,
            data={
                "type": "concept_taught",
                "pattern_id": pattern_id,
                "concept": concept,
                "student_response": student_response,
                "explanation_count": explanation_count,
                "coaching_advice": coaching_advice,
            },
            message=f"Recorded teaching '{concept}' (explanation #{explanation_count})",
        )

    if type == "milestone":
        # Record milestone achievement
        valid_milestone_types = {
            "pattern_mastered",
            "streak",
            "no_hints",
            "speed_improvement",
            "first_solve",
            "concept_mastered",
            "other",
        }
        if not milestone_type or milestone_type not in valid_milestone_types:
            milestone_type = "other"

        milestone_id = await db.add_milestone(
            user_id=user_id,
            milestone_type=milestone_type,
            description=description or f"Achievement: {milestone_type}",
            pattern_id=pattern_id,
            quest_id=quest_id,
        )

        return ToolResult(
            success=True,
            data={
                "type": "milestone",
                "pattern_id": pattern_id,
                "milestone_id": milestone_id,
                "milestone_type": milestone_type,
            },
            message=f"Milestone achieved: {description or milestone_type}",
        )

    return ToolResult(
        success=False,
        error=f"Unknown learning type: {type}",
    )


@tool(
    name="get_teaching_context",
    description="Get read-only context for teaching including history, recent mistakes, and focus areas.",
    category="consolidated",
)
async def get_teaching_context(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Get comprehensive teaching context.

    :param pattern_id: The pattern to get context for
    :return: Teaching history, mistakes, gaps, and recommendations
    """
    pattern_id = _normalize_pattern_id(pattern_id)

    # Get teaching history
    teaching_history = await db.get_teaching_history(user_id, pattern_id)

    # Categorize by student response
    understood = []
    confused = []
    needs_retry = []

    for h in teaching_history:
        entry = {
            "concept": h["concept"],
            "times_explained": h["explanation_count"],
            "last_response": h["student_response"],
        }
        if h["student_response"] == "understood":
            understood.append(entry)
        elif h["student_response"] == "confused":
            confused.append(entry)
        elif h["explanation_count"] >= 2:
            needs_retry.append(entry)

    # Get recent mistakes for this pattern
    recent_mistakes = await db.get_recent_mistakes(user_id, limit=10)
    pattern_mistakes = [m for m in recent_mistakes if m.get("pattern_id") == pattern_id]

    # Get recurring mistake types
    recurring = await db.get_recurring_mistake_types(user_id)

    # Get concept gaps
    all_concepts = _get_pattern_concepts(pattern_id)
    existing = await db.get_pattern_concepts(user_id, pattern_id)
    understood_concepts = {c.concept for c in existing if c.understood}
    gaps = [c for c in all_concepts if c not in understood_concepts]

    # Build focus recommendations
    focus_areas = []
    if gaps:
        focus_areas.append(f"Concepts to teach: {', '.join(gaps[:3])}")
    if confused:
        focus_areas.append(
            f"Confused concepts to reteach: {', '.join([c['concept'] for c in confused[:2]])}"
        )
    if pattern_mistakes:
        mistake_types = list({m.get("mistake_type") for m in pattern_mistakes})
        focus_areas.append(f"Recent mistakes: {', '.join(mistake_types[:3])}")

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "teaching_history": {
                "total_concepts_taught": len(teaching_history),
                "understood": understood,
                "confused": confused,
                "needs_different_approach": needs_retry,
            },
            "mistakes": {
                "recent_for_pattern": pattern_mistakes,
                "recurring_types": recurring,
            },
            "concept_gaps": gaps,
            "focus_areas": focus_areas,
        },
    )


# ============================================
# 4. PROGRESS TOOLS (2)
# ============================================


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
        intervals = [1, 3, 7, 14, 30]
        idx = min(completion.review_count, len(intervals) - 1)
        completion.next_review_in = intervals[idx]
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


# ============================================
# 5. CODE TOOLS (2)
# ============================================


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


# ============================================
# 6. NOTE TOOLS (2)
# ============================================


@tool(
    name="create_note",
    description="Create an Obsidian note for a pattern or problem. Auto-checks criteria unless forced.",
    category="consolidated",
)
async def create_note(
    db: Database,
    type: Literal["pattern", "problem"],
    pattern: str | None = None,
    problem_id: str | None = None,
    title: str | None = None,
    description: str | None = None,
    why_matters: str | None = None,
    trade_offs: str | None = None,
    code_example: str | None = None,
    code_explanation: str | None = None,
    sixty_second_pitch: str | None = None,
    key_terminology: str | None = None,
    follow_up_questions: str | None = None,
    common_pitfalls: str | None = None,
    companies: str | None = None,
    use_cases: str | None = None,
    related_patterns: str | None = None,
    has_diagram: bool = False,
    key_insight: str | None = None,
    edge_cases: str | None = None,
    solution_approach: str | None = None,
    time_complexity: str | None = None,
    space_complexity: str | None = None,
    difficulty: str | None = None,
    auto_check_criteria: bool = True,
    user_id: str = "default",
) -> ToolResult:
    """
    Create an Obsidian note.

    :param type: Note type - 'pattern' or 'problem'
    :param auto_check_criteria: Check if note should be created first
    :return: Created note path
    """
    vault = get_vault_path()
    if not vault:
        return ToolResult(
            success=False,
            error="OBSIDIAN_VAULT_PATH not configured in .env",
        )

    if type == "pattern":
        if not pattern:
            return ToolResult(
                success=False,
                error="pattern is required for pattern notes",
            )

        pattern = _normalize_pattern_id(pattern)

        # Check if note already exists
        filename = get_filename_for_pattern(pattern)
        if note_exists(filename, "pattern"):
            return ToolResult(
                success=False,
                message=f"Note already exists for pattern '{pattern}'",
                data={"exists": True, "filename": filename},
            )

        # Auto-check criteria
        if auto_check_criteria:
            pattern_progress = await db.get_pattern_progress(user_id, pattern)
            current_progress = pattern_progress.progress if pattern_progress else 0

            should_create, reason = should_create_note(
                pattern, current_progress, session_messages=0, progress_gain=0
            )
            if not should_create:
                return ToolResult(
                    success=False,
                    message=f"Note creation criteria not met: {reason}",
                    data={"should_create": False, "reason": reason},
                )

        # Parse string inputs
        try:
            trade_offs_list = json.loads(trade_offs) if trade_offs else []
        except json.JSONDecodeError:
            trade_offs_list = (
                [
                    {
                        "aspect": "General",
                        "description": trade_offs,
                        "when_to_use": "See context",
                    }
                ]
                if trade_offs
                else []
            )

        key_terms = [t.strip() for t in (key_terminology or "").split(",") if t.strip()]
        follow_ups = [
            q.strip() for q in (follow_up_questions or "").split(",") if q.strip()
        ]
        pitfalls = [p.strip() for p in (common_pitfalls or "").split(",") if p.strip()]
        company_list = [c.strip() for c in (companies or "").split(",") if c.strip()]
        use_case_list = [u.strip() for u in (use_cases or "").split(",") if u.strip()]

        related_list = []
        if related_patterns:
            for rel in related_patterns.split(","):
                rel = rel.strip()
                if rel:
                    related_list.append({"name": rel, "context": "Related pattern"})

        # Generate note content
        content = generate_pattern_note(
            pattern=pattern,
            title=title or pattern.replace("_", " ").title(),
            description=description or "",
            why_matters=why_matters or "",
            trade_offs=trade_offs_list,
            code_example=code_example or "",
            code_explanation=code_explanation or "",
            sixty_second_pitch=sixty_second_pitch or "",
            key_terminology=key_terms,
            follow_up_questions=follow_ups,
            common_pitfalls=pitfalls,
            companies=company_list,
            use_cases=use_case_list,
            related_patterns=related_list,
            has_diagram=has_diagram,
        )

        # Write to vault
        success_write, message, filepath = write_note(content, filename, "pattern")

        if success_write:
            return ToolResult(
                success=True,
                data={"filepath": str(filepath), "filename": filename},
                message=message,
            )
        return ToolResult(success=False, error=message)

    if type == "problem":
        if not problem_id:
            return ToolResult(
                success=False,
                error="problem_id is required for problem notes",
            )

        problem_id = _normalize_quest_id(problem_id)

        # Get quest info
        quest = _find_quest(problem_id)
        if not quest:
            return ToolResult(
                success=False,
                error=f"Problem '{problem_id}' not found",
            )

        # Parse inputs
        trade_offs_list = [
            t.strip() for t in (trade_offs or "").split(",") if t.strip()
        ]
        edge_cases_list = [
            e.strip() for e in (edge_cases or "").split(",") if e.strip()
        ]

        # Generate note
        content = generate_problem_note(
            problem_id=problem_id,
            title=title or quest.get("title", problem_id),
            pattern=pattern or quest.get("pattern", "unknown"),
            difficulty=difficulty or quest.get("difficulty", "medium"),
            key_insight=key_insight or "",
            trade_offs=trade_offs_list,
            edge_cases=edge_cases_list,
            solution_approach=solution_approach or "",
            time_complexity=time_complexity or "",
            space_complexity=space_complexity or "",
        )

        # Write to vault
        filename = get_filename_for_problem(problem_id)
        success_write, message, filepath = write_note(content, filename, "problem")

        if success_write:
            return ToolResult(
                success=True,
                data={"filepath": str(filepath), "filename": filename},
                message=message,
            )
        return ToolResult(success=False, error=message)

    return ToolResult(
        success=False,
        error=f"Unknown note type: {type}",
    )


@tool(
    name="update_note",
    description="Append new insights to an existing note.",
    category="consolidated",
)
async def update_note(
    db: Database,
    note_name: str,
    new_insights: str,
    section_title: str = "Additional Insights",
) -> ToolResult:
    """
    Append new section to existing note.

    :param note_name: Note filename (with or without .md)
    :param new_insights: Content to append
    :param section_title: Section header for new content
    :return: Success status
    """
    vault = get_vault_path()
    if not vault:
        return ToolResult(
            success=False,
            error="OBSIDIAN_VAULT_PATH not configured",
        )

    if not note_name.endswith(".md"):
        note_name += ".md"

    # Search in both Patterns and Problems
    patterns_path = vault / "Patterns" / note_name
    problems_path = vault / "Problems" / note_name

    filepath = None
    if patterns_path.exists():
        filepath = patterns_path
    elif problems_path.exists():
        filepath = problems_path
    else:
        return ToolResult(
            success=False,
            error=f"Note '{note_name}' not found in Patterns/ or Problems/",
        )

    # Update the note
    success_update, message = update_note_internal(
        filepath, new_insights, section_title
    )

    if success_update:
        return ToolResult(
            success=True,
            data={"filepath": str(filepath)},
            message=message,
        )
    return ToolResult(success=False, error=message)
