"""Teaching tools for DSA Coach agent.

Tools for diagnosing understanding, recording concept mastery, and finding knowledge gaps.
"""

import json
from datetime import datetime
from pathlib import Path

from ..storage.db import Database
from ..storage.models import ConceptUnderstanding, PatternProgress
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


def _get_pattern_concepts(pattern_id: str, mode: str = "fast_track") -> list[str]:
    """Get all concept names for a pattern from V2 curriculum."""
    quests = _load_quests()

    # Search V2 curriculum for the pattern
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                # Extract concept names (or IDs) from concepts array
                concepts = pattern.get("concepts", [])
                return [
                    c.get("concept_name", c.get("concept_id", "")) for c in concepts
                ]

    return []


@tool(
    name="diagnose_pattern_understanding",
    description="Start a diagnostic session to assess user's understanding of a pattern. Returns concepts to quiz on and current understanding state.",
    category="teaching",
)
async def diagnose_pattern_understanding(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Begin diagnosis of pattern understanding.

    :param pattern_id: The pattern to diagnose
    :return: Concepts to quiz and current state
    """
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
    name="record_concept_understanding",
    description="Record whether the user understands a specific concept within a pattern.",
    category="teaching",
)
async def record_concept_understanding(
    db: Database,
    pattern_id: str,
    concept: str,
    understood: bool,
    notes: str = "",
    user_id: str = "default",
) -> ToolResult:
    """
    Record understanding of a concept.

    :param pattern_id: The pattern this concept belongs to
    :param concept: The concept name/description
    :param understood: Whether the user understands it
    :param notes: Optional notes about the assessment
    :return: Updated understanding state
    """
    understanding = ConceptUnderstanding(
        id=f"{user_id}_{pattern_id}_{concept}",
        user_id=user_id,
        pattern_id=pattern_id,
        concept=concept,
        understood=understood,
        diagnosed_at=datetime.now(),
        notes=notes,
    )

    if understood:
        understanding.taught_at = datetime.now()

    await db.upsert_concept_understanding(understanding)

    # Update pattern progress concepts_understood list
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
            "pattern_id": pattern_id,
            "concept": concept,
            "understood": understood,
            "notes": notes,
        },
        message=f"Recorded: '{concept}' - {'Understood' if understood else 'Needs work'}",
    )


@tool(
    name="get_concept_gaps",
    description="Get concepts within a pattern that the user doesn't understand yet.",
    category="teaching",
)
async def get_concept_gaps(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Find gaps in concept understanding.

    :param pattern_id: The pattern to check
    :return: List of concepts that need teaching
    """
    all_concepts = _get_pattern_concepts(pattern_id)
    if not all_concepts:
        return ToolResult(
            success=True,
            data=[],
            message=f"No concepts defined for pattern '{pattern_id}'",
        )

    # Get recorded understanding
    recorded = await db.get_pattern_concepts(user_id, pattern_id)
    understood_concepts = {c.concept for c in recorded if c.understood}

    gaps = []
    for concept in all_concepts:
        if concept not in understood_concepts:
            gaps.append(
                {
                    "concept": concept,
                    "recorded": concept in {c.concept for c in recorded},
                }
            )

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "total_concepts": len(all_concepts),
            "understood": len(understood_concepts),
            "gaps": gaps,
        },
        message=f"{len(gaps)} concepts need teaching in {pattern_id}",
    )


