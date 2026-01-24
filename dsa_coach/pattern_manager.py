from typing import Any

from dsa_coach import paths
from dsa_coach.curriculum import get_curriculum
from dsa_coach.quests import get_all_problems
from dsa_coach.storage import load_json
from dsa_coach.storage.sync import SyncDatabase


class PatternManager:
    """Manager for pattern-based curriculum (V2 structure)."""

    patterns_by_id: dict[str, dict[str, Any]]
    mode: str

    def __init__(self, mode: str = "fast_track"):
        """
        Initialize pattern manager with V2 curriculum.

        Args:
            mode: Curriculum mode (fast_track or complete)
        """
        self.mode = mode
        self.quests_data = load_json(paths.QUESTS_FILE)

        # Load patterns from V2 curriculum
        curriculum = get_curriculum(mode)
        self.patterns_by_id = {p["pattern_id"]: p for p in curriculum}

        # Load from database
        with SyncDatabase() as db:
            profile = db.get_or_create_profile()
            # Use mode from profile if available
            if hasattr(profile, "active_mode") and profile.active_mode:
                self.mode = profile.active_mode
                curriculum = get_curriculum(self.mode)
                self.patterns_by_id = {p["pattern_id"]: p for p in curriculum}

            self._completed_quest_ids = {c.quest_id for c in db.get_completed_quests()}
            self._pattern_progress = {
                p.pattern_id: p for p in db.get_all_pattern_progress()
            }

        # Get all problems for the mode
        self.all_quests = get_all_problems(self.mode)

    def get_pattern_syllabus(self, pattern: str) -> dict[str, Any]:
        """
        Get the syllabus for a pattern from V2 curriculum.

        Returns:
            - title: Pattern name
            - description: Pattern tier and time
            - concepts: List of concept objects
            - total_problems: Count of practice problems
        """
        pattern_data = self.patterns_by_id.get(pattern)
        if not pattern_data:
            return {}

        concepts = pattern_data.get("concepts", [])
        total_problems = sum(len(c.get("practice_problems", [])) for c in concepts)

        return {
            "title": pattern_data.get("pattern_name", pattern),
            "description": f"{pattern_data.get('tier', 'foundation').title()} - {pattern_data.get('estimated_time_hours', 0)}h",
            "concepts": [
                c.get("concept_name", c.get("concept_id", "")) for c in concepts
            ],
            "total_problems": total_problems,
            "tier": pattern_data.get("tier", "foundation"),
            "estimated_time_hours": pattern_data.get("estimated_time_hours", 0),
        }

    def get_pattern_status(self, pattern: str) -> dict[str, Any]:
        """
        Get detailed status of a pattern (V2 version).

        Returns:
            - progress: User progress (0-100)
            - essential_total: Total practice problems
            - essential_done_count: Completed problems
            - essential_done_ids: List of completed problem IDs
            - next_quest: Next uncompleted problem (dict or None)
            - is_mastered: Whether pattern is mastered
        """
        # Get all problems for this pattern
        pattern_quests = [q for q in self.all_quests if q.get("pattern_id") == pattern]

        # Find completed problems
        done_problems = [
            q["problem_id"]
            for q in pattern_quests
            if q["problem_id"] in self._completed_quest_ids
        ]

        # Find next uncompleted problem
        next_quest = None
        for quest in pattern_quests:
            if quest["problem_id"] not in self._completed_quest_ids:
                next_quest = quest
                break

        # Get progress from pattern progress
        pattern_prog = self._pattern_progress.get(pattern)
        current_progress = pattern_prog.progress if pattern_prog else 0
        is_mastered = pattern_prog.mastered if pattern_prog else False

        return {
            "progress": current_progress,
            "essential_total": len(pattern_quests),
            "essential_done_count": len(done_problems),
            "essential_done_ids": done_problems,
            "next_quest": next_quest,
            "is_mastered": is_mastered,
        }
