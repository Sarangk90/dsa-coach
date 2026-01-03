import pytest
from unittest.mock import patch, MagicMock
from dsa_coach.commands import next_quest
from dsa_coach.progress import save_progress, get_default_progress

def test_next_active_quest(populated_progress, capsys):
    # Set active quest
    from dsa_coach.progress import load_progress
    progress = load_progress()
    progress["profile"]["current_quest"] = "q1"
    save_progress(progress)
    
    # Mock get_all_quests to find q1
    with patch("dsa_coach.commands.next_quest.get_all_quests") as mock_get_all:
        mock_get_all.return_value = [{"id": "q1", "title": "Quest 1"}]
        next_quest.cmd_next()
    
    captured = capsys.readouterr()
    assert "active quest: Quest 1" in captured.out

def test_next_new_quest(populated_progress, capsys, mock_workspace):
    # Mock selection to return a quest
    quest = {"id": "q2", "title": "Quest 2", "day": 1, "link": "http://link", "difficulty": "easy"}
    
    with patch("dsa_coach.commands.next_quest.get_next_quest", return_value=quest), \
         patch("dsa_coach.commands.next_quest.get_all_quests", return_value=[quest]), \
         patch("dsa_coach.commands.next_quest.create_solution_file") as mock_create, \
         patch("builtins.input", return_value="1"), \
         patch("webbrowser.open"):
        
        mock_create.return_value = mock_workspace / "q2.py"
        next_quest.cmd_next()
        
    captured = capsys.readouterr()
    # Updated: output format changed from "NEW QUEST:" to "QUEST:"
    assert "QUEST: Quest 2" in captured.out
    
    # Verify progress update
    from dsa_coach.progress import load_progress
    progress = load_progress()
    assert progress["profile"]["current_quest"] == "q2"

def test_next_low_confidence_prompt(populated_progress, capsys):
    # Setup low confidence
    from dsa_coach.progress import load_progress
    progress = load_progress()
    progress["pattern_proficiency"]["sliding_window"] = {"attempts": 1, "confidence": 10.0}
    save_progress(progress)
    
    quest = {"id": "q3", "title": "Quest 3", "pattern": "sliding_window", "difficulty": "medium"}
    
    # We need to mock mentor module because it's imported inside the function
    # But since it's not imported at top level, we mock sys.modules? 
    # Or just patch 'mentor.start_learning_session' if mentor is importable.
    
    with patch("dsa_coach.commands.next_quest.get_next_quest", return_value=quest), \
         patch("builtins.input", side_effect=["y", "n"]), \
         patch("mentor.interactive_learning_session") as mock_learn, \
         patch("webbrowser.open"):
         
        next_quest.cmd_next()
        
        mock_learn.assert_called_once()
        captured = capsys.readouterr()
        assert "confidence is 10%" in captured.out

