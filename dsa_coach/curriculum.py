"""Curriculum management: pattern unlocking, mastery tracking, and progression logic."""
from __future__ import annotations

from datetime import datetime
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


def get_active_mode(progress: dict[str, Any]) -> str:
    """Get the active curriculum mode from progress."""
    return progress.get("profile", {}).get("active_mode", "fast_track")


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

    Handles both V2 IDs (ft_02) and V1 legacy names (sliding_window).

    Examples:
        ft_02 -> "Arrays & Hashing"
        ft_04 -> "Sliding Window"
        sliding_window -> "Sliding Window"

    Falls back to title-cased pattern_id if not found.
    """
    # Try V2 lookup first
    pattern = get_pattern_by_id(pattern_id, mode)
    if pattern:
        return pattern.get("pattern_name", pattern_id)

    # V1 legacy: format nicely (sliding_window -> Sliding Window)
    return pattern_id.replace("_", " ").title()


def get_problem_name(problem_id: str, mode: str = "fast_track") -> str:
    """
    Get human-readable problem name from problem_id.

    Handles both V2 IDs (ft_02_c1_p1) and V1 legacy IDs (two_sum).

    Examples:
        ft_02_c1_p1 -> "Two Sum"
        ft_04_c1_p1 -> "Longest Substring Without Repeating Characters"
        max_consecutive_ones -> "Max Consecutive Ones"
        two_sum_ii -> "Two Sum II"

    Falls back to title-cased problem_id if not found.
    """
    # Try V2 lookup first
    problem = get_problem_by_id(problem_id, mode)
    if problem:
        return problem.get("problem_name", problem_id)

    # V1 legacy: format nicely (max_consecutive_ones -> Max Consecutive Ones)
    return problem_id.replace("_", " ").title()


def is_pattern_unlocked(pattern_id: str, progress: dict[str, Any], mode: str) -> bool:
    """
    Check if a pattern is unlocked based on prerequisites.
    
    A pattern is unlocked if:
    - It has no prerequisites, OR
    - All prerequisites are in progress['patterns_completed'], OR
    - All prerequisites with no problems are auto-completed
    """
    pattern = get_pattern_by_id(pattern_id, mode)
    if not pattern:
        return False
    
    prerequisites = pattern.get("prerequisites", [])
    if not prerequisites:
        return True
    
    completed_patterns = set(progress.get("patterns_completed", []))
    
    # Check each prerequisite
    for prereq_id in prerequisites:
        if prereq_id in completed_patterns:
            continue
        
        # Check if prerequisite has no problems (theory-only) - auto-complete it
        prereq_pattern = get_pattern_by_id(prereq_id, mode)
        if prereq_pattern:
            has_problems = False
            for concept in prereq_pattern.get("concepts", []):
                if concept.get("practice_problems", []):
                    has_problems = True
                    break
            
            if not has_problems:
                # Theory-only pattern - auto-complete it
                if prereq_id not in progress.get("patterns_completed", []):
                    progress.setdefault("patterns_completed", []).append(prereq_id)
                continue
        
        # Prerequisite not completed
        return False
    
    return True


def get_unlocked_patterns(mode: str, progress: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all patterns that the user can currently start."""
    curriculum = get_curriculum(mode)
    unlocked = []
    
    for pattern in curriculum:
        pattern_id = pattern.get("pattern_id")
        if is_pattern_unlocked(pattern_id, progress, mode):
            unlocked.append(pattern)
    
    return unlocked


def get_pattern_status(pattern_id: str, progress: dict[str, Any], mode: str) -> str:
    """
    Get the status of a pattern.
    
    Returns: 'locked', 'unlocked', 'in_progress', or 'completed'
    """
    if pattern_id in progress.get("patterns_completed", []):
        return "completed"
    
    if pattern_id in progress.get("patterns_in_progress", []):
        return "in_progress"
    
    if is_pattern_unlocked(pattern_id, progress, mode):
        return "unlocked"
    
    return "locked"


def get_concept_by_id(pattern_id: str, concept_id: str, mode: str) -> dict[str, Any] | None:
    """Get concept details by pattern_id and concept_id."""
    pattern = get_pattern_by_id(pattern_id, mode)
    if not pattern:
        return None
    
    for concept in pattern.get("concepts", []):
        if concept.get("concept_id") == concept_id:
            return concept
    
    return None


def check_concept_complete(pattern_id: str, concept_id: str, progress: dict[str, Any], mode: str) -> bool:
    """Check if all problems in a concept are solved."""
    concept = get_concept_by_id(pattern_id, concept_id, mode)
    if not concept:
        return False
    
    problems_solved = set(progress.get("problems_solved", {}).keys())
    
    for problem in concept.get("practice_problems", []):
        problem_id = problem.get("problem_id")
        if problem_id not in problems_solved:
            return False
    
    return True


