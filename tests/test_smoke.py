import json
import pytest
from unittest.mock import patch
import coach
from dsa_coach.storage import load_json

def test_full_user_flow(mock_workspace):
    """
    Test the complete new user journey:
    1. start -> creates profile
    2. next -> gets first quest
    3. done -> completes quest
    4. status -> shows progress
    """
    
    # 1. Start & 2. Next Quest & 3. Done
    # We mock input to handle all prompts in sequence:
    # 1. "What's your name?" -> "TestUser"
    # 2. "Open LeetCode...?" -> "n"
    # 3. "Choose (1/2/3)" -> "1" (start solving)
    # 4. "How many minutes...?" -> "30"
    # 5. "Choose (1/2/3/0)" -> "0" (exit the auto-transition menu after done)
    
    mock_inputs = ["TestUser", "n", "1", "30", "0"]
    
    with patch('builtins.input', side_effect=mock_inputs):
        # 1. Start
        coach.cmd_start()
        
        progress = load_json(coach.PROGRESS_FILE)
        assert progress["profile"]["name"] == "TestUser"
        assert progress["profile"]["xp"] == 0
        
        # 2. Next Quest
        coach.cmd_next()
        
        progress = load_json(coach.PROGRESS_FILE)
        current_quest_id = progress["profile"]["current_quest"]
        assert current_quest_id is not None
        
        # Verify solution file created
        quest_file = coach.SOLUTIONS_DIR / f"day1/{current_quest_id}.py"
        assert quest_file.exists()
        
        # 3. Done
        coach.cmd_done()
        
    progress = load_json(coach.PROGRESS_FILE)
    assert progress["profile"]["current_quest"] is None
    assert current_quest_id in progress["completed_quests"]
    assert progress["profile"]["xp"] > 0
    
    # 4. Status
    coach.cmd_status()

def test_status_no_profile(clean_progress):
    """Test status command when no profile exists."""
    # Should print error but not crash
    coach.cmd_status()

def test_next_no_profile(clean_progress):
    """Test next command when no profile exists."""
    # Should print error but not crash
    coach.cmd_next()