@tool(
    name="mark_concept_taught",
    description="Mark a concept as successfully taught after a teaching session.",
    category="teaching",
)
async def mark_concept_taught(
    db: Database,
    pattern_id: str,
    concept: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Mark a concept as taught and understood.

    :param pattern_id: The pattern this concept belongs to
    :param concept: The concept that was taught
    :return: Updated state
    """
    understanding = await db.get_concept_understanding(user_id, pattern_id, concept)

    if understanding:
        understanding.understood = True
        understanding.taught_at = datetime.now()
    else:
        understanding = ConceptUnderstanding(
            id=f"{user_id}_{pattern_id}_{concept}",
            user_id=user_id,
            pattern_id=pattern_id,
            concept=concept,
            understood=True,
            taught_at=datetime.now(),
        )

    await db.upsert_concept_understanding(understanding)

    # Update pattern progress
    pattern_progress = await db.get_pattern_progress(user_id, pattern_id)
    if not pattern_progress:
        pattern_progress = PatternProgress(
            id=f"{user_id}_{pattern_id}",
            user_id=user_id,
            pattern_id=pattern_id,
        )

    all_concepts = await db.get_pattern_concepts(user_id, pattern_id)
    understood_list = [c.concept for c in all_concepts if c.understood]
    pattern_progress.concepts_understood = understood_list
    pattern_progress.concepts_total = len(_get_pattern_concepts(pattern_id))

    await db.upsert_pattern_progress(pattern_progress)

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "concept": concept,
            "understood_count": len(understood_list),
            "total_concepts": pattern_progress.concepts_total,
        },
        message=f"Marked '{concept}' as understood",
    )


@tool(
    name="get_teaching_context",
    description="Get context for teaching a specific concept, including related concepts and prerequisite knowledge.",
    category="teaching",
)
async def get_teaching_context(
    db: Database,
    pattern_id: str,
    concept: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Get context for teaching a concept.

    :param pattern_id: The pattern this concept belongs to
    :param concept: The concept to teach
    :return: Teaching context with related info
    """
    # Get pattern from V2 curriculum
    quests = _load_quests()
    pattern_meta = None
    for curriculum_mode in ["fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                pattern_meta = pattern
                break
        if pattern_meta:
            break

    if not pattern_meta:
        return ToolResult(
            success=False,
            error=f"Pattern '{pattern_id}' not found in curriculum",
        )

    # Extract concept names from concepts array
    concepts_data = pattern_meta.get("concepts", [])
    all_concepts = [
        c.get("concept_name", c.get("concept_id", "")) for c in concepts_data
    ]
    description = f"{pattern_meta.get('tier', 'foundation').title()} pattern - {pattern_meta.get('estimated_time_hours', 0)}h"

    # Get user's current understanding
    understanding = await db.get_concept_understanding(user_id, pattern_id, concept)
    all_understanding = await db.get_pattern_concepts(user_id, pattern_id)
    understood = [c.concept for c in all_understanding if c.understood]

    # Find concept index to determine prerequisites
    concept_index = all_concepts.index(concept) if concept in all_concepts else 0
    prerequisites = all_concepts[:concept_index]

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "pattern_description": description,
            "concept_to_teach": concept,
            "concept_index": concept_index,
            "total_concepts": len(all_concepts),
            "prerequisites": prerequisites,
            "prerequisites_understood": [p for p in prerequisites if p in understood],
            "user_already_understands": understood,
            "previous_notes": understanding.notes if understanding else None,
        },
    )


# ==================== Mistake Recording ====================


@tool(
    name="record_mistake",
    description="Record a mistake the student made for pattern recognition and future coaching. Use this when student makes an error during code review, hints reveal a struggle, or they explicitly mention a mistake.",
    category="teaching",
)
async def record_mistake(
    db: Database,
    quest_id: str,
    pattern_id: str,
    description: str,
    mistake_type: str | None = None,
    lesson_learned: str | None = None,
    user_id: str = "default",
) -> ToolResult:
    """
    Record a mistake for adaptive coaching.

    :param quest_id: The quest where the mistake occurred
    :param pattern_id: The pattern associated with the mistake
    :param mistake_type: Category of mistake: off_by_one, edge_case, wrong_pattern, complexity, syntax, logic
    :param description: Brief description of what went wrong
    :param lesson_learned: Optional insight the student gained from this mistake
    :return: Confirmation and updated mistake stats
    """
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

    mistake_id = await db.add_mistake(
        user_id=user_id,
        quest_id=quest_id,
        pattern_id=pattern_id,
        mistake_type=mistake_type,
        description=description,
        lesson_learned=lesson_learned,
    )

    # Get updated stats for this mistake type
    recurring = await db.get_recurring_mistake_types(user_id)
    this_type_count = 1
    for m in recurring:
        if m["mistake_type"] == mistake_type:
            this_type_count = m["count"]
            break

    return ToolResult(
        success=True,
        data={
            "mistake_id": mistake_id,
            "quest_id": quest_id,
            "pattern_id": pattern_id,
            "mistake_type": mistake_type,
            "description": description,
            "lesson_learned": lesson_learned,
            "recurrence_count": this_type_count,
        },
        message=f"Recorded {mistake_type} mistake. "
        + (
            f"This has happened {this_type_count} times - worth extra attention!"
            if this_type_count > 1
            else ""
        ),
    )


@tool(
    name="record_teaching",
    description="Record that a concept was taught to track teaching history. Call this after explaining a concept to the student.",
    category="teaching",
)
async def record_teaching(
    db: Database,
    pattern_id: str,
    concept: str,
    student_response: str = "unknown",
    user_id: str = "default",
) -> ToolResult:
    """
    Record a teaching interaction for adaptive coaching.

    :param pattern_id: The pattern this concept belongs to
    :param concept: The concept that was taught
    :param student_response: How student responded: understood, confused, partially, unknown
    :return: Teaching history for this concept
    """
    valid_responses = {"understood", "confused", "partially", "unknown"}
    if student_response not in valid_responses:
        student_response = "unknown"

    await db.record_teaching(
        user_id=user_id,
        pattern_id=pattern_id,
        concept=concept,
        student_response=student_response,
    )

    # Get updated teaching history for this concept
    history = await db.get_teaching_history(user_id, pattern_id)
    this_concept_history = None
    for h in history:
        if h["concept"] == concept:
            this_concept_history = h
            break

    explanation_count = (
        this_concept_history["explanation_count"] if this_concept_history else 1
    )

    # Provide coaching advice if we've explained this multiple times
    advice = None
    if explanation_count >= 3:
        advice = "This concept has been explained 3+ times. Consider a different teaching approach."
    elif explanation_count == 2 and student_response in ("confused", "partially"):
        advice = "Second explanation with partial understanding. Try visual examples or analogies."

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "concept": concept,
            "student_response": student_response,
            "explanation_count": explanation_count,
            "coaching_advice": advice,
        },
        message=f"Recorded teaching '{concept}' (explanation #{explanation_count})",
    )


