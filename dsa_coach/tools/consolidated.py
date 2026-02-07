"""Consolidated tools — backward-compatible re-export facade.

All 13 workflow-level tools are defined in their category modules:
- session_quest.py: get_dashboard, start_quest, complete_quest, get_hint
- pattern_learning.py: list_patterns, get_pattern_details, diagnose_understanding, record_learning, get_teaching_context
- progress_review.py: get_progress_summary, record_review, manage_solution, review_code
"""

from .pattern_learning import (
    diagnose_understanding,
    get_pattern_details,
    get_teaching_context,
    list_patterns,
    record_learning,
)
from .progress_review import (
    get_progress_summary,
    manage_solution,
    record_review,
    review_code,
)
from .session_quest import complete_quest, get_dashboard, get_hint, start_quest

__all__ = [
    "get_dashboard",
    "start_quest",
    "complete_quest",
    "get_hint",
    "list_patterns",
    "get_pattern_details",
    "diagnose_understanding",
    "record_learning",
    "get_teaching_context",
    "get_progress_summary",
    "record_review",
    "manage_solution",
    "review_code",
]
