"""Code review functionality for DSA Coach."""

from typing import Any

from .client import get_ai_response
from .prompts import CODE_REVIEW_PROMPT, get_mentor_system_prompt


def review_code(quest: dict[str, Any], code: str, progress: dict[str, Any]) -> str:
    """Review student's code and provide feedback.

    Args:
        quest: Quest dictionary containing problem info
        code: Student's code to review
        progress: User progress dictionary

    Returns:
        AI-generated code review feedback
    """
    user_message = CODE_REVIEW_PROMPT.format(
        title=quest.get("title", "Unknown"),
        pattern=quest.get("pattern", "unknown").replace("_", " ").title(),
        difficulty=quest.get("difficulty", "medium"),
        code=code,
    )

    system_prompt = get_mentor_system_prompt(progress)

    try:
        return get_ai_response(user_message, system_prompt, max_tokens=500)
    except Exception as e:
        return f"Error getting code review: {e}"
