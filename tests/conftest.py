import shutil

import pytest

from dsa_coach import paths


@pytest.fixture
def mock_workspace(tmp_path):
    """
    Creates a temporary workspace with necessary files and directories.
    Monkeypatches dsa_coach.paths to point to this workspace.
    """
    # Create temp directories
    temp_progress = tmp_path / "progress.json"
    temp_solutions = tmp_path / "solutions"
    temp_solutions.mkdir()
    temp_conversations = tmp_path / "conversations"
    temp_conversations.mkdir()

    # Copy quests.json (read-only reference)
    shutil.copy(paths.QUESTS_FILE, tmp_path / "quests.json")

    # Monkeypatch paths
    # We need to patch the module-level variables in dsa_coach.paths
    import dsa_coach.paths

    orig_base_dir = dsa_coach.paths.BASE_DIR
    orig_quests = dsa_coach.paths.QUESTS_FILE
    orig_progress = dsa_coach.paths.PROGRESS_FILE
    orig_solutions = dsa_coach.paths.SOLUTIONS_DIR
    orig_conversations = dsa_coach.paths.CONVERSATIONS_DIR

    dsa_coach.paths.BASE_DIR = tmp_path
    dsa_coach.paths.QUESTS_FILE = tmp_path / "quests.json"
    dsa_coach.paths.PROGRESS_FILE = temp_progress
    dsa_coach.paths.SOLUTIONS_DIR = temp_solutions
    dsa_coach.paths.CONVERSATIONS_DIR = temp_conversations

    # Patch modules that imported constants from paths
    import dsa_coach.progress

    dsa_coach.progress.PROGRESS_FILE = temp_progress
    dsa_coach.progress.QUESTS_FILE = tmp_path / "quests.json"

    import dsa_coach.quests

    dsa_coach.quests.QUESTS_FILE = tmp_path / "quests.json"

    import coach

    coach.BASE_DIR = tmp_path
    coach.QUESTS_FILE = tmp_path / "quests.json"
    coach.PROGRESS_FILE = temp_progress
    coach.SOLUTIONS_DIR = temp_solutions

    yield tmp_path

    # Restore paths
    dsa_coach.paths.BASE_DIR = orig_base_dir
    dsa_coach.paths.QUESTS_FILE = orig_quests
    dsa_coach.paths.PROGRESS_FILE = orig_progress
    dsa_coach.paths.SOLUTIONS_DIR = orig_solutions
    dsa_coach.paths.CONVERSATIONS_DIR = orig_conversations


@pytest.fixture
def clean_progress(mock_workspace):
    """Returns a clean progress state (no file on disk yet)."""
    return mock_workspace / "progress.json"


@pytest.fixture
def populated_progress(mock_workspace):
    """Creates a progress.json with some pre-filled data."""
    import json

    from dsa_coach.progress import get_default_progress

    data = get_default_progress()
    data["profile"]["name"] = "Test User"
    data["profile"]["xp"] = 100

    progress_path = mock_workspace / "progress.json"
    with open(progress_path, "w") as f:
        json.dump(data, f)

    return progress_path
