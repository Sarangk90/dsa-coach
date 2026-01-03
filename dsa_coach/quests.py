from __future__ import annotations

from typing import Any

from . import paths
from .storage import load_json


def get_all_quests() -> list[dict[str, Any]]:
    """
    Get flat list of all quests (problems).

    For backward compatibility, this now delegates to curriculum module.
    """
    # Import here to avoid circular dependency
    from .curriculum import get_all_problems
    from .storage.sync import SyncDatabase

    # Get active mode from database profile
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        mode = profile.active_mode if hasattr(profile, 'active_mode') and profile.active_mode else "fast_track"

    return get_all_problems(mode)


def get_curriculum_mode(mode: str) -> list[dict[str, Any]]:
    """Get curriculum for a mode (fast_track or complete)."""
    from .curriculum import get_curriculum
    return get_curriculum(mode)


def get_pattern_by_id(pattern_id: str, mode: str) -> dict[str, Any] | None:
    """Get pattern details by pattern_id."""
    from .curriculum import get_pattern_by_id as _get_pattern
    return _get_pattern(pattern_id, mode)


def get_concept_by_id(pattern_id: str, concept_id: str, mode: str) -> dict[str, Any] | None:
    """Get concept details by pattern_id and concept_id."""
    from .curriculum import get_concept_by_id as _get_concept
    return _get_concept(pattern_id, concept_id, mode)


def get_problem_by_id(problem_id: str, mode: str) -> dict[str, Any] | None:
    """Get problem details (the new 'quest')."""
    from .curriculum import get_problem_by_id as _get_problem
    return _get_problem(problem_id, mode)


def get_all_problems(mode: str) -> list[dict[str, Any]]:
    """Get flat list of all problems for a mode."""
    from .curriculum import get_all_problems as _get_all
    return _get_all(mode)



