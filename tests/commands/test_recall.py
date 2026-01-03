import pytest
from unittest.mock import patch, MagicMock
from dsa_coach.commands import recall
from dsa_coach.progress import save_progress, load_progress

def test_recall_no_items(populated_progress, capsys):
    recall.cmd_recall()
    captured = capsys.readouterr()
    assert "No items due" in captured.out

def test_recall_items_due(populated_progress, capsys):
    progress = load_progress()
    progress["spaced_repetition_queue"] = [
        {"quest_id": "q1", "due": "2000-01-01T00:00:00", "interval_days": 1}
    ]
    save_progress(progress)
    
    quest = {"id": "q1", "title": "Quest 1", "pattern": "sliding_window"}
    
    # Mock inputs: 
    # 1. Press Enter (after seeing question)
    # 2. Rating (1-5) -> "4"
    mock_inputs = ["", "4"]
    
    with patch("dsa_coach.commands.recall.get_all_quests", return_value=[quest]), \
         patch("builtins.input", side_effect=mock_inputs):
         
        recall.cmd_recall()
        
    captured = capsys.readouterr()
    assert "items due for review" in captured.out
    assert "Quest 1" in captured.out
    assert "Review session complete" in captured.out
    
    progress = load_progress()
    item = progress["spaced_repetition_queue"][0]
    # Rating 4 -> interval * 2 -> 2 days
    assert item["interval_days"] == 2
    # Due date should be future
    assert item["due"] > "2000-01-01"

