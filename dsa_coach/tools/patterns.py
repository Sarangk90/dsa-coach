"""Pattern tools for DSA Coach agent.

Tools for listing, querying, and managing pattern syllabi.
"""

import json
from pathlib import Path
from typing import Any, Optional

from .registry import tool, ToolResult
from ..storage.db import Database
from ..storage.models import PatternProgress


# Cache for quests.json data
_quests_cache: Optional[dict] = None


def _load_quests() -> dict:
    """Load and cache quests.json data."""
    global _quests_cache
    if _quests_cache is None:
        quests_path = Path(__file__).parent.parent.parent / "quests.json"
        with open(quests_path, "r") as f:
            _quests_cache = json.load(f)
    return _quests_cache


def _get_pattern_metadata(pattern_id: str) -> Optional[dict]:
    """Get metadata for a specific pattern from quests.json."""
    quests = _load_quests()
    patterns = quests.get("metadata", {}).get("patterns", {})
    return patterns.get(pattern_id)


def _get_all_quests_for_pattern(pattern_id: str) -> list[dict]:
    """Get all quests that belong to a specific pattern."""
    quests = _load_quests()
    result = []
    
    for day_key, day_data in quests.get("days", {}).items():
        for quest in day_data.get("quests", []):
            if quest.get("pattern") == pattern_id:
                quest["day"] = day_key
                result.append(quest)
    
    return result


@tool(
    name="list_patterns",
    description="List all available DSA patterns with their titles and brief status. Use this to show the user what patterns are available to learn.",
    category="patterns",
)
async def list_patterns(db: Database, user_id: str = "default") -> ToolResult:
    """
    List all available patterns with their learning status.
    
    Returns a list of patterns with:
    - pattern_id: Unique identifier
    - title: Display name
    - confidence: User's current confidence (0-100)
    - quests_completed: Number of completed quests
    - quests_total: Total essential quests
    - mastered: Whether pattern is mastered
    """
    quests = _load_quests()
    patterns = quests.get("metadata", {}).get("patterns", {})
    
    result = []
    for pattern_id, pattern_data in patterns.items():
        # Get user's progress for this pattern
        progress = await db.get_pattern_progress(user_id, pattern_id)
        
        # Count quests for this pattern
        all_quests = _get_all_quests_for_pattern(pattern_id)
        essential = pattern_data.get("essential_questions", [])
        
        result.append({
            "pattern_id": pattern_id,
            "title": pattern_data.get("title", pattern_id.replace("_", " ").title()),
            "description": pattern_data.get("description", ""),
            "confidence": progress.confidence if progress else 0,
            "quests_completed": progress.quests_completed if progress else 0,
            "quests_total": len(essential) if essential else len(all_quests),
            "mastered": progress.mastered if progress else False,
            "has_syllabus": bool(pattern_data.get("concepts")),
        })
    
    # Sort by confidence (ascending) to show weakest first
    result.sort(key=lambda p: p["confidence"])
    
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
) -> ToolResult:
    """
    Get detailed syllabus and progress for a pattern.
    
    :param pattern_id: The pattern identifier (e.g., 'sliding_window')
    :return: Pattern details with syllabus and user progress
    """
    pattern_meta = _get_pattern_metadata(pattern_id)
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
    all_quests = _get_all_quests_for_pattern(pattern_id)
    essential_ids = pattern_meta.get("essential_questions", [])
    
    # Get quest completion status
    completed_quests = await db.get_completed_quests(user_id, pattern_id)
    completed_ids = {c.quest_id for c in completed_quests}
    
    # Build essential quests list with status
    essential_quests = []
    for quest_id in essential_ids:
        quest = next((q for q in all_quests if q["id"] == quest_id), None)
        if quest:
            essential_quests.append({
                "id": quest_id,
                "title": quest.get("title", quest_id),
                "difficulty": quest.get("difficulty", "medium"),
                "completed": quest_id in completed_ids,
            })
    
    # Build concepts list with understanding status
    concepts = []
    for concept in pattern_meta.get("concepts", []):
        concepts.append({
            "concept": concept,
            "understood": concepts_map.get(concept, False),
        })
    
    result = {
        "pattern_id": pattern_id,
        "title": pattern_meta.get("title", pattern_id.replace("_", " ").title()),
        "description": pattern_meta.get("description", ""),
        "concepts": concepts,
        "essential_quests": essential_quests,
        "all_quests_count": len(all_quests),
        "progress": {
            "confidence": progress.confidence if progress else 0,
            "quests_completed": progress.quests_completed if progress else 0,
            "concepts_understood": len([c for c in concepts if c["understood"]]),
            "concepts_total": len(concepts),
            "mastered": progress.mastered if progress else False,
            "last_practiced": progress.last_practiced.isoformat() if progress and progress.last_practiced else None,
        },
    }
    
    return ToolResult(success=True, data=result)


