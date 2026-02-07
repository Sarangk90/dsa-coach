"""Quest and curriculum helper functions for DSA Coach tools."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .. import paths
from ..curriculum import get_curriculum, get_curriculum_data, get_pattern_by_id
from ..id_mappings import get_new_pattern_id, get_new_problem_id, is_old_format_id

if TYPE_CHECKING:
    from ..storage.db import Database


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
    data = get_curriculum_data()

    # First pass: exact ID match
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = data.get("curriculum", {}).get(curriculum_mode, [])
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
        curriculum = data.get("curriculum", {}).get(curriculum_mode, [])
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
    data = get_curriculum_data()
    quest_id_lower = quest_id.lower()

    # Extract key words from the quest_id
    words = set(quest_id_lower.replace("_", " ").replace("-", " ").split())

    # Find quests with overlapping words
    matches = []
    for curriculum_mode in ["fast_track", "complete"]:
        curriculum = data.get("curriculum", {}).get(curriculum_mode, [])
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
    """Get pattern details from V2 curriculum structure (checks multiple modes)."""
    for curriculum_mode in [mode, "fast_track", "complete"]:
        result = get_pattern_by_id(pattern_id, curriculum_mode)
        if result is not None:
            return result
    return None


def _get_curriculum(mode: str = "fast_track") -> list[dict]:
    """Get curriculum patterns for a specific mode."""
    return get_curriculum(mode)


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
    for mode in ["fast_track", "complete"]:
        pattern = get_pattern_by_id(pattern_id, mode)
        if pattern:
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
    for curriculum_mode in [mode, "fast_track", "complete"]:
        pattern = get_pattern_by_id(pattern_id, curriculum_mode)
        if pattern:
            return [
                c.get("concept_name", c.get("concept_id", ""))
                for c in pattern.get("concepts", [])
            ]
    return []


def _get_solutions_dir() -> Path:
    """Get the solutions directory path."""
    return paths.SOLUTIONS_DIR


def should_create_note(
    pattern: str,
    progress: float,
    session_messages: int,
    progress_gain: float,
) -> tuple[bool, str]:
    """Determine if a pattern note should be created after a learning session.

    Args:
        pattern: Pattern name
        progress: Current progress level
        session_messages: Number of messages in session
        progress_gain: Progress increase from session

    Returns:
        (should_create: bool, reason: str)
    """
    # Don't create note if session was too short
    if session_messages < 4:
        return (False, "Session too short (< 4 messages)")

    # Create note if progress is now above threshold (pattern understood)
    if progress >= 40 and progress_gain > 10:
        return (
            True,
            f"Pattern learned (progress: {progress:.0f}%, gain: +{progress_gain:.0f}%)",
        )

    # Create note if session was substantial even if progress is still low
    if session_messages >= 10:
        return (True, f"Substantial session ({session_messages} messages)")

    return (False, "Session didn't meet thresholds for note creation")