@tool(
    name="get_recent_mistakes",
    description="Get the student's recent mistakes for review and coaching.",
    category="teaching",
)
async def get_recent_mistakes(
    db: Database,
    limit: int = 5,
    user_id: str = "default",
) -> ToolResult:
    """
    Get recent mistakes for coaching context.

    :param limit: Number of recent mistakes to retrieve
    :return: List of recent mistakes with patterns
    """
    mistakes = await db.get_recent_mistakes(user_id, limit)
    recurring = await db.get_recurring_mistake_types(user_id)

    return ToolResult(
        success=True,
        data={
            "recent_mistakes": mistakes,
            "recurring_patterns": recurring,
        },
        message=f"Found {len(mistakes)} recent mistakes, {len(recurring)} recurring patterns",
    )


@tool(
    name="log_session_activity",
    description="Log activity for the current session (problems solved, time spent). Call this when a quest is completed or session ends.",
    category="teaching",
)
async def log_session_activity(
    db: Database,
    problems_delta: int = 0,
    time_delta_mins: int = 0,
    hints_delta: int = 0,
    pattern_worked: str | None = None,
    user_id: str = "default",
) -> ToolResult:
    """
    Log session activity for engagement tracking.

    :param problems_delta: Number of problems solved in this session
    :param time_delta_mins: Approximate time spent in minutes
    :param hints_delta: Number of hints used
    :param pattern_worked: Pattern practiced (if any)
    :return: Updated weekly activity stats
    """
    await db.upsert_daily_log(
        user_id=user_id,
        problems_delta=problems_delta,
        time_delta_mins=time_delta_mins,
        hints_delta=hints_delta,
        pattern_worked=pattern_worked,
    )

    # Get updated weekly stats
    weekly = await db.get_weekly_activity(user_id)

    return ToolResult(
        success=True,
        data={
            "logged": {
                "problems": problems_delta,
                "time_mins": time_delta_mins,
                "hints": hints_delta,
                "pattern": pattern_worked,
            },
            "weekly_totals": weekly,
        },
        message=f"Logged {problems_delta} problem(s), {time_delta_mins} mins",
    )


@tool(
    name="add_milestone",
    description="Record a milestone achievement for positive reinforcement.",
    category="teaching",
)
async def add_milestone(
    db: Database,
    milestone_type: str,
    description: str,
    pattern_id: str | None = None,
    quest_id: str | None = None,
    user_id: str = "default",
) -> ToolResult:
    """
    Record a milestone achievement.

    :param milestone_type: Type: pattern_mastered, streak, no_hints, speed_improvement, first_solve
    :param description: Human-readable achievement description
    :param pattern_id: Associated pattern (if applicable)
    :param quest_id: Associated quest (if applicable)
    :return: Milestone ID and recent milestones
    """
    valid_types = {
        "pattern_mastered",
        "streak",
        "no_hints",
        "speed_improvement",
        "first_solve",
        "concept_mastered",
        "other",
    }
    if milestone_type not in valid_types:
        milestone_type = "other"

    milestone_id = await db.add_milestone(
        user_id=user_id,
        milestone_type=milestone_type,
        description=description,
        pattern_id=pattern_id,
        quest_id=quest_id,
    )

    # Get recent milestones for context
    recent = await db.get_recent_milestones(user_id, days=7)

    return ToolResult(
        success=True,
        data={
            "milestone_id": milestone_id,
            "type": milestone_type,
            "description": description,
            "recent_milestones": recent,
        },
        message=f"🎉 Milestone achieved: {description}",
    )


@tool(
    name="get_teaching_history_for_pattern",
    description="Get all concepts taught for a pattern and how the student responded.",
    category="teaching",
)
async def get_teaching_history_for_pattern(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Get teaching history for a pattern.

    :param pattern_id: The pattern to check
    :return: List of taught concepts with response data
    """
    history = await db.get_teaching_history(user_id, pattern_id)

    # Categorize by student response
    understood = []
    confused = []
    needs_retry = []

    for h in history:
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

    return ToolResult(
        success=True,
        data={
            "pattern_id": pattern_id,
            "total_concepts_taught": len(history),
            "understood": understood,
            "confused": confused,
            "needs_different_approach": needs_retry,
            "history": history,
        },
        message=f"Found {len(history)} concepts taught for {pattern_id}",
    )
