from __future__ import annotations

import json


def test_reset_single_pattern(populated_progress, monkeypatch):
    from dsa_coach.commands.reset import cmd_reset
    from dsa_coach.progress import load_progress

    # Ensure pattern has progress
    progress = load_progress()
    progress["pattern_proficiency"]["sliding_window"]["attempts"] = 3
    progress["pattern_proficiency"]["sliding_window"]["successes"] = 2
    progress["pattern_proficiency"]["sliding_window"]["avg_time_mins"] = 12
    progress["pattern_proficiency"]["sliding_window"]["confidence"] = 55.0
    with open(populated_progress, "w") as f:
        json.dump(progress, f)

    # Non-interactive safe path via --yes
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    cmd_reset(["pattern", "sliding_window", "--yes"])

    updated = load_progress()
    sw = updated["pattern_proficiency"]["sliding_window"]
    assert sw["attempts"] == 0
    assert sw["successes"] == 0
    assert sw["avg_time_mins"] is None
    assert sw["confidence"] == 0.0

    # Unrelated fields unchanged
    assert updated["profile"]["name"] == "Test User"
    assert updated["profile"]["xp"] == 100


def test_reset_all_patterns(populated_progress, monkeypatch):
    from dsa_coach.commands.reset import cmd_reset
    from dsa_coach.progress import load_progress

    progress = load_progress()
    progress["pattern_proficiency"]["sliding_window"]["attempts"] = 2
    progress["pattern_proficiency"]["sliding_window"]["successes"] = 2
    progress["pattern_proficiency"]["sliding_window"]["confidence"] = 76.0
    progress["pattern_proficiency"]["two_pointers"]["attempts"] = 1
    progress["pattern_proficiency"]["two_pointers"]["successes"] = 0
    progress["pattern_proficiency"]["two_pointers"]["confidence"] = 10.0
    with open(populated_progress, "w") as f:
        json.dump(progress, f)

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    cmd_reset(["patterns", "--yes"])

    updated = load_progress()
    for pat, prof in updated["pattern_proficiency"].items():
        assert prof["attempts"] == 0
        assert prof["successes"] == 0
        assert prof["avg_time_mins"] is None
        assert prof["confidence"] == 0.0


def test_reset_requires_confirmation_when_interactive(monkeypatch, populated_progress):
    from dsa_coach.commands.reset import cmd_reset
    from dsa_coach.progress import load_progress

    progress = load_progress()
    progress["pattern_proficiency"]["sliding_window"]["attempts"] = 2
    with open(populated_progress, "w") as f:
        json.dump(progress, f)

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "n")

    cmd_reset(["pattern", "sliding_window"])

    updated = load_progress()
    assert updated["pattern_proficiency"]["sliding_window"]["attempts"] == 2




