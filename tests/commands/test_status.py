from dsa_coach.commands import status


def test_status_output(populated_progress, capsys):
    status.cmd_status()
    captured = capsys.readouterr()
    assert "Test User" in captured.out
    assert "Novice" in captured.out
    assert "XP" in captured.out
    assert "100" in captured.out


def test_status_no_profile(mock_workspace, capsys):
    status.cmd_status()
    captured = capsys.readouterr()
    assert "No profile found" in captured.out
