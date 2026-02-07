"""Regression tests for note creation/update tool behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from dsa_coach.storage.models import PatternProgress
from dsa_coach.tools import consolidated
from dsa_coach.tools.consolidated import create_note, update_note


class DummyDB:
    def __init__(self, progress: int | None = None):
        self.progress = progress

    async def get_pattern_progress(self, _user_id: str, pattern_id: str):
        if self.progress is None:
            return None
        return PatternProgress(
            id=f"default_{pattern_id}",
            user_id="default",
            pattern_id=pattern_id,
            progress=self.progress,
        )


@pytest.mark.asyncio
async def test_create_note_returns_error_when_vault_not_configured(monkeypatch):
    monkeypatch.setattr(consolidated, "get_vault_path", lambda: None)

    result = await create_note(db=DummyDB(), type="pattern", pattern="graphs")

    assert result.success is False
    assert "OBSIDIAN_VAULT_PATH" in result.error


@pytest.mark.asyncio
async def test_create_note_pattern_respects_auto_check_criteria(monkeypatch, tmp_path):
    monkeypatch.setattr(consolidated, "get_vault_path", lambda: tmp_path)
    monkeypatch.setattr(consolidated, "note_exists", lambda _filename, _kind: False)
    monkeypatch.setattr(
        consolidated,
        "should_create_note",
        lambda *_args, **_kwargs: (False, "session too short"),
    )

    result = await create_note(
        db=DummyDB(progress=20),
        type="pattern",
        pattern="graphs",
        auto_check_criteria=True,
    )

    assert result.success is False
    assert "criteria not met" in (result.message or "")
    assert result.data["should_create"] is False


@pytest.mark.asyncio
async def test_create_note_pattern_writes_note_on_success_path(monkeypatch, tmp_path):
    monkeypatch.setattr(consolidated, "get_vault_path", lambda: tmp_path)
    monkeypatch.setattr(consolidated, "note_exists", lambda _filename, _kind: False)
    monkeypatch.setattr(
        consolidated,
        "should_create_note",
        lambda *_args, **_kwargs: (True, "ready"),
    )

    captured = {}

    def fake_generate_pattern_note(**kwargs):
        captured["generate_kwargs"] = kwargs
        return "# Pattern Note"

    def fake_write_note(content: str, filename: str, kind: str):
        captured["write"] = {"content": content, "filename": filename, "kind": kind}
        return True, "written", Path(tmp_path) / "Patterns" / filename

    monkeypatch.setattr(
        consolidated, "generate_pattern_note", fake_generate_pattern_note
    )
    monkeypatch.setattr(consolidated, "write_note", fake_write_note)

    result = await create_note(
        db=DummyDB(progress=80),
        type="pattern",
        pattern="graphs",
        trade_offs="not-json-tradeoff",
        related_patterns="trees, bfs",
        key_terminology="queue, visited",
    )

    assert result.success is True
    assert result.data["filename"].endswith(".md")
    assert captured["write"]["kind"] == "pattern"
    assert captured["write"]["content"] == "# Pattern Note"
    # Invalid JSON should fall back to a single generic tradeoff entry.
    assert len(captured["generate_kwargs"]["trade_offs"]) == 1
    assert captured["generate_kwargs"]["related_patterns"][0]["name"] == "trees"


@pytest.mark.asyncio
async def test_create_note_problem_validates_problem_id_and_unknown_type(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(consolidated, "get_vault_path", lambda: tmp_path)

    missing_problem = await create_note(db=DummyDB(), type="problem", problem_id=None)
    assert missing_problem.success is False
    assert "problem_id is required" in missing_problem.error

    unknown_type = await create_note(db=DummyDB(), type="weird")
    assert unknown_type.success is False
    assert "Unknown note type" in unknown_type.error


@pytest.mark.asyncio
async def test_update_note_not_found_and_success_paths(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    patterns_dir = vault / "Patterns"
    patterns_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(consolidated, "get_vault_path", lambda: vault)

    not_found = await update_note(
        db=DummyDB(),
        note_name="missing_note",
        new_insights="new insight",
    )
    assert not_found.success is False
    assert "not found" in not_found.error

    target = patterns_dir / "existing_note.md"
    target.write_text("# Existing")

    monkeypatch.setattr(
        consolidated,
        "update_note_internal",
        lambda filepath, insights, section: (
            filepath == target
            and insights == "new insight"
            and section == "Additional Insights",
            "updated",
        ),
    )

    updated = await update_note(
        db=DummyDB(),
        note_name="existing_note",  # verifies .md suffix auto-append
        new_insights="new insight",
    )
    assert updated.success is True
    assert updated.data["filepath"].endswith("existing_note.md")
