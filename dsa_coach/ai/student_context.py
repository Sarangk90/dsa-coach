"""Student context builder for dynamic system prompt injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import SLICE_READINESS

if TYPE_CHECKING:
    from ..storage.db import Database


def _format_mastery_snapshot(patterns: list) -> str:
    """Format pattern mastery levels for context injection."""
    if not patterns:
        return "No patterns started yet."

    lines = []
    for p in sorted(patterns, key=lambda x: x.progress, reverse=True):
        level = (
            "MASTERED"
            if p.progress >= 80
            else "PROFICIENT"
            if p.progress >= 60
            else "DEVELOPING"
            if p.progress >= 30
            else "BEGINNER"
        )
        pattern_name = p.pattern_id.replace("_", " ").title()
        lines.append(f"- {pattern_name}: {p.progress}% ({level})")

    return "\n".join(lines) if lines else "No patterns started yet."


def _format_current_session(session) -> str:
    """Format current session context."""
    if not session:
        return "No active session."

    parts = [f"Type: {session.session_type}"]
    if session.current_pattern:
        parts.append(f"Pattern: {session.current_pattern.replace('_', ' ').title()}")
    if session.current_quest:
        parts.append(f"Quest: {session.current_quest}")

    return " | ".join(parts)


def _format_concepts(concepts: list[dict]) -> str:
    """Format concept list for context injection."""
    if not concepts:
        return "None recorded."

    lines = []
    for c in concepts[:10]:  # Limit to 10 most relevant
        pattern = c.get("pattern_id", "").replace("_", " ").title()
        concept = c.get("concept", "Unknown")
        lines.append(f"- [{pattern}] {concept}")

    return "\n".join(lines) if lines else "None recorded."


def _format_mistakes(mistakes: list[dict]) -> str:
    """Format recurring mistakes for context injection."""
    if not mistakes:
        return "No recurring mistakes detected - great job!"

    lines = []
    for m in mistakes[:5]:
        # DB returns "type" not "mistake_type" from get_recurring_mistake_types
        mtype = (
            m.get("type", m.get("mistake_type", "unknown")).replace("_", " ").title()
        )
        count = m.get("count", 1)
        patterns = m.get("patterns", [])
        pattern_str = ", ".join(p.replace("_", " ").title() for p in patterns[:2])
        lines.append(f"- {mtype} (x{count}) in {pattern_str}")

    return "\n".join(lines) if lines else "No recurring mistakes detected."


def _format_due_reviews(reviews: list) -> str:
    """Format spaced repetition queue."""
    if not reviews:
        return "No reviews due - all caught up!"

    lines = []
    for r in reviews[:5]:
        quest_id = (
            r.quest_id if hasattr(r, "quest_id") else r.get("quest_id", "Unknown")
        )
        pattern = r.pattern_id if hasattr(r, "pattern_id") else r.get("pattern_id", "")
        pattern_name = pattern.replace("_", " ").title()
        lines.append(f"- {quest_id} ({pattern_name})")

    return "\n".join(lines) if lines else "No reviews due."


def _format_wins(milestones: list[dict]) -> str:
    """Format recent wins for encouragement."""
    if not milestones:
        return "Keep going - first wins are coming!"

    lines = []
    for m in milestones[:3]:
        desc = m.get("description", "Achievement unlocked")
        achieved = m.get("achieved_at", "")[:10] if m.get("achieved_at") else ""
        lines.append(f"- {desc} ({achieved})")

    return "\n".join(lines) if lines else "Keep going!"


def _format_activity(activity: dict) -> str:
    """Format weekly activity summary."""
    if not activity:
        return "No activity this week yet."

    problems = activity.get("problems_solved", 0)
    time_mins = activity.get("time_spent_mins", 0)
    patterns = activity.get("patterns_worked", [])

    hours = time_mins // 60
    mins = time_mins % 60
    time_str = f"{hours}h {mins}m" if hours else f"{mins}m"
    pattern_str = ", ".join(p.replace("_", " ").title() for p in patterns[:3]) or "None"

    return f"Problems: {problems} | Time: {time_str} | Patterns: {pattern_str}"


async def _compute_slice_progress(db: Database, user_id: str) -> dict:
    """Compute Google L6 slice progress from completed quests."""
    import json
    from pathlib import Path

    completed_quests = await db.get_completed_quests(user_id)
    completed_ids = {q.quest_id for q in completed_quests}

    # Load quests.json to get slice tags
    quests_path = Path(__file__).parent.parent.parent / "quests.json"
    try:
        with quests_path.open() as f:
            quests = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "slice-1": {"total": 0, "done": 0},
            "slice-2": {"total": 0, "done": 0},
            "slice-3": {"total": 0, "done": 0},
        }

    slice_counts: dict[str, dict[str, int]] = {
        "slice-1": {"total": 0, "done": 0},
        "slice-2": {"total": 0, "done": 0},
        "slice-3": {"total": 0, "done": 0},
    }

    for pattern in quests.get("curriculum", {}).get("fast_track", []):
        for concept in pattern.get("concepts", []):
            for problem in concept.get("practice_problems", []):
                tags = problem.get("tags", [])
                for slice_tag in ["slice-1", "slice-2", "slice-3"]:
                    if slice_tag in tags:
                        slice_counts[slice_tag]["total"] += 1
                        if problem["problem_id"] in completed_ids:
                            slice_counts[slice_tag]["done"] += 1

    return slice_counts


def _format_slice_progress(slice_counts: dict) -> str:
    """Format slice progress for display with visual progress bars."""
    lines = []
    readiness_map = SLICE_READINESS

    for slice_tag in ["slice-1", "slice-2", "slice-3"]:
        counts = slice_counts.get(slice_tag, {"done": 0, "total": 0})
        done, total = counts["done"], counts["total"]
        pct = (done / total * 100) if total > 0 else 0
        filled = int(pct / 10)
        bar = "\u2588" * filled + "\u2591" * (10 - filled)
        readiness = readiness_map.get(slice_tag, "")
        status = (
            "\u2713 COMPLETE" if pct >= 100 else f"\u2192 {readiness} ready when done"
        )
        lines.append(
            f"- {slice_tag.upper()}: {bar} {done}/{total} ({pct:.0f}%) {status}"
        )

    return "\n".join(lines) if lines else "No slice data available."


def _get_current_slice(slice_counts: dict) -> str:
    """Determine which slice the student should focus on."""
    for slice_tag in ["slice-1", "slice-2", "slice-3"]:
        counts = slice_counts.get(slice_tag, {"done": 0, "total": 0})
        if counts["done"] < counts["total"]:
            return slice_tag.upper()
    return "ALL COMPLETE"


async def build_student_context(db: Database, user_id: str = "default") -> str:
    """
    Build comprehensive student context for system prompt injection.

    This creates a rich understanding of the student for the agent,
    enabling truly adaptive, personalized coaching.

    Args:
        db: Database instance (must be connected)
        user_id: User identifier

    Returns:
        Formatted student context string for system prompt
    """
    # Gather all student data
    profile = await db.get_or_create_profile(user_id)
    patterns = await db.get_all_pattern_progress(user_id)
    due_reviews = await db.get_due_reviews(user_id)
    await db.get_recent_mistakes(user_id, limit=5)
    recurring_mistakes = await db.get_recurring_mistake_types(user_id)
    concepts_struggling = await db.get_struggling_concepts(user_id)
    concepts_mastered = await db.get_mastered_concepts(user_id)
    recent_wins = await db.get_recent_milestones(user_id, days=7)
    current_session = await db.get_latest_session(user_id)
    weekly_activity = await db.get_weekly_activity(user_id)

    # Compute Google L6 slice progress
    slice_counts = await _compute_slice_progress(db, user_id)
    current_slice = _get_current_slice(slice_counts)

    # Build the context string
    return f"""
