from datetime import datetime, timedelta
from typing import Any


def get_due_items(queue: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """Return list of items from queue that are due or overdue."""
    due_items = []
    for item in queue:
        due_time = datetime.fromisoformat(item["due"])
        if due_time <= now:
            due_items.append(item)
    return due_items


def update_item_review(
    item: dict[str, Any], rating: int, reviewed_at: datetime
) -> dict[str, Any]:
    """
    Update the item's interval and due date based on recall rating (1-5).
    Rating >= 4: Double interval
    Rating >= 3: Keep interval
    Rating < 3: Reset to 1 day
    """
    current_interval = item.get("interval_days", 1)

    if rating >= 4:
        new_interval = current_interval * 2
    elif rating >= 3:
        new_interval = current_interval
    else:
        new_interval = 1

    item["interval_days"] = new_interval
    item["due"] = (reviewed_at + timedelta(days=new_interval)).isoformat()
    return item


def schedule_new_review(quest_id: str, completed_at: datetime) -> dict[str, Any]:
    """Create a new spaced repetition item starting with 1 day interval."""
    return {
        "quest_id": quest_id,
        "due": (completed_at + timedelta(days=1)).isoformat(),
        "interval_days": 1,
    }
