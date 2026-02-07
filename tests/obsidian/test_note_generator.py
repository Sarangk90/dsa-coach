"""Regression tests for Obsidian note generation helpers."""

from __future__ import annotations

from dsa_coach.obsidian import note_generator as ng


def test_filename_helpers_sanitize_and_append_md():
    assert ng._sanitize_filename("Sliding Window") == "sliding-window"  # noqa: SLF001
    assert ng.get_filename_for_pattern("two_pointers") == "two-pointers.md"
    assert (
        ng.get_filename_for_problem("arrays_hashing_two_sum")
        == "arrays-hashing-two-sum.md"
    )


def test_generate_pattern_note_includes_optional_sections_and_links():
    note = ng.generate_pattern_note(
        pattern="sliding_window",
        title="Sliding Window",
        description="Window technique.",
        why_matters="Shows optimization thinking.",
        trade_offs=[
            {"aspect": "Time", "description": "Linear scan", "when_to_use": "Need O(n)"}
        ],
        code_example="def solve(nums):\n    return len(nums)",
        code_explanation="Maintain an invariant window.",
        sixty_second_pitch="Track bounds and update fast.",
        key_terminology=["invariant", "amortized"],
        follow_up_questions=["Why does this stay O(n)?"],
        common_pitfalls=["Forgetting to shrink"],
        companies=["Google"],
        use_cases=["Rate limiting"],
        related_patterns=[{"name": "Two Pointers", "context": "Adjacent technique"}],
        has_diagram=True,
    )

    assert "title: Sliding Window" in note
    assert "## Core Concept" in note
    assert "## Visual Model" in note
    assert "## Key Trade-offs" in note
    assert "## Interview Articulation Guide" in note
    assert "## Real-World Usage" in note
    assert "[[two-pointers|Two Pointers]]" in note


def test_generate_pattern_note_adds_length_guidance_markers():
    short_note = ng.generate_pattern_note(
        pattern="graphs",
        title="Graphs",
        description="Short",
        why_matters="Short",
        trade_offs=[],
        code_example="pass",
        code_explanation="Short",
        sixty_second_pitch="Short",
        key_terminology=[],
        follow_up_questions=[],
        common_pitfalls=[],
        has_diagram=False,
    )
    assert "Consider expanding this note" in short_note

    long_lines = "\n".join([f"line {i}" for i in range(450)])
    long_note = ng.generate_pattern_note(
        pattern="graphs",
        title="Graphs",
        description=long_lines,
        why_matters=long_lines,
        trade_offs=[],
        code_example=long_lines,
        code_explanation=long_lines,
        sixty_second_pitch=long_lines,
        key_terminology=["a"],
        follow_up_questions=["b"],
        common_pitfalls=["c"],
        has_diagram=False,
    )
    assert "Note exceeds 400 lines" in long_note


def test_generate_problem_note_includes_complexity_and_improvements():
    note = ng.generate_problem_note(
        problem_id="two_sum",
        title="Two Sum",
        pattern="Hash Map",
        difficulty="Easy",
        key_insight="Store complements.",
        trade_offs=["Space for speed"],
        edge_cases=["Duplicate numbers"],
        articulation_improvements=[
            {"before": "I guess a map", "after": "I use a complement lookup map"}
        ],
        solution_approach="One pass map.",
        time_complexity="O(n)",
        space_complexity="O(n)",
    )

    assert "**Pattern**: [[hash-map|Hash Map]]" in note
    assert "### Complexity" in note
    assert "- **Time**: O(n)" in note
    assert "## Trade-offs" in note
    assert "## Edge Cases to Remember" in note
    assert "## Articulation Improvements" in note
