"""Pattern tools for DSA Coach agent.

Tools for listing, querying, and managing pattern syllabi.
"""

import json
from pathlib import Path

from ..id_mappings import get_new_pattern_id, is_old_format_id
from ..storage.db import Database
from .registry import ToolResult, tool


def _normalize_pattern_id(pattern_id: str) -> str:
    """Normalize pattern ID, converting old ft_* format to new slugs if needed."""
    if is_old_format_id(pattern_id):
        return get_new_pattern_id(pattern_id)
    return pattern_id


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


def _get_pattern_from_curriculum(
    pattern_id: str, mode: str = "fast_track"
) -> dict | None:
    """Get pattern details from V2 curriculum structure."""
    quests = _load_quests()

    # Check both fast_track and complete curricula
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            if pattern.get("pattern_id") == pattern_id:
                return pattern

    return None


def _get_all_quests_for_pattern(
    pattern_id: str, mode: str = "fast_track"
) -> list[dict]:
    """Get all quests (practice problems) for a specific pattern from V2 structure."""
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


@tool(
    name="list_patterns",
    description="List all available DSA patterns with their titles and brief status. Use this to show the user what patterns are available to learn.",
    category="patterns",
)
async def list_patterns(
    db: Database, user_id: str = "default", mode: str = "fast_track"
) -> ToolResult:
    """
    List all available patterns with their learning status.

    Returns a list of patterns with:
    - pattern_id: Unique identifier
    - title: Display name
    - progress: User's current progress (0-100)
    - quests_completed: Number of completed quests
    - quests_total: Total practice problems
    - mastered: Whether pattern is mastered
    """
    quests = _load_quests()

    # Get patterns from V2 curriculum structure
    curriculum = quests.get("curriculum", {}).get(mode, [])

    result = []
    for pattern_data in curriculum:
        pattern_id = pattern_data.get("pattern_id")
        if not pattern_id:
            continue

        # Get user's progress for this pattern
        progress = await db.get_pattern_progress(user_id, pattern_id)

        # Count total quests for this pattern
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
            }
        )

    # Sort by sequence order (curriculum progression)
    result.sort(key=lambda p: p["sequence_order"])

    return ToolResult(
        success=True,
        data=result,
        message=f"Found {len(result)} patterns",
    )


@tool(
    name="get_pattern_details",
    description="Get detailed information about a specific pattern including its syllabus, concepts to learn, and essential practice problems.",
    category="patterns",
)
async def get_pattern_details(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
    mode: str = "fast_track",
) -> ToolResult:
    """
    Get detailed syllabus and progress for a pattern.

    :param pattern_id: The pattern identifier (e.g., 'sliding_window')
    :return: Pattern details with syllabus and user progress
    """
    # Normalize pattern_id (accept old ft_* format for backward compatibility)
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

    # Build quests list from concepts
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
        concept_id = concept_data.get("concept_id", "")
        concepts.append(
            {
                "concept_id": concept_id,
                "concept_name": concept_data.get("concept_name", ""),
                "explanation_goal": concept_data.get("explanation_goal", ""),
                "understood": concepts_map.get(concept_id, False),
                "problems_count": len(concept_data.get("practice_problems", [])),
            }
        )

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
            "progress": progress.progress if progress else 0,
            "quests_completed": progress.quests_completed if progress else 0,
            "concepts_understood": len([c for c in concepts if c["understood"]]),
            "concepts_total": len(concepts),
            "mastered": progress.mastered if progress else False,
            "last_practiced": progress.last_practiced.isoformat()
            if progress and progress.last_practiced
            else None,
        },
    }

    return ToolResult(success=True, data=result)


@tool(
    name="get_weak_patterns",
    description="Get patterns that need the most work, sorted by progress (lowest first). Use this to recommend what the user should focus on.",
    category="patterns",
)
async def get_weak_patterns(
    db: Database,
    limit: int = 5,
    user_id: str = "default",
    mode: str = "fast_track",
) -> ToolResult:
    """
    Get patterns with lowest progress that need work.

    :param limit: Maximum number of patterns to return
    :return: List of weak patterns with details
    """
    quests = _load_quests()
    curriculum = quests.get("curriculum", {}).get(mode, [])

    # Get all pattern progress
    all_progress = await db.get_all_pattern_progress(user_id)
    progress_map = {p.pattern_id: p for p in all_progress}

    result = []
    for pattern_data in curriculum:
        pattern_id = pattern_data.get("pattern_id")
        if not pattern_id:
            continue

        pattern_progress = progress_map.get(pattern_id)
        current_progress = pattern_progress.progress if pattern_progress else 0

        # Calculate why it's weak
        reasons = []
        if current_progress == 0:
            reasons.append("Not started")
        elif current_progress < 30:
            reasons.append("Low progress")
        elif current_progress < 60:
            reasons.append("Needs more practice")

        if pattern_progress and not pattern_progress.mastered:
            if pattern_progress.quests_completed < pattern_progress.quests_total:
                reasons.append(
                    f"Only {pattern_progress.quests_completed}/{pattern_progress.quests_total} problems solved"
                )

        result.append(
            {
                "pattern_id": pattern_id,
                "title": pattern_data.get(
                    "pattern_name", pattern_id.replace("_", " ").title()
                ),
                "progress": current_progress,
                "reasons": reasons or ["Could use more practice"],
                "has_syllabus": bool(pattern_data.get("concepts")),
            }
        )

    # Sort by progress (ascending) and take top N
    result.sort(key=lambda p: p["progress"])
    result = result[:limit]

    return ToolResult(
        success=True,
        data=result,
        message=f"Found {len(result)} patterns that need work",
    )


@tool(
    name="get_next_essential_quest",
    description="Get the next practice problem for a pattern that hasn't been completed yet.",
    category="patterns",
)
async def get_next_essential_quest(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
    mode: str = "fast_track",
) -> ToolResult:
    """
    Get the next uncompleted quest for a pattern.

    :param pattern_id: The pattern identifier
    :return: Next quest details or null if all completed
    """
    pattern_meta = _get_pattern_from_curriculum(pattern_id, mode)
    if not pattern_meta:
        return ToolResult(
            success=False,
            error=f"Pattern '{pattern_id}' not found",
        )

    # Get all quests for this pattern
    all_quests = _get_all_quests_for_pattern(pattern_id, mode)
    if not all_quests:
        return ToolResult(
            success=True,
            data=None,
            message="No practice problems defined for this pattern",
        )

    # Get completed quests
    completed = await db.get_completed_quests(user_id, pattern_id)
    completed_ids = {c.quest_id for c in completed}

    # Find first uncompleted quest
    for quest in all_quests:
        quest_id = quest["id"]
        if quest_id not in completed_ids:
            return ToolResult(
                success=True,
                data={
                    "quest_id": quest_id,
                    "title": quest.get("title", quest_id),
                    "difficulty": quest.get("difficulty", "medium"),
                    "link": quest.get("link", ""),
                    "pattern": pattern_id,
                    "concept": quest.get("concept_name", ""),
                },
            )

    # All quests completed
    return ToolResult(
        success=True,
        data=None,
        message=f"All practice problems for {pattern_id} are completed! Pattern mastered!",
    )
