# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DSA Coach is an adaptive CLI tool for mastering Data Structures, Algorithms, and System Design for Google L6 interviews. Features AI-powered mentorship (Claude Agent SDK), spaced repetition, progress-based learning (0-100), and a pattern-first curriculum (16 patterns, 85 problems across 3 slices).

## Development Commands

```bash
# Setup
uv venv && source .venv/bin/activate && uv sync

# Run the app
python coach.py                    # Interactive AI coaching agent
python coach.py dashboard          # Streamlit progress dashboard
python coach.py dashboard --daemon # Dashboard in background
python coach.py dashboard --stop   # Stop background dashboard

# Testing
pytest                             # All tests (skips integration + harness)
pytest tests/storage/test_db.py    # Single test file
pytest -k "test_name"              # Single test by name
python test_harness.py --scenario basic_conversation  # Agent integration test
python test_harness.py hydrate     # Populate test data

# Linting (also runs via pre-commit hooks on commit)
ruff check . --fix                 # Lint + auto-fix
ruff format .                      # Format (88 char lines, double quotes)
mypy dsa_coach/                    # Type check

# Makefile shortcuts
make check                         # lint + format + typecheck + test
make run                           # python coach.py
make dashboard                     # python coach.py dashboard
make clean                         # Remove __pycache__, .pytest_cache, etc.
```

**pytest config:** `asyncio_mode = "auto"`, integration tests marked with `@pytest.mark.integration` (skipped by default), harness tests in `tests/harness/` ignored by default.

## Core Development Principles

- **Maintenance-first**: Small, reversible changes. No new dependencies without clear payoff.
- **Data safety**: `coach.db` is user data — never manually edit. `quests.json` is versioned content — keep schema consistent. Schema changes need safe migrations with fallbacks.
- **TDD enforced**: Write tests BEFORE implementing. Bug fixes start with a reproducing test. Tests must not modify user data (use fixtures/temp dirs). Mock LLM calls and side effects.
- **Code organization**: Functions ~80 lines max. Files ~400 lines max, then extract. Separate pure logic from side effects.
- **LLM cost control**: Never send `quests.json` wholesale to the model. Prefer deterministic/local logic; use LLM only for mentorship text. If API key is unavailable, CLI must still work with a clear error message.

## ⚠️ CRITICAL: Storage Architecture

**SQLite (`coach.db`) is the SINGLE SOURCE OF TRUTH for all user progress data.** (`progress.json` is legacy and no longer exists.)

| Context | Class | Import |
|---------|-------|--------|
| Agent tools (async) | `Database` | `from dsa_coach.storage.db import Database` |
| Dashboard/scripts (sync) | `SyncDatabase` | `from dsa_coach.storage.sync import SyncDatabase` |

```python
# Async (agent tools) — primary interface
@tool(name="my_tool", description="...", category="consolidated")
async def my_tool(db: Database, user_id: str = "default") -> ToolResult:
    profile = await db.get_or_create_profile(user_id)
    patterns = await db.get_all_pattern_progress(user_id)
    return ToolResult(success=True, data={...})

# Sync (dashboard, scripts)
with SyncDatabase() as db:
    profile = db.get_or_create_profile()
```

**Key methods:** `get_or_create_profile()`, `get_all_pattern_progress()`, `get_completed_quests()`, `get_due_reviews()`, `upsert_pattern_progress()`, `upsert_quest_completion()`

**Tables:** sessions, messages, user_profiles, pattern_progress, quest_completions, concept_understanding, mistakes, daily_logs, milestones, teaching_history, schema_version

## Architecture

### Data Flow

```
User Input → prompt_toolkit → Agent Loop → SDKCoachAgent.run()
  → LLM (Anthropic/OpenAI) → Tool Selection → Database Ops → ToolResult
  → LLM formats response → Rich Terminal Display
```

### Module Boundaries

- **`coach.py`** — Thin CLI entrypoint. Two modes: agent (default) or `dashboard`.
- **`dsa_coach/constants.py`** — Named business-rule constants (thresholds, intervals, validation sets).
- **`dsa_coach/curriculum.py`** — Canonical curriculum data access (cached). Single source for quest/pattern lookup from `quests.json`.
- **`dsa_coach/agent/`** — AI agent system
  - `sdk_agent.py`: `SDKCoachAgent` — sole agent implementation using Claude Agent SDK. Handles tool orchestration loop (up to 5 iterations), extended thinking with signature replay, workflow state persistence.
  - `loop.py`: Main interactive loop. Special commands: `quit/exit`, `help`, `dashboard`, `/resume`. Uses `prompt_toolkit` for multiline input (Ctrl+J newline, Enter submit).
  - `session.py`: `SessionManager` — always starts fresh sessions. `/resume` explicitly restores previous sessions. Stores thinking + thinking_signature for extended thinking replay.
  - `workflows.py`: Session mode state machine (GREETING → PRACTICING/LEARNING/REVIEWING/SIMULATING). Mode-specific tool availability sets.
  - `terminal.py`: Rich terminal UI. Session timer, token usage tracking (with 75%+ warning), session picker for `/resume`, conversation history rendering.