def check_pattern_mastery(pattern_id: str, progress: dict[str, Any], mode: str) -> tuple[bool, list[str]]:
    """
    Validate mastery_criteria for a pattern.
    
    Returns: (is_mastered, list_of_unmet_criteria)
    """
    pattern = get_pattern_by_id(pattern_id, mode)
    if not pattern:
        return False, ["Pattern not found"]
    
    mastery_criteria = pattern.get("mastery_criteria", {})
    if not mastery_criteria:
        # If no criteria defined, just check if all problems are solved
        return check_all_problems_complete(pattern_id, progress, mode), []
    
    unmet_criteria = []
    problems_solved = progress.get("problems_solved", {})
    
    for criterion, requirement in mastery_criteria.items():
        if isinstance(requirement, bool):
            # Boolean criteria - assume met if pattern is being checked for completion
            # These would be validated through other means (e.g., user confirmation)
            continue
        elif isinstance(requirement, int):
            # Count-based criteria (e.g., solved_two_sum_variants: 2)
            # Try to find matching problems
            count = 0
            for problem_id in problems_solved:
                # Simple heuristic: check if criterion keyword appears in problem_id
                if criterion.replace("_", " ").lower() in problem_id.replace("_", " ").lower():
                    count += 1
            
            if count < requirement:
                unmet_criteria.append(f"{criterion}: {count}/{requirement}")
    
    return len(unmet_criteria) == 0, unmet_criteria


def check_all_problems_complete(pattern_id: str, progress: dict[str, Any], mode: str) -> bool:
    """Check if all problems in all concepts of a pattern are solved."""
    pattern = get_pattern_by_id(pattern_id, mode)
    if not pattern:
        return False
    
    for concept in pattern.get("concepts", []):
        concept_id = concept.get("concept_id")
        if not check_concept_complete(pattern_id, concept_id, progress, mode):
            return False
    
    return True


def get_next_review_patterns(progress: dict[str, Any]) -> list[dict[str, Any]]:
    """Get patterns due for spaced repetition review."""
    due_reviews = []
    now = datetime.now()
    
    for item in progress.get("spaced_repetition_queue", []):
        due_date = datetime.fromisoformat(item.get("due", ""))
        if due_date <= now:
            due_reviews.append(item)
    
    return due_reviews


def unlock_dependent_patterns(completed_pattern_id: str, progress: dict[str, Any], mode: str) -> list[str]:
    """
    Return newly unlocked pattern IDs after completing a pattern.
    
    Checks the 'unlocks' array of the completed pattern.
    """
    pattern = get_pattern_by_id(completed_pattern_id, mode)
    if not pattern:
        return []
    
    unlocks = pattern.get("unlocks", [])
    newly_unlocked = []
    
    for unlocked_id in unlocks:
        if is_pattern_unlocked(unlocked_id, progress, mode):
            newly_unlocked.append(unlocked_id)
    
    return newly_unlocked


def add_pattern_to_spaced_repetition(
    pattern_id: str, 
    progress: dict[str, Any], 
    mode: str
) -> None:
    """Add a completed pattern to the spaced repetition queue."""
    pattern = get_pattern_by_id(pattern_id, mode)
    if not pattern:
        return
    
    review_schedule = pattern.get("review_schedule_days", [3, 7, 14, 30])
    
    # Add the first review
    if review_schedule:
        first_review_days = review_schedule[0]
        due_date = datetime.now()
        from datetime import timedelta
        due_date = due_date + timedelta(days=first_review_days)
        
        progress.setdefault("spaced_repetition_queue", []).append({
            "pattern_id": pattern_id,
            "due": due_date.isoformat(),
            "review_index": 0,
            "schedule": review_schedule
        })


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


def get_all_problems(mode: str) -> list[dict[str, Any]]:
    """Get flat list of all problems for a mode (for backward compatibility)."""
    curriculum = get_curriculum(mode)
    all_problems = []
    
    for pattern in curriculum:
        for concept in pattern.get("concepts", []):
            for problem in concept.get("practice_problems", []):
                # Enrich with pattern and concept info
                enriched_problem = {
                    **problem,
                    "pattern_id": pattern.get("pattern_id"),
                    "pattern_name": pattern.get("pattern_name"),
                    "concept_id": concept.get("concept_id"),
                    "concept_name": concept.get("concept_name"),
                }
                all_problems.append(enriched_problem)
    
    return all_problems


def get_problems_for_pattern(pattern_id: str, mode: str) -> list[dict[str, Any]]:
    """Get all problems for a specific pattern."""
    pattern = get_pattern_by_id(pattern_id, mode)
    if not pattern:
        return []
    
    problems = []
    for concept in pattern.get("concepts", []):
        for problem in concept.get("practice_problems", []):
            enriched_problem = {
                **problem,
                "pattern_id": pattern_id,
                "pattern_name": pattern.get("pattern_name"),
                "concept_id": concept.get("concept_id"),
                "concept_name": concept.get("concept_name"),
            }
            problems.append(enriched_problem)
    
    return problems

