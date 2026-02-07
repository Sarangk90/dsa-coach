"""Regression tests for student-context prompt helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dsa_coach.ai import prompts
from dsa_coach.ai import student_context as student_context_mod


def test_format_mastery_snapshot_sorts_and_labels_levels():
    patterns = [
        SimpleNamespace(pattern_id="graphs", progress=35),
        SimpleNamespace(pattern_id="arrays_hashing", progress=85),
        SimpleNamespace(pattern_id="trees", progress=60),
        SimpleNamespace(pattern_id="dp", progress=20),
    ]

    formatted = prompts._format_mastery_snapshot(patterns)  # noqa: SLF001
    lines = formatted.splitlines()

    assert "Arrays Hashing: 85% (MASTERED)" in lines[0]
    assert "Trees: 60% (PROFICIENT)" in lines[1]
    assert any("(DEVELOPING)" in line for line in lines)
    assert any("(BEGINNER)" in line for line in lines)


def test_format_helpers_cover_none_and_mixed_input_shapes():
    assert prompts._format_current_session(None) == "No active session."  # noqa: SLF001

    session = SimpleNamespace(
        session_type="practice",
        current_pattern="sliding_window",
        current_quest="q1",
    )
    current = prompts._format_current_session(session)  # noqa: SLF001
    assert "Type: practice" in current
    assert "Pattern: Sliding Window" in current
    assert "Quest: q1" in current

    mistakes = prompts._format_mistakes(  # noqa: SLF001
        [{"type": "off_by_one", "count": 3, "patterns": ["arrays_hashing"]}]
    )
    assert "Off By One (x3)" in mistakes

    due = prompts._format_due_reviews(  # noqa: SLF001
        [
            SimpleNamespace(quest_id="q1", pattern_id="graphs"),
            {"quest_id": "q2", "pattern_id": "trees"},
        ]
    )
    assert "q1 (Graphs)" in due
    assert "q2 (Trees)" in due

    assert (
        prompts._get_current_slice(  # noqa: SLF001
            {
                "slice-1": {"done": 2, "total": 2},
                "slice-2": {"done": 1, "total": 3},
                "slice-3": {"done": 0, "total": 4},
            }
        )
        == "SLICE-2"
    )


@pytest.mark.asyncio
async def test_compute_slice_progress_handles_missing_file(monkeypatch, tmp_path):
    fake_prompts = tmp_path / "pkg" / "dsa_coach" / "ai" / "student_context.py"
    fake_prompts.parent.mkdir(parents=True, exist_ok=True)
    fake_prompts.write_text("# placeholder")
    monkeypatch.setattr(student_context_mod, "__file__", str(fake_prompts))

    class FakeDB:
        async def get_completed_quests(self, _user_id):
            return []

    result = await prompts._compute_slice_progress(FakeDB(), "u1")  # noqa: SLF001
    assert result == {
        "slice-1": {"total": 0, "done": 0},
        "slice-2": {"total": 0, "done": 0},
        "slice-3": {"total": 0, "done": 0},
    }


@pytest.mark.asyncio
async def test_compute_slice_progress_reads_slice_tags(monkeypatch, tmp_path):
    fake_prompts = tmp_path / "dsa_coach" / "ai" / "student_context.py"
    fake_prompts.parent.mkdir(parents=True, exist_ok=True)
    fake_prompts.write_text("# placeholder")

    quests = tmp_path / "quests.json"
    quests.write_text(
        """
{
  "curriculum": {
    "fast_track": [
      {
        "pattern_id": "arrays_hashing",
        "concepts": [
          {
            "practice_problems": [
              {"problem_id": "q_slice_1", "tags": ["slice-1"]},
              {"problem_id": "q_slice_2", "tags": ["slice-2"]}
            ]
          }
        ]
      }
    ]
  }
}
""".strip()
    )

    monkeypatch.setattr(student_context_mod, "__file__", str(fake_prompts))

    class FakeDB:
        async def get_completed_quests(self, _user_id):
            return [SimpleNamespace(quest_id="q_slice_1")]

    result = await prompts._compute_slice_progress(FakeDB(), "u1")  # noqa: SLF001
    assert result["slice-1"] == {"total": 1, "done": 1}
    assert result["slice-2"] == {"total": 1, "done": 0}
    assert result["slice-3"] == {"total": 0, "done": 0}


@pytest.mark.asyncio
async def test_build_student_context_includes_key_sections(monkeypatch):
    class FakeDB:
        async def get_or_create_profile(self, _user_id):
            return SimpleNamespace(name="Alice")

        async def get_all_pattern_progress(self, _user_id):
            return [SimpleNamespace(pattern_id="graphs", progress=65)]

        async def get_due_reviews(self, _user_id):
            return [SimpleNamespace(quest_id="q1", pattern_id="graphs")]

        async def get_recent_mistakes(self, _user_id, limit=5):
            return []

        async def get_recurring_mistake_types(self, _user_id):
            return [{"type": "edge_case", "count": 2, "patterns": ["graphs"]}]

        async def get_struggling_concepts(self, _user_id):
            return [{"pattern_id": "graphs", "concept": "cycle detection"}]

        async def get_mastered_concepts(self, _user_id):
            return [{"pattern_id": "arrays_hashing", "concept": "hash map lookup"}]

        async def get_recent_milestones(self, _user_id, days=7):
            return [{"description": "Mastered Arrays", "achieved_at": "2026-02-01"}]

        async def get_latest_session(self, _user_id):
            return SimpleNamespace(
                session_type="practice",
                current_pattern="graphs",
                current_quest="q1",
            )

        async def get_weekly_activity(self, _user_id):
            return {
                "problems_solved": 4,
                "time_spent_mins": 125,
                "patterns_worked": ["graphs", "arrays_hashing"],
            }

    async def fake_slice_progress(_db, _user_id):
        return {
            "slice-1": {"done": 3, "total": 3},
            "slice-2": {"done": 1, "total": 4},
            "slice-3": {"done": 0, "total": 5},
        }

    monkeypatch.setattr(
        student_context_mod, "_compute_slice_progress", fake_slice_progress
    )

    context = await prompts.build_student_context(FakeDB(), "u1")
    assert "YOUR STUDENT: Alice" in context
    assert "Current Focus: SLICE-2" in context
    assert "Mastered Arrays (2026-02-01)" in context
    assert "edge_case".replace("_", " ").title() in context


def test_get_agent_system_prompt_prioritizes_student_context_then_dashboard():
    custom = prompts.get_agent_system_prompt(
        dashboard_state={"profile": {"name": "Ignored"}},
        student_context="CUSTOM STUDENT CONTEXT",
    )
    assert custom.endswith("CUSTOM STUDENT CONTEXT")

    dashboard = prompts.get_agent_system_prompt(
        dashboard_state={
            "profile": {
                "name": "Bob",
                "quests_completed": 9,
                "created_at": "2026-01-01",
            },
            "current_quest": {"title": "Two Sum"},
            "alerts": [{"type": "review"}],
        },
        student_context=None,
    )
    assert "CURRENT SESSION CONTEXT" in dashboard
    assert "User: Bob" in dashboard
    assert "Current Quest: Two Sum" in dashboard
