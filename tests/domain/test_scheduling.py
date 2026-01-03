import pytest
from datetime import datetime, timedelta
from dsa_coach.domain import scheduling

def test_get_due_items():
    now = datetime(2025, 1, 1, 12, 0, 0)
    queue = [
        {"quest_id": "q1", "due": "2025-01-01T11:00:00", "interval_days": 1}, # Due
        {"quest_id": "q2", "due": "2025-01-02T12:00:00", "interval_days": 1}, # Not due
    ]
    
    due = scheduling.get_due_items(queue, now)
    assert len(due) == 1
    assert due[0]["quest_id"] == "q1"

def test_update_item_success_high_rating():
    now = datetime(2025, 1, 1, 12, 0, 0)
    item = {"quest_id": "q1", "due": "2025-01-01T10:00:00", "interval_days": 2}
    
    # Rating 5 -> double interval
    updated = scheduling.update_item_review(item, rating=5, reviewed_at=now)
    
    assert updated["interval_days"] == 4
    expected_due = now + timedelta(days=4)
    assert updated["due"] == expected_due.isoformat()

def test_update_item_success_medium_rating():
    now = datetime(2025, 1, 1, 12, 0, 0)
    item = {"quest_id": "q1", "due": "2025-01-01T10:00:00", "interval_days": 3}
    
    # Rating 3 -> keep interval
    updated = scheduling.update_item_review(item, rating=3, reviewed_at=now)
    
    assert updated["interval_days"] == 3
    expected_due = now + timedelta(days=3)
    assert updated["due"] == expected_due.isoformat()

def test_update_item_fail_low_rating():
    now = datetime(2025, 1, 1, 12, 0, 0)
    item = {"quest_id": "q1", "due": "2025-01-01T10:00:00", "interval_days": 10}
    
    # Rating 2 -> reset to 1 day
    updated = scheduling.update_item_review(item, rating=2, reviewed_at=now)
    
    assert updated["interval_days"] == 1
    expected_due = now + timedelta(days=1)
    assert updated["due"] == expected_due.isoformat()

