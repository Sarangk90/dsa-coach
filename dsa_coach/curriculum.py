"""Curriculum management: quest and pattern lookup."""

from __future__ import annotations

from typing import Any

from . import paths
from .storage import load_json


def get_curriculum_data() -> dict[str, Any]:
    """Load the full curriculum data from quests.json (V2 structure only)."""
    data = load_json(paths.QUESTS_FILE)

    # Ensure V2 structure
    assert "curriculum" in data, "Expected V2 quest structure with 'curriculum' key"
    assert "quests" not in data, "V1 'quests' array no longer supported"
    assert "days" not in data, "V1 'days' structure no longer supported"

    return data


def get_curriculum(mode: str) -> list[dict[str, Any]]:
    """Get curriculum patterns for a specific mode."""
    data = get_curriculum_data()
    return data.get("curriculum", {}).get(mode, [])


def get_pattern_by_id(pattern_id: str, mode: str) -> dict[str, Any] | None:
    """Get pattern details by pattern_id."""
    curriculum = get_curriculum(mode)
    for pattern in curriculum:
        if pattern.get("pattern_id") == pattern_id:
            return pattern
    return None


def get_pattern_name(pattern_id: str, mode: str = "fast_track") -> str:
    """
    Get human-readable pattern name from pattern_id.

    Pattern IDs use human-readable slugs (e.g., sliding_window, arrays_hashing).

    Examples:
        arrays_hashing -> "Arrays & Hashing"
        sliding_window -> "Sliding Window"
        two_pointers -> "Two Pointers"

    Falls back to title-cased pattern_id if not found.
    """
    pattern = get_pattern_by_id(pattern_id, mode)
    if pattern:
        return pattern.get("pattern_name", pattern_id)

    # Fallback: format nicely (sliding_window -> Sliding Window)
    return pattern_id.replace("_", " ").title()


def get_problem_by_id(problem_id: str, mode: str) -> dict[str, Any] | None:
    """Get problem details by problem_id."""
    curriculum = get_curriculum(mode)

    for pattern in curriculum:
        for concept in pattern.get("concepts", []):
            for problem in concept.get("practice_problems", []):
                if problem.get("problem_id") == problem_id:
                    # Enrich with pattern and concept info
                    return {
                        **problem,
                        "pattern_id": pattern.get("pattern_id"),
                        "pattern_name": pattern.get("pattern_name"),
                        "concept_id": concept.get("concept_id"),
                        "concept_name": concept.get("concept_name"),
                    }

    return None


def get_problem_name(problem_id: str, mode: str = "fast_track") -> str:
    """
    Get human-readable problem name from problem_id.

    Problem IDs use human-readable slugs: <pattern_slug>_<problem_slug>
    (e.g., arrays_hashing_two_sum, sliding_window_minimum_window_substring).

    Examples:
        arrays_hashing_two_sum -> "Two Sum"
        sliding_window_longest_substring_without_repeating -> "Longest Substring Without Repeating Characters"
        two_pointers_3sum -> "3Sum"

    Falls back to title-cased problem_id if not found.
    """
    problem = get_problem_by_id(problem_id, mode)
    if problem:
        return problem.get("problem_name", problem_id)

    # Fallback: format nicely (arrays_hashing_two_sum -> Arrays Hashing Two Sum)
    return problem_id.replace("_", " ").title()
