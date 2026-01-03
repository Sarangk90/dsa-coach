from unittest.mock import patch

from dsa_coach.commands import done
from dsa_coach.progress import load_progress, save_progress


def test_done_no_active_quest(populated_progress, capsys):
    # Ensure no active quest
    progress = load_progress()
    progress["profile"]["current_quest"] = None
    save_progress(progress)

    done.cmd_done()
    captured = capsys.readouterr()
    assert "No active quest" in captured.out


def test_done_success(populated_progress, mock_workspace, capsys):
    # Setup active quest
    progress = load_progress()
    progress["profile"]["current_quest"] = "q1"
    # Ensure q1 exists in all_quests
    quest = {"id": "q1", "title": "Quest 1", "xp": 100, "pattern": "sliding_window"}
    save_progress(progress)

    with (
        patch("dsa_coach.commands.done.get_all_quests", return_value=[quest]),
        patch("builtins.input", return_value="30"),
    ):  # 30 mins
        done.cmd_done()

    captured = capsys.readouterr()
    assert "VICTORY" in captured.out

    progress = load_progress()
    assert progress["profile"]["current_quest"] is None
    assert "q1" in progress["completed_quests"]
    # XP should be 100 (base) + 20 (no hints) = 120 + existing 100 = 220
    # PLUS Achievement "First Blood" (25 XP) since it's the first completed quest.
    # Expected total is 245
    assert progress["profile"]["xp"] == 245


def test_done_achievement_unlock(populated_progress, capsys):
    # Setup for first blood
    progress = load_progress()
    progress["profile"]["current_quest"] = "q1"
    progress["completed_quests"] = {}  # Empty
    progress["achievements"] = []
    save_progress(progress)

    quest = {"id": "q1", "title": "Quest 1", "xp": 100, "type": "code"}

    # We need to mock check_achievements to return something, or rely on real logic?
    # Real logic uses QUESTS_FILE which is patched.
    # The patched QUESTS_FILE has achievements.

    with (
        patch("dsa_coach.commands.done.get_all_quests", return_value=[quest]),
        patch("builtins.input", return_value="30"),
    ):
        done.cmd_done()

    captured = capsys.readouterr()
    assert "ACHIEVEMENT UNLOCKED" in captured.out

    progress = load_progress()
    assert "first_blood" in progress["achievements"]
