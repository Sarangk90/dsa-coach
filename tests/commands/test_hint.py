import pytest
from unittest.mock import patch
from dsa_coach.commands import hint
from dsa_coach.progress import save_progress, get_default_progress, load_progress

def test_hint_no_active_quest(populated_progress, capsys):
    progress = load_progress()
    progress["profile"]["current_quest"] = None
    save_progress(progress)
    
    hint.cmd_hint()
    captured = capsys.readouterr()
    assert "No active quest" in captured.out

def test_hint_static(populated_progress, capsys):
    # Setup quest
    progress = load_progress()
    progress["profile"]["current_quest"] = "q1"
    save_progress(progress)
    
    quest = {
        "id": "q1", 
        "pattern": "sliding_window",
        "hints": {"low": "Static Hint"}
    }
    
    # Mock confidence < 30 -> low hint
    # Mock mentor import failure
    with patch("dsa_coach.commands.hint.get_all_quests", return_value=[quest]), \
         patch("dsa_coach.commands.hint.get_confidence", return_value=10.0), \
         patch("mentor.get_adaptive_hint", side_effect=ImportError):
         
        hint.cmd_hint()
        
    captured = capsys.readouterr()
    assert "Static Hint" in captured.out
    
    progress = load_progress()
    assert progress["hints_used"] == 1

def test_hint_ai(populated_progress, capsys):
    # Setup quest
    progress = load_progress()
    progress["profile"]["current_quest"] = "q1"
    save_progress(progress)
    
    quest = {"id": "q1", "pattern": "sliding_window"}
    
    with patch("dsa_coach.commands.hint.get_all_quests", return_value=[quest]), \
         patch("dsa_coach.commands.hint.get_confidence", return_value=10.0), \
         patch("mentor.get_adaptive_hint", return_value="AI Hint"):
         
        hint.cmd_hint()
        
    captured = capsys.readouterr()
    assert "AI Hint" in captured.out

