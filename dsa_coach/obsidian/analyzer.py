"""Analyze learning sessions to determine when notes should be created.

Identifies note-worthy concepts from conversations and provides
context for note generation.
"""

from __future__ import annotations

from typing import Any


def analyze_learning_session(
    pattern: str,
    messages: list[dict[str, str]],
    progress_before: float,
    progress_after: float,
) -> dict[str, Any]:
    """Analyze a learning session to extract note-worthy insights.

    Args:
        pattern: Pattern name
        messages: Conversation messages
        progress_before: Progress before session
        progress_after: Progress after session

    Returns:
        Analysis dict with insights, articulation_improvements, key_concepts
    """
    analysis: dict[str, Any] = {
        "pattern": pattern,
        "progress_gain": progress_after - progress_before,
        "message_count": len(messages),
        "insights": [],
        "articulation_improvements": [],
        "key_concepts": [],
        "follow_up_questions": [],
    }

    # Extract user messages for analysis
    user_messages = [m for m in messages if m.get("role") == "user"]
    assistant_messages = [m for m in messages if m.get("role") == "assistant"]

    # Look for articulation improvements (user questions that got refined)
    for i, msg in enumerate(user_messages):
        content = msg.get("content", "").lower()

        # Check if user asked "how", "when", "why" questions
        if any(
            word in content for word in ["how do", "when should", "why use", "what is"]
        ):
            # Find the assistant's response
            if i < len(assistant_messages):
                response = assistant_messages[i].get("content", "")
                # Extract key phrases from response (simplified)
                if len(response) > 50:
                    analysis["insights"].append(
                        {
                            "question": msg.get("content", "")[:100],
                            "insight": response[:200] + "...",
                        }
                    )

    # Identify key concepts mentioned (simplified heuristic)
    common_concepts = [
        "time complexity",
        "space complexity",
        "trade-off",
        "edge case",
        "optimization",
        "pattern",
        "approach",
        "algorithm",
    ]

    all_content = " ".join(m.get("content", "").lower() for m in messages)
    for concept in common_concepts:
        if concept in all_content:
            analysis["key_concepts"].append(concept)

    return analysis


def should_create_note(
    pattern: str,
    progress: float,
    session_messages: int,
    progress_gain: float,
) -> tuple[bool, str]:
    """Determine if a pattern note should be created after a learning session.

    Args:
        pattern: Pattern name
        progress: Current progress level
        session_messages: Number of messages in session
        progress_gain: Progress increase from session

    Returns:
        (should_create: bool, reason: str)
    """
    # Don't create note if session was too short
    if session_messages < 4:
        return (False, "Session too short (< 4 messages)")

    # Create note if progress is now above threshold (pattern understood)
    if progress >= 40 and progress_gain > 10:
        return (
            True,
            f"Pattern learned (progress: {progress:.0f}%, gain: +{progress_gain:.0f}%)",
        )

    # Create note if session was substantial even if progress is still low
    if session_messages >= 10:
        return (True, f"Substantial session ({session_messages} messages)")

    return (False, "Session didn't meet thresholds for note creation")


def should_create_problem_note(
    problem_id: str,
    pattern: str,
    hints_used: int,
    time_spent: int | None = None,
) -> tuple[bool, str]:
    """Determine if a problem note should be created.

    Problem notes are only created if the problem taught something
    interview-worthy beyond the pattern itself.

    Args:
        problem_id: Problem identifier
        pattern: Associated pattern
        hints_used: Number of hints used
        time_spent: Time spent in minutes (optional)

    Returns:
        (should_create: bool, reason: str)
    """
    # For now, we'll be conservative and not auto-create problem notes
    # Agent can decide based on user's explicit insights

    if hints_used >= 3:
        return (
            True,
            f"Challenging problem (used {hints_used} hints) - may have unique insights",
        )

    if time_spent and time_spent > 45:
        return (
            True,
            f"Time-intensive problem ({time_spent}m) - likely has valuable insights",
        )

    return (False, "Problem follows standard pattern - note optional")


def extract_articulation_improvements(
    messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Extract articulation improvements from conversation.

    Looks for cases where user phrased something poorly and mentor
    provided a better phrasing.

    Args:
        messages: Conversation messages

    Returns:
        List of dicts with 'before', 'after', 'context'
    """
    improvements = []

    # Simplified extraction - look for correction patterns
    for i in range(len(messages) - 1):
        if messages[i].get("role") == "user":
            user_content = messages[i].get("content", "")

            if i + 1 < len(messages) and messages[i + 1].get("role") == "assistant":
                assistant_content = messages[i + 1].get("content", "")

                # Look for phrases indicating correction/improvement
                correction_indicators = [
                    "better way to say",
                    "more precise term is",
                    "technically speaking",
                    "correct term for",
                    "we call this",
                ]

                for indicator in correction_indicators:
                    if indicator in assistant_content.lower():
                        improvements.append(
                            {
                                "before": user_content[:100],
                                "after": assistant_content[:200],
                                "context": "terminology correction",
                            }
                        )
                        break

    return improvements
