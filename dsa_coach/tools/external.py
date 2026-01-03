"""External tools for DSA Coach agent.

Tools for browser interactions, dashboard display, and external resources.
"""

import json
import webbrowser
from pathlib import Path

from ..curriculum import get_pattern_name
from ..storage.db import Database
from .registry import ToolResult, tool

# Cache for quests.json data
_quests_cache: dict | None = None


def _load_quests() -> dict:
    """Load and cache quests.json data."""
    global _quests_cache
    if _quests_cache is None:
        quests_path = Path(__file__).parent.parent.parent / "quests.json"
        with quests_path.open() as f:
            _quests_cache = json.load(f)
    return _quests_cache


def _find_quest(quest_id: str) -> dict | None:
    """Find a quest by ID."""
    quests = _load_quests()

    for quest in quests.get("quests", []):
        if quest.get("id") == quest_id:
            return quest

    return None


@tool(
    name="open_browser",
    description="Open a URL in the user's default web browser.",
    category="external",
)
async def open_browser(
    db: Database,
    url: str,
) -> ToolResult:
    """
    Open a URL in the browser.

    :param url: The URL to open
    :return: Success status
    """
    try:
        webbrowser.open(url)
        return ToolResult(
            success=True,
            data={"url": url},
            message=f"Opened {url} in browser",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to open browser: {str(e)}",
        )


@tool(
    name="open_leetcode_problem",
    description="Open a LeetCode problem for a specific quest in the browser.",
    category="external",
)
async def open_leetcode_problem(
    db: Database,
    quest_id: str,
) -> ToolResult:
    """
    Open the LeetCode problem for a quest.

    :param quest_id: The quest to open
    :return: Success status and URL
    """
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    url = quest.get("link", "")
    if not url:
        return ToolResult(
            success=False,
            error=f"No LeetCode link for quest '{quest_id}'",
        )

    try:
        webbrowser.open(url)
        return ToolResult(
            success=True,
            data={
                "quest_id": quest_id,
                "title": quest.get("title", quest_id),
                "url": url,
            },
            message=f"Opened {quest.get('title', quest_id)} on LeetCode",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to open browser: {str(e)}",
        )


@tool(
    name="get_dashboard_state",
    description="Get the current state for rendering the dashboard including current quest, pattern progress, and alerts.",
    category="external",
)
async def get_dashboard_state(
    db: Database,
    user_id: str = "default",
) -> ToolResult:
    """
    Get complete dashboard state for rendering.

    :return: Dashboard data including profile, current quest, patterns
    """
    # Get profile
    profile = await db.get_or_create_profile(user_id)

    # Get session state
    session = await db.get_latest_session(user_id)
    current_quest = None
    if session and session.current_quest:
        quest = _find_quest(session.current_quest)
        if quest:
            current_quest = {
                "id": session.current_quest,
                "title": quest.get("title", session.current_quest),
                "pattern": quest.get("pattern", "unknown"),
                "difficulty": quest.get("difficulty", "medium"),
            }

    # Get pattern progress (top 5 weakest)
    all_progress = await db.get_all_pattern_progress(user_id)
    weak_patterns = sorted(all_progress, key=lambda p: p.confidence)[:5]

    # Get due reviews
    due_reviews = await db.get_due_reviews(user_id)

    # Build alerts
    alerts = []
    if due_reviews:
        alerts.append(
            {
                "type": "review",
                "message": f"{len(due_reviews)} quests due for review",
                "priority": "high" if len(due_reviews) >= 3 else "medium",
            }
        )

    return ToolResult(
        success=True,
        data={
            "profile": {
                "name": profile.name,
                "quests_completed": profile.quests_completed,
                "member_since": profile.created_at.isoformat(),
            },
            "current_quest": current_quest,
            "weak_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_name": get_pattern_name(p.pattern_id),
                    "confidence": p.confidence,
                }
                for p in weak_patterns
            ],
            "due_reviews_count": len(due_reviews),
            "alerts": alerts,
        },
    )


@tool(
    name="search_patterns_and_quests",
    description="Search for patterns and quests by keyword.",
    category="external",
)
async def search_patterns_and_quests(
    db: Database,
    query: str,
) -> ToolResult:
    """
    Search patterns and quests by keyword.

    :param query: Search query
    :return: Matching patterns and quests
    """
    quests = _load_quests()
    query_lower = query.lower()

    # Search patterns
    matching_patterns = []
    patterns = quests.get("metadata", {}).get("patterns", {})
    for pattern_id, pattern_data in patterns.items():
        if (
            query_lower in pattern_id.lower()
            or query_lower in pattern_data.get("title", "").lower()
            or query_lower in pattern_data.get("description", "").lower()
        ):
            matching_patterns.append(
                {
                    "pattern_id": pattern_id,
                    "title": pattern_data.get("title", pattern_id),
                    "description": pattern_data.get("description", "")[:100],
                }
            )

    # Search quests
    matching_quests = []
    for quest in quests.get("quests", []):
        if (
            query_lower in quest.get("id", "").lower()
            or query_lower in quest.get("title", "").lower()
            or query_lower in quest.get("pattern", "").lower()
        ):
            matching_quests.append(
                {
                    "quest_id": quest["id"],
                    "title": quest.get("title", quest["id"]),
                    "pattern": quest.get("pattern", "unknown"),
                    "difficulty": quest.get("difficulty", "medium"),
                }
            )

    return ToolResult(
        success=True,
        data={
            "query": query,
            "patterns": matching_patterns,
            "quests": matching_quests[:10],  # Limit to 10
        },
        message=f"Found {len(matching_patterns)} patterns and {len(matching_quests)} quests",
    )
