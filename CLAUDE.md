# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DSA Coach is an adaptive CLI tool for mastering Data Structures, Algorithms, and System Design for Principal Engineer interviews. Features AI-powered mentorship, spaced repetition, progress-based learning (0-100), and a comprehensive pattern-first curriculum.

## Core Development Principles

**Maintenance-First Philosophy:**
- Prefer small, reversible changes over large refactors
- Optimize for clarity and future maintainability
- Keep user-facing CLI output stable and readable
- Preserve backward compatibility for persisted data (SQLite schema)
- Avoid introducing new dependencies without clear UX or maintenance payoff

**Code Organization:**
- Keep functions short (~80 lines max)
- Separate pure logic from side effects (printing, file I/O, API calls, browser opening)
- When files exceed ~400 lines, extract modules
- Prefer pure functions, minimize global side-effects

**Data Safety:**
- `coach.db` is user data - never manually edit to "make things work"
- `quests.json` is versioned content - keep schema consistent
- When schema changes are needed, implement safe migrations with fallbacks

**Testing (TDD Enforced):**
- Write tests BEFORE implementing features
- All new features and refactors must have covering tests
- When fixing bugs, first write a test that reproduces the bug, then fix it
- Tests live in `tests/`, mirroring source structure
- Tests must not modify user data (use fixtures, temporary directories)
- Mock external API calls (LLMs) and heavy side effects (browser opening)

## ⚠️ CRITICAL: Storage Architecture

**SQLite (`coach.db`) is the SINGLE SOURCE OF TRUTH for all user progress data.**

### ALWAYS Use the Right Database Class

1. **ALWAYS use `Database`** for agent tools (async code) — this is the primary interface
2. **ALWAYS use `SyncDatabase`** for synchronous code (web dashboard, scripts)

### Quick Reference

```python
# For agent tools (async) — primary interface
from dsa_coach.storage.db import Database

@tool(name="my_tool", description="...", category="...")
async def my_tool(db: Database, user_id: str = "default") -> ToolResult:
    profile = await db.get_or_create_profile(user_id)
    patterns = await db.get_all_pattern_progress(user_id)
    return ToolResult(success=True, data={...})

# For synchronous code (dashboard, scripts)
from dsa_coach.storage.sync import SyncDatabase

def load_data():
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        completed = db.get_completed_quests()
        due_reviews = db.get_due_reviews()
```

### Key Database Methods

| Method | Description |
|--------|-------------|
| `get_or_create_profile()` | Get user profile, create if not exists |
| `get_all_pattern_progress()` | Get all pattern progress records |
| `get_completed_quests()` | Get all completed quest records |
| `get_due_reviews()` | Get quests due for spaced repetition |
| `upsert_pattern_progress(progress)` | Create/update pattern progress |
| `upsert_quest_completion(completion)` | Create/update quest completion |

## Agent Architecture

### Claude Agent SDK

The project uses the **Claude Agent SDK** for tool orchestration:

- **Agent**: `SDKCoachAgent` in `dsa_coach/agent/sdk_agent.py` (sole agent implementation)
- **Tools**: 15 workflow-level tools in `dsa_coach/tools/consolidated.py`

### Consolidated Tools

The agent uses 15 high-level workflow tools (`dsa_coach/tools/consolidated.py`):

**Tool Categories:**
- **Session & Quest (4)**: `get_dashboard`, `start_quest`, `complete_quest`, `get_hint`
- **Pattern (2)**: `list_patterns`, `get_pattern_details`
- **Learning (3)**: `diagnose_understanding`, `record_learning`, `get_teaching_context`
- **Progress (2)**: `get_progress_summary`, `record_review`
- **Code (2)**: `manage_solution`, `review_code`
- **Notes (2)**: `create_note`, `update_note`

**Internal Hooks**: Each tool has deterministic follow-up actions built-in (logging, milestones, note suggestions).

### ID Migration: Human-Readable Slugs

**Quest/Pattern IDs changed from cryptic codes to readable slugs:**
- Old: `ft_04_c1_p1` → New: `sliding_window_minimum_window_substring`
- Old: `ft_04` → New: `sliding_window`
- Mapping logic: `dsa_coach/id_mappings.py` (backward compatible)

### Workflow State Machine

