from typing import Optional, Any
from dsa_coach.storage import load_json
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.quests import get_all_quests
from dsa_coach import paths


class PatternManager:
    def __init__(self):
        self.quests_data = load_json(paths.QUESTS_FILE)
        self.patterns_config = self.quests_data.get("metadata", {}).get("patterns", {})
        # Handle case where patterns might still be a list (backward compatibility)
        if isinstance(self.patterns_config, list):
            self.patterns_config = {p: {"title": p.replace("_", " ").title()} for p in self.patterns_config}

        # Load from database
        with SyncDatabase() as db:
            self._completed_quest_ids = {c.quest_id for c in db.get_completed_quests()}
            self._pattern_progress = {p.pattern_id: p for p in db.get_all_pattern_progress()}

        self.all_quests = get_all_quests()

    def get_pattern_syllabus(self, pattern: str) -> dict[str, Any]:
        """Get the syllabus (concepts, essential questions) for a pattern."""
        return self.patterns_config.get(pattern, {})

    def get_pattern_status(self, pattern: str) -> dict[str, Any]:
        """
        Get detailed status of a pattern.
        Returns:
            - confidence
            - essential_total
            - essential_done_count
            - essential_done_ids
            - next_quest (dict or None)
            - is_mastered
        """
        syllabus = self.get_pattern_syllabus(pattern)
        essential_ids = syllabus.get("essential_questions", [])

        done_essential = [qid for qid in essential_ids if qid in self._completed_quest_ids]

        next_quest_id = None
        for qid in essential_ids:
            if qid not in self._completed_quest_ids:
                next_quest_id = qid
                break

        # Find the full quest object for next_quest_id
        next_quest = None
        if next_quest_id:
            next_quest = next((q for q in self.all_quests if q["id"] == next_quest_id), None)

        # Get confidence from pattern progress
        pattern_prog = self._pattern_progress.get(pattern)
        confidence = pattern_prog.confidence if pattern_prog else 0

        return {
            "confidence": confidence,
            "essential_total": len(essential_ids),
            "essential_done_count": len(done_essential),
            "essential_done_ids": done_essential,
            "next_quest": next_quest,
            "is_mastered": len(done_essential) == len(essential_ids) and len(essential_ids) > 0
        }