@tool(
    name="get_weak_patterns",
    description="Get patterns that need the most work, sorted by confidence (lowest first). Use this to recommend what the user should focus on.",
    category="patterns",
)
async def get_weak_patterns(
    db: Database,
    limit: int = 5,
    user_id: str = "default",
) -> ToolResult:
    """
    Get patterns with lowest confidence that need work.
    
    :param limit: Maximum number of patterns to return
    :return: List of weak patterns with details
    """
    quests = _load_quests()
    patterns = quests.get("metadata", {}).get("patterns", {})
    
    # Get all pattern progress
    all_progress = await db.get_all_pattern_progress(user_id)
    progress_map = {p.pattern_id: p for p in all_progress}
    
    result = []
    for pattern_id, pattern_data in patterns.items():
        progress = progress_map.get(pattern_id)
        confidence = progress.confidence if progress else 0
        
        # Calculate why it's weak
        reasons = []
        if confidence == 0:
            reasons.append("Not started")
        elif confidence < 30:
            reasons.append("Low confidence")
        elif confidence < 60:
            reasons.append("Needs more practice")
        
        if progress and not progress.mastered:
            if progress.quests_completed < progress.quests_total:
                reasons.append(f"Only {progress.quests_completed}/{progress.quests_total} problems solved")
        
        result.append({
            "pattern_id": pattern_id,
            "title": pattern_data.get("title", pattern_id.replace("_", " ").title()),
            "confidence": confidence,
            "reasons": reasons or ["Could use more practice"],
            "has_syllabus": bool(pattern_data.get("concepts")),
        })
    
    # Sort by confidence (ascending) and take top N
    result.sort(key=lambda p: p["confidence"])
    result = result[:limit]
    
    return ToolResult(
        success=True,
        data=result,
        message=f"Found {len(result)} patterns that need work",
    )


@tool(
    name="get_next_essential_quest",
    description="Get the next essential practice problem for a pattern that hasn't been completed yet.",
    category="patterns",
)
async def get_next_essential_quest(
    db: Database,
    pattern_id: str,
    user_id: str = "default",
) -> ToolResult:
    """
    Get the next uncompleted essential quest for a pattern.
    
    :param pattern_id: The pattern identifier
    :return: Next quest details or null if all completed
    """
    pattern_meta = _get_pattern_metadata(pattern_id)
    if not pattern_meta:
        return ToolResult(
            success=False,
            error=f"Pattern '{pattern_id}' not found",
        )
    
    essential_ids = pattern_meta.get("essential_questions", [])
    if not essential_ids:
        return ToolResult(
            success=True,
            data=None,
            message="No essential questions defined for this pattern",
        )
    
    # Get completed quests
    completed = await db.get_completed_quests(user_id, pattern_id)
    completed_ids = {c.quest_id for c in completed}
    
    # Find first uncompleted essential quest
    all_quests = _get_all_quests_for_pattern(pattern_id)
    
    for quest_id in essential_ids:
        if quest_id not in completed_ids:
            quest = next((q for q in all_quests if q["id"] == quest_id), None)
            if quest:
                return ToolResult(
                    success=True,
                    data={
                        "quest_id": quest_id,
                        "title": quest.get("title", quest_id),
                        "difficulty": quest.get("difficulty", "medium"),
                        "link": quest.get("link", ""),
                        "pattern": pattern_id,
                    },
                )
    
    # All essential quests completed
    return ToolResult(
        success=True,
        data=None,
        message=f"All essential quests for {pattern_id} are completed! Pattern mastered!",
    )



