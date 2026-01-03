"""Quest selection logic with prerequisite checking and intelligent prioritization."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .curriculum import (
    get_active_mode,
    get_all_problems,
    get_next_review_patterns,
    get_pattern_by_id,
    get_problems_for_pattern,
    get_unlocked_patterns,
    is_pattern_unlocked,
)


def get_next_quest(progress: dict[str, Any]) -> dict[str, Any] | None:
    """
    Get the optimal next quest (problem) based on progress.
    
    Priority order:
    1. Spaced repetition - patterns due for review
    2. Continue current pattern/concept
    3. Weakest unlocked pattern (lowest time investment)
    4. Next pattern in sequence order
    """
    mode = get_active_mode(progress)
    completed_problem_ids = set(progress.get("problems_solved", {}).keys())
    
    # Priority 1: Spaced repetition items due today
    due_reviews = get_next_review_patterns(progress)
    if due_reviews:
        for review_item in due_reviews:
            pattern_id = review_item.get("pattern_id")
            # Return first uncompleted problem from this pattern
            pattern_problems = get_problems_for_pattern(pattern_id, mode)
            for problem in pattern_problems:
                if problem.get("problem_id") not in completed_problem_ids:
                    return problem
    
    # Priority 2: Continue current pattern/concept
    current_pattern_id = progress.get("profile", {}).get("current_pattern_id")
    current_concept_id = progress.get("profile", {}).get("current_concept_id")
    
    if current_pattern_id and current_concept_id:
        pattern = get_pattern_by_id(current_pattern_id, mode)
        if pattern:
            # Find the current concept and get next problem
            for concept in pattern.get("concepts", []):
                if concept.get("concept_id") == current_concept_id:
                    for problem in concept.get("practice_problems", []):
                        if problem.get("problem_id") not in completed_problem_ids:
                            # Enrich with pattern/concept info
                            return {
                                **problem,
                                "pattern_id": current_pattern_id,
                                "pattern_name": pattern.get("pattern_name"),
                                "concept_id": current_concept_id,
                                "concept_name": concept.get("concept_name"),
                            }
    
    # Priority 3: Weakest unlocked pattern (lowest time investment)
    unlocked = get_unlocked_patterns(mode, progress)
    completed_patterns = set(progress.get("patterns_completed", []))
    
    # Filter out completed patterns
    incomplete_unlocked = [p for p in unlocked if p.get("pattern_id") not in completed_patterns]
    
    if incomplete_unlocked:
        # Sort by time spent (ascending) - focus on patterns with least investment
        time_by_pattern = progress.get("time_spent_hours", {}).get("by_pattern", {})
        
        def get_time_spent(pattern: dict) -> float:
            return time_by_pattern.get(pattern.get("pattern_id"), 0.0)
        
        sorted_patterns = sorted(incomplete_unlocked, key=get_time_spent)
        
        # Get first uncompleted problem from weakest pattern
        for pattern in sorted_patterns:
            pattern_id = pattern.get("pattern_id")
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    if problem.get("problem_id") not in completed_problem_ids:
                        # Enrich with pattern/concept info
                        return {
                            **problem,
                            "pattern_id": pattern_id,
                            "pattern_name": pattern.get("pattern_name"),
                            "concept_id": concept.get("concept_id"),
                            "concept_name": concept.get("concept_name"),
                        }
    
    # Priority 4: Next pattern in sequence order (all unlocked patterns exhausted)
    # This shouldn't happen often, but handles edge cases
    all_problems = get_all_problems(mode)
    for problem in all_problems:
        problem_id = problem.get("problem_id")
        pattern_id = problem.get("pattern_id")
        
        # Check if pattern is unlocked and problem not completed
        if (problem_id not in completed_problem_ids and 
            is_pattern_unlocked(pattern_id, progress, mode)):
            return problem
    
    # No quests available
    return None


def get_next_quest_for_pattern(pattern_id: str, progress: dict[str, Any]) -> dict[str, Any] | None:
    """Get the next uncompleted problem for a specific pattern."""
    mode = get_active_mode(progress)
    completed_problem_ids = set(progress.get("problems_solved", {}).keys())
    
    pattern_problems = get_problems_for_pattern(pattern_id, mode)
    for problem in pattern_problems:
        if problem.get("problem_id") not in completed_problem_ids:
            return problem
    
    return None
