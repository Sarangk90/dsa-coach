from __future__ import annotations

from pathlib import Path


def get_repo_root() -> Path:
    """Return the repository root directory.

    Assumes this file lives at `<repo>/dsa_coach/paths.py`.
    """
    return Path(__file__).resolve().parents[1]


BASE_DIR: Path = get_repo_root()
QUESTS_FILE: Path = BASE_DIR / "quests.json"
PROGRESS_FILE: Path = BASE_DIR / "progress.json"
SOLUTIONS_DIR: Path = BASE_DIR / "solutions"
CONVERSATIONS_DIR: Path = BASE_DIR / "conversations"
