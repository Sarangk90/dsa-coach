"""Adaptive hint generation for DSA Coach."""

from typing import Any

from .client import get_ai_response
from .prompts import DIVE_FRAMEWORK, HINT_PROMPT_TEMPLATE, get_mentor_system_prompt


def get_adaptive_hint(
    quest: dict[str, Any], progress: dict[str, Any], hint_level: str
) -> str:
    """Get an adaptive hint based on student's level and pattern proficiency.

    Args:
        quest: Quest dictionary containing problem info
        progress: User progress dictionary
        hint_level: "low", "medium", or "high" hint level

    Returns:
        Formatted hint text with optional DIVE framework
    """
    pattern = quest.get("pattern", "unknown")
    current_progress = (
        progress.get("pattern_proficiency", {}).get(pattern, {}).get("progress", 0)
    )

    # Map hint_level string to number
    level_map = {"low": 1, "medium": 2, "high": 3}
    level_num = level_map.get(hint_level.lower(), 2)

    # Build the prompt
    user_message = HINT_PROMPT_TEMPLATE.format(
        title=quest.get("title", "Unknown"),
        pattern=pattern.replace("_", " ").title(),
        difficulty=quest.get("difficulty", "medium"),
        description=f"Link: {quest.get('link', 'N/A')}",
        progress=current_progress,
        hint_level=level_num,
    )

    system_prompt = get_mentor_system_prompt(progress)

    # At hint level 2+, also show DIVE framework
    dive_prefix = ""
    if level_num >= 2:
        dive_prefix = DIVE_FRAMEWORK + "\nWhich step are you stuck on?\n\n"

    try:
        llm_hint = get_ai_response(user_message, system_prompt, max_tokens=200)
        return dive_prefix + llm_hint
    except Exception as e:
        # Fallback to static hints
        hints = quest.get("hints", {})
        return dive_prefix + hints.get(hint_level, f"Error getting hint: {e}")
