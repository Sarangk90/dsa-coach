from __future__ import annotations

from pathlib import Path


def test_save_and_load_conversation_roundtrip(tmp_path: Path) -> None:
    """Regression: load_conversation should not crash and should load saved messages."""
    from dsa_coach.ai import session as s

    conversations_dir = tmp_path / "conversations"
    conversations_dir.mkdir(parents=True, exist_ok=True)

    # Patch the module-level constant used by save/load.
    s.CONVERSATIONS_DIR = conversations_dir

    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    s.save_conversation(
        "learn", "sliding_window", messages, metadata={"pattern": "sliding_window"}
    )

    loaded = s.load_conversation("learn", "sliding_window")
    assert loaded is not None
    assert loaded["messages"] == messages