Session modes guide tool availability and agent behavior:
- **GREETING**: Initial state, show dashboard
- **PRACTICING**: Working on a quest (problem-solving)
- **LEARNING**: Teaching a pattern (concept explanation)
- **REVIEWING**: Spaced repetition (review practice)
- **SIMULATING**: Mock interview mode

See `dsa_coach/agent/workflows.py` for state transitions.

## Development Commands

### Environment Setup

```bash
# Create virtual environment and install dependencies
uv venv && source .venv/bin/activate
uv sync

# Set up API keys for AI features (optional)
cp env.example .env
# Edit .env with ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### Running the Application

```bash
# Launch the interactive AI coaching agent
python coach.py

# Launch the Streamlit progress dashboard
python coach.py dashboard
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/storage/test_db.py

# Test harness for agent testing (see test_harness.py --help)
python test_harness.py --scenario basic_conversation
python test_harness.py hydrate  # Populate test data
```

## Architecture

### Core Components

**coach.py** - Thin CLI entrypoint
- Launches the agent interactive loop or Streamlit dashboard

**quests.json** - Quest database
- Hierarchical: curriculum → patterns → concepts → problems
- Human-readable IDs: `sliding_window_minimum_window_substring`

**coach.db** - SQLite database (SINGLE SOURCE OF TRUTH)
- Tables: sessions, messages, user_profiles, pattern_progress, quest_completions, concept_understanding, mistakes, daily_logs, milestones, teaching_history, schema_version

**Storage Module** (`dsa_coach/storage/`)
- **db.py**: Async `Database` class for agent tools
- **sync.py**: Sync `SyncDatabase` wrapper for dashboard/scripts
- **models.py**: Pydantic models for all entities

### Module Boundaries & Architecture Patterns

**Separation of Concerns:**

- **Tools** (`dsa_coach/tools/`): Agent-callable functions
  - **consolidated.py**: 15 workflow-level tools
  - **registry.py**: Tool registration with `@tool` decorator
  - All tools are async, use `Database` class
  - Return `ToolResult` with structured data

- **Domain** (`dsa_coach/domain/`): Pure business logic
  - No I/O, no printing, no API calls
  - Spaced repetition scheduling, XP calculations

- **Agent** (`dsa_coach/agent/`): AI agent system
  - `sdk_agent.py`: SDKCoachAgent (sole agent implementation)
  - `loop.py`: Main interactive loop
  - `session.py`: Session management
  - `workflows.py`: Session modes and state machine
  - `hooks.py`: PostToolUse hooks for deterministic follow-ups
  - `terminal.py`: Rich terminal UI rendering

**Data Flow:**
```
User Message → Agent → Tool Selection → Database Operations → Return ToolResult
                 ↓
           Format Response → Display in Terminal
