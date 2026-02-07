"""Regression tests for Obsidian writer file operations."""

from __future__ import annotations

from pathlib import Path

from dsa_coach.obsidian import writer


def test_get_vault_path_env_handling(monkeypatch, tmp_path):
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    assert writer.get_vault_path() is None

    missing = tmp_path / "missing"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(missing))
    assert writer.get_vault_path() is None

    existing = tmp_path / "vault"
    existing.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(existing))
    assert writer.get_vault_path() == existing


def test_ensure_structure_and_note_exists(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))

    structure = writer._ensure_vault_structure()  # noqa: SLF001
    assert structure["vault"] == vault
    assert (vault / "Patterns").exists()
    assert (vault / "Problems").exists()
    assert (vault / "Patterns" / "Advanced").exists()

    assert writer.note_exists("missing.md", "pattern") is False
    (vault / "Patterns" / "present.md").write_text("x", encoding="utf-8")
    assert writer.note_exists("present.md", "pattern") is True


def test_ensure_structure_returns_error_when_directory_creation_fails(
    monkeypatch, tmp_path
):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))

    original_mkdir = Path.mkdir

    def failing_mkdir(self, *args, **kwargs):
        if self.name == "Patterns":
            raise OSError("mkdir denied")
        return original_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)
    structure = writer._ensure_vault_structure()  # noqa: SLF001

    assert structure["vault"] == vault
    assert structure["patterns"] is None
    assert structure["problems"] is None
    assert "mkdir denied" in str(structure["error"] or "")


def test_write_note_create_conflict_and_overwrite(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))

    success, message, path = writer.write_note(
        content="# First",
        filename="sample.md",
        note_type="pattern",
    )
    assert success is True
    assert path is not None and path.exists()
    assert "Note created" in message
    assert path.read_text(encoding="utf-8") == "# First"

    conflict_success, conflict_message, conflict_path = writer.write_note(
        content="# Second",
        filename="sample.md",
        note_type="pattern",
        overwrite=False,
    )
    assert conflict_success is False
    assert "already exists" in conflict_message
    assert conflict_path == path

    overwrite_success, _, overwrite_path = writer.write_note(
        content="# Overwritten",
        filename="sample.md",
        note_type="pattern",
        overwrite=True,
    )
    assert overwrite_success is True
    assert overwrite_path == path
    assert path.read_text(encoding="utf-8") == "# Overwritten"


def test_write_note_and_update_note_error_and_success_paths(monkeypatch, tmp_path):
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    success, message, path = writer.write_note(
        content="x",
        filename="a.md",
        note_type="problem",
    )
    assert success is False
    assert "not configured" in message
    assert path is None

    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))
    note_path = vault / "Patterns" / "to_update.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("# Existing", encoding="utf-8")

    missing_success, missing_message = writer.update_note(
        vault / "Patterns" / "missing.md",
        "new section",
    )
    assert missing_success is False
    assert "does not exist" in missing_message

    updated_success, updated_message = writer.update_note(
        note_path,
        "new content",
        section_title="New Insights",
    )
    assert updated_success is True
    assert "Note updated" in updated_message
    updated = note_path.read_text(encoding="utf-8")
    assert "## New Insights" in updated
    assert "new content" in updated

    # Verify append without section title.
    writer.update_note(note_path, "tail content", section_title="")
    assert "tail content" in note_path.read_text(encoding="utf-8")