## YOUR STUDENT: {profile.name}

### Mastery Levels
{_format_mastery_snapshot(patterns)}

### Google L6 Slice Progress (Current Focus: {current_slice})
{_format_slice_progress(slice_counts)}

### Current Session
{_format_current_session(current_session)}

### Concepts Mastered (build on these foundations)
{_format_concepts(concepts_mastered)}

### Concepts Struggling With (focus teaching here)
{_format_concepts(concepts_struggling)}

### Recurring Mistake Patterns (proactively address these)
{_format_mistakes(recurring_mistakes)}

### Spaced Repetition Queue ({len(due_reviews)} due)
{_format_due_reviews(due_reviews)}

### Recent Wins (reference for encouragement)
{_format_wins(recent_wins)}

### Engagement This Week
{_format_activity(weekly_activity)}


<context_usage>

## HOW TO USE THIS STUDENT CONTEXT

<emotional_first>
CHECK EMOTIONAL STATE FIRST (Pillar 12):
Watch for anxiety signals: "I'll never get this", rushing, repeated apologies, frustration.
If detected: PAUSE content. Acknowledge \u2192 Normalize \u2192 Shrink the win \u2192 Rebuild.
Their emotional state comes first, their understanding second, their speed third.
</emotional_first>

<scaffolding_guide>
Adjust approach based on their mastery levels (Pillar 6 - 5 Levels):
- **BEGINNER (0-30%)**: HIGH scaffolding - worked examples, explicit pattern naming. Struggle limit: 2-3 min.
- **DEVELOPING (30-55%)**: MEDIUM scaffolding - Socratic questions, hints on request. Struggle limit: 5 min.
- **PROFICIENT (55-75%)**: LOW scaffolding - edge cases, trade-offs, peer-like. Struggle limit: 10 min.
- **ADVANCED (75-90%)**: INTERVIEW-READY - mock conditions, timed problems, combined patterns.
- **EXPERT (90%+)**: MINIMAL - peer-level optimization, interview simulation with full debrief.
</scaffolding_guide>

