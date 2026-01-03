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

    dsa_coach.progress.PROGRESS_FILE = temp_progress  # type: ignore[attr-defined]
    dsa_coach.progress.QUESTS_FILE = tmp_path / "quests.json"  # type: ignore[attr-defined]

    import dsa_coach.quests

    dsa_coach.quests.QUESTS_FILE = tmp_path / "quests.json"  # type: ignore[attr-defined]

    import coach

    coach.BASE_DIR = tmp_path  # type: ignore[attr-defined]
    coach.QUESTS_FILE = tmp_path / "quests.json"  # type: ignore[attr-defined]
    coach.PROGRESS_FILE = temp_progress  # type: ignore[attr-defined]
    coach.SOLUTIONS_DIR = temp_solutions  # type: ignore[attr-defined]

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


# =============================================================================
# AGENT TEST HARNESS FIXTURES
# =============================================================================


@pytest.fixture
async def coach_harness(tmp_path):
    """
    Async fixture that provides an initialized CoachTestHarness.

    The harness uses an isolated temp database and is automatically
    cleaned up after the test.

    Usage:
        async def test_something(coach_harness):
            response = await coach_harness.send("Hello!")
            assert "hello" in response.content.lower()
    """
    from tests.harness import CoachTestHarness

    db_path = tmp_path / "test_coach.db"
    harness = CoachTestHarness(db_path=db_path)
    await harness.setup()

    yield harness

    await harness.cleanup()


@pytest.fixture
async def hydrated_harness(tmp_path):
    """
    Async fixture that provides a CoachTestHarness pre-populated with test data.

    Includes:
    - User profile with some progress
    - Pattern progress at various levels
    - Completed quests
    - Some mistakes and milestones

    Usage:
        async def test_progress(hydrated_harness):
            patterns = await hydrated_harness.inspect_patterns()
            assert len(patterns) > 0
    """
    from tests.harness import CoachTestHarness

    db_path = tmp_path / "test_coach.db"
    harness = CoachTestHarness(db_path=db_path, auto_hydrate=True)
    await harness.setup()

    yield harness

    await harness.cleanup()


@pytest.fixture
def sync_coach_harness(tmp_path):
    """
    Synchronous fixture that provides a SyncCoachTestHarness.

    Useful for tests that don't want to deal with async.

    Usage:
        def test_something(sync_coach_harness):
            response = sync_coach_harness.send("Hello!")
            assert "hello" in response.content.lower()
    """
    from tests.harness.coach_harness import SyncCoachTestHarness

    db_path = tmp_path / "test_coach.db"
    harness = SyncCoachTestHarness(db_path=db_path)
    harness.__enter__()

    yield harness

    harness.__exit__(None, None, None)
