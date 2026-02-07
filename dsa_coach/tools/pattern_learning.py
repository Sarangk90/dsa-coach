"""Pattern & Learning tools (5): list_patterns, get_pattern_details, diagnose_understanding, record_learning, get_teaching_context."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from ..constants import (
    VALID_MILESTONE_TYPES,
    VALID_MISTAKE_TYPES,
    VALID_STUDENT_RESPONSES,
)
from ..curriculum import get_curriculum_data
from ..logging_config import ToolLogger
from ..storage.db import Database
from ..storage.models import ConceptUnderstanding
from .quest_helpers import (
    _get_all_quests_for_pattern,
    _get_pattern_concepts,
    _get_pattern_from_curriculum,
    _normalize_pattern_id,
)
from .registry import ToolResult, tool


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
    data = get_curriculum_data()
    curriculum = data.get("curriculum", {}).get(mode, [])

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
        if not mistake_type or mistake_type not in VALID_MISTAKE_TYPES:
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

        if not student_response or student_response not in VALID_STUDENT_RESPONSES:
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
        if not milestone_type or milestone_type not in VALID_MILESTONE_TYPES:
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