<mistake_prevention>
Use their recurring mistakes with ADAPTIVE timing (Pillar 9):
- **1st occurrence**: Let them make it, THEN discuss (learning opportunity)
- **2nd+ occurrence**: Proactive warning JUST before risky step
- **3rd+ occurrence**: INTERRUPT: "Stop. You're doing it again."

Before coding, require pattern preflight: invariant, boundary semantics, likely mistake to avoid.
</mistake_prevention>

<invariant_requirements>
Require explicit invariants (Pillar 13):
Before coding: "What must always be true? How will each step maintain it?"
After coding: "State the invariant. Why does termination give correct answer?"
For PROFICIENT+: "Big-O time and space. Why is this optimal?"
</invariant_requirements>

<concept_handling>
For "Struggling" concepts: They don't understand it. Use a NEW analogy. Verify with teach-back.
For "Mastered" concepts: Build on these. "Remember how you nailed hash tables? Same idea here..."
</concept_handling>

<encouragement>
Use their past wins for SPECIFIC encouragement (Pillar 10):
"Remember when you solved [specific win] without hints? Same caliber problem."
For PROFICIENT+: "In an interview, this would be [HIRE/LEAN HIRE/etc] because..."
Never say "good job" without specifics.
</encouragement>

<interview_mode>
Check interview timeline (Pillar 11):
- >8 weeks: Deep learning, full Ladder Method
- 4-8 weeks: Balanced mode, weekly mocks
- 2-4 weeks: Simulation mode, timed daily
- <2 weeks: Confidence mode, NO new patterns, "You're ready"
- Day before: NO NEW PROBLEMS, review strongest patterns only
</interview_mode>

<socratic_exceptions>
Direct teaching IS appropriate when:
- First time seeing a pattern (then switch to Socratic)
- 3+ failed attempts (missing foundation)
- <7 days to interview
- Student explicitly asks: "Can you just show me?"
Signal: "Let me show you this one, THEN you'll apply it."
</socratic_exceptions>

<red_flag_recovery>
If they say "I'm lost" / "I don't see how this relates" / random guessing (Pillar 2):
1. Stop advancing immediately
2. Drop 1-3 abstraction levels (adaptive)
3. Rebuild from a 3-element concrete example
4. Continue until you see "Oh! I see it now."
</red_flag_recovery>

</context_usage>
"""