```

### File Structure

```
dsa-coach/
├── coach.py              # Thin CLI entrypoint (agent + dashboard)
├── coach.db              # SQLite database - SINGLE SOURCE OF TRUTH
├── test_harness.py       # Agent testing CLI
├── quests.json           # Quest database
├── dsa_coach/
│   ├── main.py           # Package CLI entrypoint
│   ├── agent/            # AI agent system
│   │   ├── sdk_agent.py  # SDKCoachAgent (sole agent)
│   │   ├── loop.py       # Main interactive loop
│   │   ├── session.py    # Session management
│   │   ├── terminal.py   # Rich terminal UI
│   │   ├── hooks.py      # PostToolUse hooks
│   │   └── workflows.py  # Session modes & state machine
│   ├── tools/            # Agent-callable tools
│   │   ├── consolidated.py  # 15 workflow-level tools
│   │   └── registry.py     # Tool registration & execution
│   ├── storage/          # Database module
│   │   ├── db.py         # Async Database (agent tools)
│   │   ├── sync.py       # SyncDatabase (dashboard, scripts)
│   │   ├── models.py     # Pydantic models
│   │   └── migrations.py # JSON→SQLite migration
│   ├── ai/               # AI client & system prompts
│   │   ├── client.py     # LLM provider abstraction
│   │   └── prompts.py    # System prompts & student context
│   ├── domain/           # Pure business logic
│   │   └── scheduling.py # Spaced repetition
│   ├── obsidian/         # Obsidian note integration
│   │   ├── analyzer.py   # Solution analysis
│   │   ├── note_generator.py # Note content generation
│   │   └── writer.py     # File writing
│   ├── web/              # Streamlit dashboard
│   │   ├── dashboard.py  # Dashboard app
│   │   └── data.py       # Data loading
│   ├── curriculum.py     # Quest loading & lookup
│   ├── id_mappings.py    # Legacy→slug ID conversion
│   ├── solution.py       # Solution file management
│   ├── paths.py          # Path constants
│   ├── ui.py             # CLI formatting utilities
│   └── logging_config.py # Logging setup
├── scripts/              # Maintenance scripts
│   ├── hydrate_test_data.py  # Test data population
│   └── cleanup_db.py        # Database cleanup
├── tests/                # Test suite
└── solutions/            # User solution files
```

### Key Patterns (Fast Track — Google L6 Sprint)

16 patterns, 120 hours, 85 problems:
- **big_o_analysis**, **arrays_hashing**, **two_pointers**, **sliding_window**, **binary_search**, **recursion**, **trees**, **graphs**, **dynamic_programming**, **design**, **backtracking**, **heaps**, **linked_lists**, **monotonic_stack**, **intervals**, **trie**

### Adaptive Learning Algorithm

Quest selection priority:
1. Spaced repetition items due today
2. Patterns with lowest progress scores
3. Next unstarted quest in curriculum order

Progress = `(earned_points / (quests_total * 15)) * 100`, where each quest earns 15 points (no hints) or 10 points (with hints), capped at 100

### Spaced Repetition Schedule

Intervals: `[1, 3, 7, 14, 30]` days, indexed by `review_count`:
- 1st review: 1 day after completion
- 2nd review: 3 days later
- 3rd review: 7 days later
- 4th review: 14 days later
- Long-term: 30 day intervals
- Failed review resets to 1 day

## Development Conventions

### Python Style

**Language Version:** Python 3.11+
- Modern type hints: `list[int]`, `dict[str, Any]`, `str | None`
- Use `pathlib.Path` for file operations

**Type Hints:**
- Add type hints to all public functions
- Add docstrings for business logic
- Use Pydantic models for data validation

**Error Handling:**
- Prefer user-friendly errors (short message + how to fix)
- Avoid stack traces for expected errors
- Fail loudly for unexpected errors with actionable context

**File I/O:**
- Atomic writes for user data files
- Implement migrations for schema changes
- Never silently discard user data

### Code Quality

**Linting Tools:**
- **Ruff** (v0.14.10): Fast linter and formatter (88 char line length)
- **Mypy** (v1.19.1): Static type checker
- **Pre-commit** (v4.5.1): Git hooks framework

**Running Linters:**
```bash
ruff check . --fix    # Auto-fix issues
ruff format .         # Format code
mypy dsa_coach/       # Type check
```

**Best Practices:**
- Run linters before committing
- Follow 88 char line length
- Remove unused imports/variables
- Add type hints to new functions

### Creating New Agent Tools

```python
from dsa_coach.tools.registry import tool, ToolResult
from dsa_coach.storage.db import Database

@tool(name="my_tool", description="...", category="learning")
async def my_tool(
    db: Database,
    user_id: str = "default",
    my_param: str = ""
) -> ToolResult:
    """Detailed description."""
    try:
        data = await db.get_something(user_id)
        return ToolResult(success=True, data={"key": "value"})
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

**Tool Best Practices:**
- Add to `consolidated.py` as workflow-level operations
- Include deterministic follow-ups (logging, milestones) within the tool
- Handle ID normalization for backward compatibility
- Return structured data in `ToolResult.data`
- Never print directly - let agent format output

## Environment Variables

**Agent Configuration:**
- `LLM_PROVIDER`: "anthropic" (default) or "openai"
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`: API keys

**UI Configuration:**
- `COACH_WIDTH`: Terminal width (default: 88)
- `COACH_CHAT_STYLE`: "discord" or "classic"
- `COACH_AUTOSAVE`: Auto-save conversations (default: enabled)

## Known Limitations

- SQLite database not backed up automatically
- Single user support (hardcoded `user_id="default"`)
- AI features require external API keys
- ID migration is backward compatible (old `ft_*` IDs auto-converted)
