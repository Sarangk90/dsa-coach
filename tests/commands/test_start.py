from unittest.mock import patch

from dsa_coach.commands import start
from dsa_coach.progress import load_progress


def test_start_creates_profile(mock_workspace, capsys):
    with patch("builtins.input", return_value="TestUser"):
        start.cmd_start()

    captured = capsys.readouterr()
    assert "Profile Created!" in captured.out

    progress = load_progress()
    assert progress["profile"]["name"] == "TestUser"


def test_start_existing_profile(populated_progress, capsys):
    # If profile exists, it should welcome back
    start.cmd_start()

    captured = capsys.readouterr()
    assert "Welcome back" in captured.out
    assert "Test User" in captured.out