- **`dsa_coach/tools/`** — Agent-callable functions (13 tools, all async, `category="consolidated"`)
  - `consolidated.py`: Re-export facade — imports all tools from the category modules below.
  - `session_quest.py`: 4 tools — `get_dashboard`, `start_quest`, `complete_quest`, `get_hint`.
  - `pattern_learning.py`: 5 tools — `list_patterns`, `get_pattern_details`, `diagnose_understanding`, `record_learning`, `get_teaching_context`.
  - `progress_review.py`: 4 tools — `get_progress_summary`, `record_review`, `manage_solution`, `review_code`.
  - `quest_helpers.py`: Shared helpers — quest lookup, ID normalization, recommendation engine, `should_create_note()`.
  - `registry.py`: `@tool` decorator, `ToolRegistry`, `ToolResult`. Auto-injects `db` and `user_id` params.
- **`dsa_coach/mcp/`** — MCP integration for Obsidian notes (`client.py`: spawns `mcp-obsidian` server, discovers tools, routes calls). Gracefully disabled when `OBSIDIAN_API_KEY` not set.
- **`dsa_coach/storage/`** — Database module (mixin-based architecture)
  - `db.py`: `Database` class composed from 5 domain mixins + connection management + migrations.
  - `db_sessions.py`: `SessionMixin` — session and message CRUD.
  - `db_profiles.py`: `ProfileMixin` — user profile CRUD.
  - `db_progress.py`: `ProgressMixin` — pattern progress and derived stats.
  - `db_quests.py`: `QuestMixin` — quest completion CRUD.
  - `db_learning.py`: `LearningMixin` — concepts, mistakes, milestones, teaching history, daily logs.
  - `schema.py`: SQL schema definition (`SCHEMA_SQL` constant).
  - `sync.py`: `SyncDatabase` sync wrapper, `models.py`: Pydantic models, `migrations.py`: JSON→SQLite migration.
- **`dsa_coach/ai/`** — LLM provider and system prompts
  - `client.py`: Anthropic `claude-sonnet-4-5` default, OpenAI `gpt-5.2`, extended thinking with configurable budget.
  - `system_prompt.py`: Static `COACH_AGENT_SYSTEM_PROMPT` (~740 lines, 13 teaching pillars).
  - `student_context.py`: `build_student_context()` + format helpers for dynamic context injection.
  - `prompts.py`: Re-export facade + `get_agent_system_prompt()` composition function.
- **`dsa_coach/web/`** — Streamlit dashboard (uses `SyncDatabase`)

### Consolidated Tools (13 local + MCP)

- **Session & Quest (4)**: `get_dashboard`, `start_quest`, `complete_quest`, `get_hint`
- **Pattern (2)**: `list_patterns`, `get_pattern_details`
- **Learning (3)**: `diagnose_understanding`, `record_learning`, `get_teaching_context`
- **Progress (2)**: `get_progress_summary`, `record_review`
- **Code (2)**: `manage_solution`, `review_code`
- **Notes**: Provided by `mcp-obsidian` MCP server when `OBSIDIAN_API_KEY` is set

### Workflow State Machine

Session modes in `dsa_coach/agent/workflows.py`:
- **GREETING**: Initial state, show dashboard
- **PRACTICING**: Working on a quest (problem-solving)
- **LEARNING**: Teaching a pattern (concept explanation)
- **REVIEWING**: Spaced repetition review
- **SIMULATING**: Mock interview mode

Tool availability is mode-specific. Universal tools (available in all modes): `get_dashboard`, `list_patterns`, `get_pattern_details`. Obsidian MCP tools are available in all modes when connected.

### ID Migration

Quest/Pattern IDs use human-readable slugs (e.g. `sliding_window_minimum_window_substring`). Legacy `ft_*` IDs are auto-converted via `dsa_coach/id_mappings.py`.

## Creating New Agent Tools

```python
from dsa_coach.tools.registry import tool, ToolResult
from dsa_coach.storage.db import Database

@tool(name="my_tool", description="...", category="consolidated")
async def my_tool(db: Database, user_id: str = "default", my_param: str = "") -> ToolResult:
    """Detailed description."""
    data = await db.get_something(user_id)
    return ToolResult(success=True, data={"key": "value"})
```

- Add to the appropriate category file (`session_quest.py`, `pattern_learning.py`, or `progress_review.py`) and re-export from `consolidated.py`
- Handle ID normalization for backward compatibility (`id_mappings.py`)
- Return structured data in `ToolResult.data` — never print directly
- `db` and `user_id` params are injected by the registry executor (skip in schema)
- Include deterministic internal hooks (logging, milestone checks) within the tool

## Python Style

- Python 3.11+, modern type hints (`list[int]`, `str | None`), `pathlib.Path` for file ops
- Pydantic models for data validation (`dsa_coach/storage/models.py`)
- Uses `progress` field consistently (not `confidence`) — renamed project-wide
- Ruff (88 char lines, double quotes), Mypy, pre-commit hooks enforce on commit

## Environment Variables

- `LLM_PROVIDER`: "anthropic" (default) or "openai"
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`: API keys
- `COACH_WIDTH`: Terminal width (default: 88)
- `THINKING_BUDGET`: Extended thinking token budget (default: 10000)
- `OBSIDIAN_API_KEY`: Obsidian Local REST API key (enables MCP note tools)
- `OBSIDIAN_MCP_COMMAND`: Command to run mcp-obsidian (default: "uvx")

## Known Limitations

- Single user support (hardcoded `user_id="default"`)
- AI features require external API keys
