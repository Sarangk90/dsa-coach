"""Tests for main interactive agent loop control flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

from dsa_coach.agent import loop


@dataclass
class FakeResponse:
    content: str = ""
    token_usage: Any = None
    tool_calls_made: list[dict] = field(default_factory=list)
    tool_errors: list[dict] = field(default_factory=list)
    state_updated: bool = False
    error: str | None = None


class FakeUI:
    """Minimal terminal UI test double for loop integration tests."""

    def __init__(self, inputs: list[Any]):
        self.inputs = list(inputs)
        self.infos: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.messages: list[tuple[str, str]] = []
        self.tool_activity: list[str] = []
        self.tool_errors: list[tuple[str, str]] = []
        self.help_count = 0
        self.dashboard_count = 0
        self.goodbye_count = 0
        self.session_picker_count = 0
        self.conversation_history_count = 0
        self.token_updates: list[Any] = []
        self.reasoning: list[str] = []
        self.start_timer_count = 0
        self.selection: int | None = None
        self.selection_calls = 0

    def clear(self) -> None:
        pass

    def print_header(self) -> None:
        pass

    def render_info(self, message: str) -> None:
        self.infos.append(message)

    def render_success(self, message: str) -> None:
        self.successes.append(message)

    def render_error(self, message: str) -> None:
        self.errors.append(message)

    def render_dashboard(self, state: dict) -> None:
        self.dashboard_count += 1

    def render_welcome(self, greeting: str) -> None:
        self.messages.append(("welcome", greeting))

    def start_session_timer(self) -> None:
        self.start_timer_count += 1

    async def get_input(self) -> str | None:
        if not self.inputs:
            raise EOFError
        item = self.inputs.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def render_help(self) -> None:
        self.help_count += 1

    def render_session_picker(self, sessions: list[dict]) -> None:
        self.session_picker_count += 1

    async def get_session_selection(self, max_index: int) -> int | None:
        self.selection_calls += 1
        return self.selection

    def render_conversation_history(self, messages: list[dict]) -> None:
        self.conversation_history_count += 1

    def render_message(self, role: str, content: str) -> None:
        self.messages.append((role, content))

    def render_thinking(self) -> None:
        pass

    def render_reasoning(self, content: str) -> None:
        self.reasoning.append(content)

    def update_token_usage(self, token_usage: Any) -> None:
        self.token_updates.append(token_usage)

    def render_tool_activity(self, tool_name: str) -> None:
        self.tool_activity.append(tool_name)

    def render_tool_error(self, tool_name: str, error: str) -> None:
        self.tool_errors.append((tool_name, error))

    def render_goodbye(self) -> None:
        self.goodbye_count += 1


class FakeDB:
    def __init__(self, sessions: list[dict] | None = None):
        self.sessions = sessions or []
        self.connected = False
        self.closed = False
        self.list_sessions_calls: list[dict] = []

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.closed = True

    async def list_sessions(
        self, limit: int = 10, exclude_session_id: str | None = None
    ) -> list[dict]:
        self.list_sessions_calls.append(
            {"limit": limit, "exclude_session_id": exclude_session_id}
        )
        return self.sessions


class FakeSessionManager:
    def __init__(self):
        self.session = SimpleNamespace(id="current-session")
        self._messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        self.resume_calls: list[str] = []
        self.resume_result = True

    async def resume_by_id(self, session_id: str) -> bool:
        self.resume_calls.append(session_id)
        if self.resume_result:
            self.session = SimpleNamespace(id=session_id)
        return self.resume_result

    def get_display_messages(self) -> list[dict]:
        return self._messages


class FakeAgent:
    def __init__(self, db: FakeDB):
        self.db = db
        self.dashboard = {"profile": {"quests_completed": 0}}
        self.session = FakeSessionManager()
        self.initialize_called = False
        self.refresh_dashboard_calls = 0
        self.refresh_context_calls = 0
        self.run_calls: list[str] = []
        self.responses: list[FakeResponse] = []

    async def initialize(self) -> None:
        self.initialize_called = True

    async def get_greeting(self) -> str:
        return "Welcome back!"

    async def _refresh_dashboard(self) -> None:
        self.refresh_dashboard_calls += 1

    async def _refresh_student_context(self) -> None:
        self.refresh_context_calls += 1

    async def run(self, user_input: str, on_reasoning=None) -> FakeResponse:
        self.run_calls.append(user_input)
        if on_reasoning is not None:
            on_reasoning("intermediate reasoning")
        if self.responses:
            return self.responses.pop(0)
        return FakeResponse(content="default response")


@pytest.mark.asyncio
async def test_run_agent_loop_handles_help_then_quit(monkeypatch):
    fake_ui = FakeUI(inputs=["help", "quit"])
    fake_db = FakeDB()
    fake_agent = FakeAgent(fake_db)

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert fake_db.connected is True
    assert fake_db.closed is True
    assert fake_ui.help_count == 1
    assert fake_ui.goodbye_count == 1
    assert fake_ui.start_timer_count == 1
    assert ("welcome", "Welcome back!") in fake_ui.messages


@pytest.mark.asyncio
async def test_run_agent_loop_shows_resume_message_when_no_prior_sessions(monkeypatch):
    fake_ui = FakeUI(inputs=["/resume", "quit"])
    fake_db = FakeDB(sessions=[])
    fake_agent = FakeAgent(fake_db)

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert fake_db.list_sessions_calls == [
        {"limit": 10, "exclude_session_id": "current-session"}
    ]
    assert "No previous sessions to resume." in fake_ui.infos


@pytest.mark.asyncio
async def test_run_agent_loop_processes_agent_response_and_state_refresh(monkeypatch):
    fake_ui = FakeUI(inputs=["work on graphs", "quit"])
    fake_db = FakeDB()
    fake_agent = FakeAgent(fake_db)
    token_usage = object()
    fake_agent.responses = [
        FakeResponse(
            content="Let's continue with graphs.",
            token_usage=token_usage,
            tool_calls_made=[{"name": "list_patterns"}],
            tool_errors=[{"tool": "complete_quest", "error": "already complete"}],
            state_updated=True,
        )
    ]

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert fake_agent.run_calls == ["work on graphs"]
    assert fake_agent.refresh_dashboard_calls == 1
    assert fake_ui.token_updates == [token_usage]
    assert fake_ui.tool_activity == ["list_patterns"]
    assert fake_ui.tool_errors == [("complete_quest", "already complete")]
    assert ("assistant", "Let's continue with graphs.") in fake_ui.messages
    assert fake_ui.reasoning == ["intermediate reasoning"]


@pytest.mark.asyncio
async def test_run_agent_loop_runs_migration_and_surfaces_error(monkeypatch):
    fake_ui = FakeUI(inputs=["quit"])
    fake_db = FakeDB()
    fake_agent = FakeAgent(fake_db)

    async def migration_needed(_db):
        return True

    async def failed_migration(_db):
        return {"status": "error", "reason": "bad payload"}

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_needed)
    monkeypatch.setattr(loop, "migrate_from_json", failed_migration)

    await loop.run_agent_loop()

    assert "Migrating existing progress to new format..." in fake_ui.infos
    assert "Migration error: bad payload" in fake_ui.errors


@pytest.mark.asyncio
async def test_run_agent_loop_handles_cancelled_input(monkeypatch):
    fake_ui = FakeUI(inputs=[None, "quit"])
    fake_db = FakeDB()
    fake_agent = FakeAgent(fake_db)

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert "Message cancelled." in fake_ui.infos
    assert fake_agent.run_calls == []


@pytest.mark.asyncio
async def test_run_agent_loop_resume_success_renders_history_and_refreshes_state(
    monkeypatch,
):
    fake_ui = FakeUI(inputs=["/resume", "quit"])
    fake_ui.selection = 0
    fake_db = FakeDB(
        sessions=[
            {
                "id": "prior-session",
                "updated_at": "2026-02-01T10:00:00",
                "first_message": "Need help with trees",
                "current_pattern": "trees",
                "current_quest": "trees_max_depth",
                "message_count": 4,
            }
        ]
    )
    fake_agent = FakeAgent(fake_db)

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)
    monkeypatch.setattr(loop, "format_time_ago", lambda _dt: "2 days ago")

    await loop.run_agent_loop()

    assert fake_ui.session_picker_count == 1
    assert fake_ui.selection_calls == 1
    assert fake_agent.session.resume_calls == ["prior-session"]
    assert fake_agent.refresh_context_calls == 1
    assert fake_agent.refresh_dashboard_calls == 1
    assert fake_ui.conversation_history_count == 1
    assert any("Resumed session from 2 days ago" in msg for msg in fake_ui.successes)


@pytest.mark.asyncio
async def test_run_agent_loop_resume_cancelled_selection(monkeypatch):
    fake_ui = FakeUI(inputs=["/resume", "quit"])
    fake_ui.selection = None
    fake_db = FakeDB(
        sessions=[
            {
                "id": "prior-session",
                "updated_at": "2026-02-01T10:00:00",
                "first_message": "Need help",
                "current_pattern": "trees",
                "current_quest": "q",
                "message_count": 2,
            }
        ]
    )
    fake_agent = FakeAgent(fake_db)

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert "Resume cancelled." in fake_ui.infos
    assert fake_agent.session.resume_calls == []


@pytest.mark.asyncio
async def test_run_agent_loop_resume_failure_shows_error(monkeypatch):
    fake_ui = FakeUI(inputs=["/resume", "quit"])
    fake_ui.selection = 0
    fake_db = FakeDB(
        sessions=[
            {
                "id": "bad-session",
                "updated_at": "2026-02-01T10:00:00",
                "first_message": "Need help",
                "current_pattern": "trees",
                "current_quest": "q",
                "message_count": 2,
            }
        ]
    )
    fake_agent = FakeAgent(fake_db)
    fake_agent.session.resume_result = False

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert "Failed to resume session." in fake_ui.errors


@pytest.mark.asyncio
async def test_run_agent_loop_keyboard_interrupt_during_input_is_handled(monkeypatch):
    fake_ui = FakeUI(inputs=[KeyboardInterrupt(), "quit"])
    fake_db = FakeDB()
    fake_agent = FakeAgent(fake_db)

    async def migration_not_needed(_db):
        return False

    monkeypatch.setattr(loop, "TerminalUI", lambda: fake_ui)
    monkeypatch.setattr(loop, "Database", lambda *args, **kwargs: fake_db)
    monkeypatch.setattr(loop, "SDKCoachAgent", lambda db: fake_agent)
    monkeypatch.setattr(loop, "check_migration_needed", migration_not_needed)

    await loop.run_agent_loop()

    assert any("Use 'quit' to exit" in info for info in fake_ui.infos)
