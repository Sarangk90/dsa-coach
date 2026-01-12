# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DSA Coach is an adaptive CLI tool for mastering Data Structures, Algorithms, and System Design for Principal Engineer interviews. It features AI-powered mentorship, spaced repetition, confidence-based learning (0-100), and a comprehensive pattern-first curriculum.

## ⚠️ CRITICAL: Storage Architecture (December 2024)

**SQLite (`coach.db`) is the SINGLE SOURCE OF TRUTH for all user progress data.**

### What This Means for Development

1. **NEVER use `progress.json`** - It is deprecated and will be removed
2. **NEVER import from `dsa_coach.progress`** - Functions emit deprecation warnings
3. **ALWAYS use `SyncDatabase`** for CLI commands (synchronous code)
4. **ALWAYS use `Database`** for agent tools (async code)

### Quick Reference

```python
# ✅ CORRECT - For CLI commands (synchronous)
from dsa_coach.storage.sync import SyncDatabase

def my_command():
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        completed = db.get_completed_quests()
        due_reviews = db.get_due_reviews()

        # For functions expecting legacy progress dict format:
        progress_compat = db.build_progress_compat()

# ✅ CORRECT - For agent tools (async)
from dsa_coach.storage.db import Database

async def my_tool(db: Database, user_id: str = "default"):
    profile = await db.get_or_create_profile(user_id)
    progress_compat = await db.build_progress_compat(user_id)

# ❌ WRONG - DEPRECATED
from dsa_coach.progress import load_progress, save_progress  # DON'T DO THIS
progress = load_progress()  # Emits DeprecationWarning
```

### The `build_progress_compat()` Method

Some legacy functions in `curriculum.py` and `selection.py` expect a progress dict. Use `build_progress_compat()` to create a compatible dict from database data:

```python
with SyncDatabase() as db:
    progress_compat = db.build_progress_compat()
    # Returns:
    # {
    #     "profile": {"name": str, "current_quest": str|None, "active_mode": str},
    #     "pattern_proficiency": {pattern_id: {"confidence": int, "attempts": int, ...}},
    #     "completed_quests": {quest_id: True, ...},
    #     "problems_solved": {quest_id: True, ...},
    #     "patterns_completed": [pattern_id, ...],  # Derived from mastered flag
    #     "patterns_in_progress": [pattern_id, ...],  # Has quests but not mastered
    # }

    # Now use with legacy functions:
    from dsa_coach.curriculum import get_active_mode, is_pattern_unlocked
    mode = get_active_mode(progress_compat)
    unlocked = is_pattern_unlocked("ft_02", progress_compat, mode)
```

## Development Commands

### Environment Setup

#### Prerequisites
Install uv (if not already installed):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

#### Setup
```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install all dependencies (including dev tools)
uv sync

# Or install production dependencies only
uv pip install -e .

# Set up API keys for AI features (optional)
cp env.example .env
# Edit .env with ANTHROPIC_API_KEY or OPENAI_API_KEY
```

**Note:** `uv sync` installs both main dependencies and dev dependencies (pytest, ruff, mypy, pre-commit). Use `uv pip install -e .` if you only need runtime dependencies.

### Running the Application

#### Interactive Menu (Recommended)
```bash
# Launch interactive menu with dashboard and numbered options
python coach-menu.py
```

The interactive menu provides:
- Visual dashboard showing progress, current quest, weak patterns
- Numbered menu (no need to remember command syntax)
- Smart alerts for due reviews
- Auto-refresh after each command

#### Traditional CLI Commands
```bash
python coach.py start          # Initialize user profile
python coach.py status         # View progress and pattern confidence
python coach.py today          # Daily schedule and recommendations
python coach.py next           # Get optimal next quest
python coach.py done           # Mark current quest complete
python coach.py hint           # Get adaptive hints
python coach.py review <file>  # Request AI code review
python coach.py recall         # Spaced repetition practice
python coach.py learn [pattern]# Interactive learning session
python coach.py design [name]  # System design interview
python coach.py sessions       # List saved conversations
python coach.py mistakes       # Review mistake journal
python coach.py summary        # Full progress dump
```

### Testing

#### Test Harness (Recommended for Agent Testing)

The test harness (`test_harness.py`) enables programmatic testing of the agent with conversation management and state verification. **Use this when testing agent behavior, tool calls, or state changes.**

**Quick Start:**
```bash
# Run a predefined test scenario
python test_harness.py --scenario basic_conversation

# Single commands
python test_harness.py hydrate                           # Populate test data
python test_harness.py send "What should I work on?"     # Send message
python test_harness.py inspect patterns                  # Check database state
python test_harness.py inspect mistakes                  # Check recorded mistakes
```

**Interactive JSON Mode (for scripted testing):**
```bash
python test_harness.py --json
# Then send JSON commands:
{"action": "hydrate"}
{"action": "send", "message": "I want to learn binary search"}
{"action": "inspect", "entity": "patterns"}
{"action": "snapshot"}
{"action": "diff"}
```

**Available Scenarios:**
- `basic_conversation` - Greeting, questions, pattern info
- `progress_tracking` - Complete a quest and verify state changes
- `mistake_recording` - Report a mistake and verify it's recorded
- `teaching_flow` - Learning session with concept understanding

**Inspect Entities:**
- `profile` - User profile
- `patterns` - Pattern progress (confidence, mastery)
- `quests` - Completed quests
- `mistakes` - Recorded mistakes with recurrence tracking
- `milestones` - Achievements
- `teaching` - Teaching history (what was explained)
- `concepts` - Concept understanding records
- `reviews` - Quests due for spaced repetition

**What the Harness Verifies:**
- ✅ Agent responses are appropriate
- ✅ Tools are called correctly (see `tools_used` in response)
- ✅ Database state updates after tool calls (use `snapshot` → action → `diff`)
- ✅ Mistakes, teaching, and learning are recorded automatically
- ✅ Memory is incorporated into coaching (past mistakes influence recommendations)

**Using in Pytest:**
```python
import pytest
from tests.harness import CoachTestHarness

@pytest.mark.asyncio
async def test_agent_records_mistake(tmp_path):
    async with CoachTestHarness(db_path=tmp_path / "test.db", auto_hydrate=True) as harness:
        # Take snapshot before
        before = await harness.snapshot()
        
        # Send message describing a mistake
        response = await harness.send("I made an off-by-one error on ft_04_c1_p1")
        
        # Check what changed
        after = await harness.snapshot()
        diff = harness.diff_snapshot(before, after)
        
        # Verify mistake was recorded
        assert "mistakes_added" in diff
```

#### Test Data Hydration
Use the hydration script to populate the database with realistic test data:
```bash
# Populate database with test data (idempotent)
python scripts/hydrate_test_data.py

# Reset database and repopulate (destructive)
python scripts/hydrate_test_data.py --reset
```

The script creates:
- User profile (Alex Chen)
- Pattern progress (various mastery levels)
- Quest completions (10 quests, some with reviews due)
- Daily logs (7 days of activity)
- Milestones (pattern mastered, streaks)
- Mistakes (including recurring off_by_one)
- Teaching history and concept understanding

#### Manual CLI Testing
```bash
# Test basic commands
python coach.py status    # Should show progress from SQLite
python coach.py next      # Should recommend based on weak patterns
python coach.py summary   # Full progress dump
python coach.py mistakes  # Should show recurring mistake patterns
python coach.py recall    # Should list 6 due reviews (with test data)

# Test interactive menu
python coach-menu.py
```

#### Agent Mode Testing (Programmatic)
Test the agent without terminal UI:
```python
import asyncio
from dsa_coach.storage.db import Database
from dsa_coach.agent.agent import CoachAgent

async def test_agent():
    db = Database()
    await db.connect()

    agent = CoachAgent(db)
    await agent.initialize()

    # Check student context was loaded
    print(agent._student_context[:500])

    # Test agent response
    response = await agent.run("What should I work on next?")
    print(response.content)
    print(f"Tools used: {response.tool_calls_made}")

    await db.close()

asyncio.run(test_agent())
```

#### Verification Checklist (December 2024 Migration)
After migration, verify:
- [x] Dashboard and agent show same "due for review" count
- [x] All CLI commands work with SQLite
- [x] Agent loads student context from database
- [x] Tools update database correctly (confidence, completions)
- [x] No JSON file reads/writes occurring

## Architecture

### Core Components

**coach.py** - Main CLI orchestrator
- Command dispatcher using sys.argv
- Progress tracking and persistence (SQLite database: coach.db)
- Quest selection algorithm (adaptive learning + spaced repetition)
- Confidence tracking (0-100 per pattern)
- File generation for solution templates
- Integration with mentor.py for AI features

**mentor.py** - AI-powered mentorship layer
- LLM provider abstraction (OpenAI/Anthropic)
- Conversation persistence and resumption
- Adaptive teaching styles based on confidence levels
- Interactive learning sessions (Socratic method)
- Code review functionality
- System design interview simulation

**quests.json** - Quest database (V2 curriculum structure)
- Hierarchical structure: curriculum → patterns → concepts → problems
- Quest IDs follow format: `{pattern_id}_{concept_id}_{problem_num}` (e.g., ft_04_c1_p1)
- Pattern IDs follow format: `ft_{number}` (e.g., ft_02, ft_03, ft_04)
- Each quest contains: problem_id, problem_name, difficulty, url, estimated_time, hints
- Supports multiple curriculum modes: fast_track (80 hours), complete (425 hours)
- System design challenges with RESPECT framework guidance

**coach.db** - SQLite database (SINGLE SOURCE OF TRUTH)
- **user_profiles**: name, quests_completed, created_at, last_active, active_mode
- **pattern_progress**: pattern_id, confidence (0-100), quests_completed, mastered flag
- **quest_completions**: quest_id, pattern_id, completed_at, time_minutes, hints_used, review scheduling
- **concept_understanding**: pattern_id, concept, understood, diagnosed_at, taught_at
- **sessions**: current quest tracking, session type, timestamps
- **daily_logs**: problems_solved, time_spent, hints_used per day
- **mistakes**: mistake_type, description, lesson_learned, recurrence tracking
- **milestones**: achievements like pattern_mastered, streaks, no_hints
- **teaching_history**: what concepts have been explained and student response

**Storage Module** (`dsa_coach/storage/`)
- **db.py**: Async `Database` class for agent tools (uses aiosqlite)
- **sync.py**: Sync `SyncDatabase` wrapper for CLI commands (wraps async with asyncio.run)
- **models.py**: Pydantic models (UserProfile, PatternProgress, QuestCompletion, etc.)
- **migrations.py**: One-time migration from progress.json to SQLite

**DEPRECATED**: `progress.json` and `dsa_coach/progress.py` - Do not use

### Key Patterns Used

The project uses a structured curriculum with pattern IDs and full names:

**Fast Track Mode** (9 patterns, 80 hours):
- **ft_01**: Big-O Analysis & Complexity
- **ft_02**: Arrays & Hashing (Two Sum, Group Anagrams, Prefix Sum)
- **ft_03**: Two Pointers (3Sum, Container With Most Water, Fast-Slow)
- **ft_04**: Sliding Window (Longest Substring, Minimum Window)
- **ft_05**: Binary Search (Standard, Rotated Array, Answer Space)
- **ft_06**: Recursion Fundamentals (Fibonacci, Memoization)
- **ft_07**: Trees (DFS, BST, BFS, Path Problems)
- **ft_08**: Graphs (DFS, BFS, Topological Sort, Union Find)
- **ft_09**: Dynamic Programming (1D, 2D Grid, Knapsack)

**Note**: Pattern IDs changed from V1 friendly names (e.g., `sliding_window`) to V2 codes (e.g., `ft_04`) as of December 2024 migration.

### Adaptive Learning Algorithm

The `next` command intelligently selects quests using:
1. **Priority 1**: Spaced repetition items due today (based on last_reviewed + next_review_in)
2. **Priority 2**: Patterns with lowest confidence scores (weakest areas)
3. **Priority 3**: Next unstarted quest in daily curriculum order

Confidence scores update after each quest:
- Correct + no hints: +15 confidence
- Correct + hints: +10 confidence
- Confidence capped at 100

### Learning System

**Confidence Tracking (0-100)**:
- Starts at 0 for new patterns
- Increases with successful problem solving (+15 without hints, +10 with hints)
- Used to drive adaptive hints and problem selection
- Goal: 70%+ confidence = pattern mastery

**Spaced Repetition**:
- 1st review: 1 day after completion
- 2nd review: 3 days later
- 3rd review: 7 days later
- Long-term: 14 day intervals

### AI Integration

When API keys are configured, mentor.py provides:
- **Adaptive hints**: Tailored to confidence level (low: detailed walkthrough, medium: conceptual nudge, high: Socratic question)
- **Interactive learning**: Multi-turn conversational teaching with comprehension checks
- **Code review**: Feedback on time/space complexity, edge cases, style
- **System design coaching**: RESPECT framework guidance with trade-off discussions
- **Conversation persistence**: Auto-save/resume for interrupted sessions

## File Structure

```
dsa-coach/
├── coach.py              # CLI entrypoint (traditional commands)
├── coach-menu.py         # Interactive menu entrypoint
├── mentor.py             # AI mentorship layer (thin wrapper for backward compat)
├── coach.db              # SQLite database - SINGLE SOURCE OF TRUTH
├── dsa_coach/            # Core package
│   ├── __init__.py
│   ├── main.py           # CLI orchestration
│   ├── menu.py           # Interactive menu system
│   ├── paths.py          # Centralized file paths
│   ├── storage.py        # JSON I/O (for quests.json only)
│   ├── progress.py       # DEPRECATED - do not use
│   ├── quests.py         # Quest loading (uses SyncDatabase for mode)
│   ├── selection.py      # Quest selection logic
│   ├── curriculum.py     # Curriculum functions (patterns, concepts, problems)
│   ├── pattern_manager.py# Pattern status and syllabus
│   ├── solution.py       # Solution file generation
│   ├── ui.py             # Terminal UI helpers
│   ├── storage/          # DATABASE MODULE - USE THIS
│   │   ├── __init__.py
│   │   ├── db.py         # Async Database class (for agent tools)
│   │   ├── sync.py       # SyncDatabase wrapper (for CLI commands)
│   │   ├── models.py     # Pydantic models for all entities
│   │   └── migrations.py # JSON to SQLite migration
│   ├── domain/           # Pure business logic
│   │   └── scheduling.py # Spaced repetition algorithms
│   ├── commands/         # CLI command handlers (all use SyncDatabase)
│   │   ├── start.py      # Initialize profile
│   │   ├── status.py     # View progress
│   │   ├── next_quest.py # Get next quest
│   │   ├── done.py       # Mark quest complete
│   │   ├── hint.py       # Get adaptive hints
│   │   ├── recall.py     # Spaced repetition practice
│   │   ├── learn.py      # Interactive learning
│   │   ├── review.py     # Code review
│   │   ├── mistakes.py   # Mistake journal
│   │   ├── summary.py    # Full progress dump
│   │   ├── reset.py      # Reset progress
│   │   └── note.py       # Obsidian note management
│   ├── tools/            # Agent tools (async, use Database)
│   │   ├── quests.py     # Quest-related tools
│   │   ├── teaching.py   # Teaching/mistake recording tools
│   │   └── obsidian.py   # Note creation tools
│   ├── agent/            # AI Agent system
│   │   ├── agent.py      # CoachAgent with student context
│   │   ├── loop.py       # Agent interaction loop
│   │   └── terminal.py   # Terminal rendering
│   └── ai/               # AI mentorship (legacy)
│       ├── client.py     # LLM provider abstraction
│       ├── prompts.py    # System prompts & student context builder
│       ├── session.py    # Conversation persistence
│       └── hints.py      # Adaptive hint generation
├── scripts/              # Utility scripts
│   └── hydrate_test_data.py  # Test data hydration (creates realistic test data)
├── test_harness.py       # CLI for programmatic agent testing
├── tests/                # Test suite (pytest)
│   ├── harness/          # Agent test harness
│   │   ├── coach_harness.py  # CoachTestHarness class
│   │   └── test_harness_examples.py  # Example tests
│   └── conftest.py       # Pytest fixtures (coach_harness, hydrated_harness)
├── quests.json           # Quest database (curriculum structure)
├── progress.json         # DEPRECATED - do not use
├── requirements.txt      # Python dependencies
├── solutions/            # User solution files
└── conversations/        # Saved AI sessions
```

## Important Implementation Details

### Solution File Auto-Creation
When a user runs `python coach.py next`, the system:
1. Creates `solutions/dayN/` directory if needed
2. Generates `quest_id.py` with template code from quests.json
3. Opens LeetCode link in browser automatically
4. Displays DIVE protocol reminders

### Spaced Repetition Logic
After completing a quest, it schedules review:
- First review: 1 day later
- Second review: 3 days later
- Third review: 7 days later
- Fourth+: 14 days later (long-term retention)

### Conversation Persistence
Interactive sessions (`learn`, `design`) save to `conversations/`:
- Filename: `{type}_{id}.json`
- Contains: message history, metadata, timestamp
- Auto-saves on Ctrl+C, manual save with "pause" command
- Resume by running same command again

### Confidence Calculation
Per-pattern confidence (0-100):
- Starts at 0 for new patterns
- Increments based on success + hint usage
- Decrements if quest marked incomplete (not implemented yet)
- Used to prioritize weak areas in quest selection

## Dependencies

**Required**:
- python-dotenv: Environment variable management

**Recommended** (enhanced UX):
- rich: Beautiful terminal formatting and tables

**Optional** (AI features):
- openai: OpenAI API client (GPT-4)
- anthropic: Anthropic API client (Claude)

## Environment Variables

- `LLM_PROVIDER`: "openai" or "anthropic" (default: "anthropic")
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `COACH_WIDTH`: Terminal reading width (default: 88 chars)

## Development Conventions

### Adding New Quests
Edit `quests.json`:
- Add to appropriate pattern/concept section in curriculum
- Include all required fields: problem_id, problem_name, difficulty, url, hints, template
- Ensure hints follow 3-tier system (low/medium/high confidence)
- Update estimated_time_minutes for planning

### Working with User Progress Data

**For CLI Commands (synchronous):**
```python
from dsa_coach.storage.sync import SyncDatabase

def cmd_my_command():
    with SyncDatabase() as db:
        # Read operations
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        completed = db.get_completed_quests()
        due_reviews = db.get_due_reviews()

        # Write operations
        db.update_profile(profile)
        db.upsert_pattern_progress(pattern_progress)
        db.upsert_quest_completion(completion)
        db.upsert_daily_log(user_id="default", problems_delta=1, time_delta_mins=30)

        # For legacy function compatibility
        progress_compat = db.build_progress_compat()
```

**For Agent Tools (async):**
```python
from dsa_coach.storage.db import Database

@tool(name="my_tool", description="...", category="...")
async def my_tool(db: Database, user_id: str = "default") -> ToolResult:
    # Read operations
    profile = await db.get_or_create_profile(user_id)
    patterns = await db.get_all_pattern_progress(user_id)

    # For legacy function compatibility
    progress_compat = await db.build_progress_compat(user_id)

    return ToolResult(success=True, data={...})
```

### Key Database Methods

| Method | Description |
|--------|-------------|
| `get_or_create_profile()` | Get user profile, create if not exists |
| `get_all_pattern_progress()` | Get all pattern progress records |
| `get_pattern_progress(user_id, pattern_id)` | Get specific pattern progress |
| `get_completed_quests()` | Get all completed quest records |
| `get_due_reviews()` | Get quests due for spaced repetition |
| `get_latest_session()` | Get current session (active quest) |
| `upsert_pattern_progress(progress)` | Create/update pattern progress |
| `upsert_quest_completion(completion)` | Create/update quest completion |
| `upsert_daily_log(...)` | Update daily activity log |
| `add_milestone(...)` | Record achievement |
| `build_progress_compat()` | Build legacy-compatible progress dict |

### Modifying Confidence System
- Confidence is stored in `pattern_progress.confidence` (0-100)
- Updated via `db.upsert_pattern_progress()`
- Confidence thresholds: Used in hint adaptation (< 40%, 40-70%, >70%)
- Pattern mastery: Set `pattern_progress.mastered = True` when 70%+ and all problems complete

### Customizing AI Behavior
- Teaching prompts: `dsa_coach/ai/prompts.py`
- Student context: `build_student_context()` in prompts.py
- Hint generation: `dsa_coach/ai/hints.py`
- Agent system prompt: `get_agent_system_prompt()` in prompts.py

## Code Quality & Linting

The project uses modern Python linting and formatting tools to maintain code quality and consistency.

### Tools Configured

**Ruff** (v0.14.10) - Fast, comprehensive linter and formatter
- Replaces flake8, isort, black, and other tools
- Enforces PEP 8 style guidelines
- Checks for common bugs and code smells
- Auto-formats code consistently (88 char line length)
- Configuration in `pyproject.toml`

**Mypy** (v1.19.1) - Static type checker
- Validates type annotations
- Catches type-related bugs before runtime
- Works seamlessly with Pydantic models
- Configuration in `pyproject.toml`

**Pre-commit** (v4.5.1) - Git hooks framework
- Runs linters automatically before each commit
- Auto-fixes formatting and simple issues
- Blocks commits with serious code quality issues
- Configuration in `.pre-commit-config.yaml`

### Running Linters

**Automatic (via pre-commit hooks):**
```bash
git add .
git commit -m "your message"
# Linters run automatically before commit
# Auto-fixes are applied when possible
```

**Manual (run all hooks):**
```bash
pre-commit run --all-files  # Check all files
```

**Manual (specific tools):**
```bash
ruff check .                # Check for issues
ruff check . --fix          # Auto-fix issues
ruff format .               # Format code
mypy dsa_coach/             # Type check
```

### Best Practices for Claude Code

**ALWAYS follow these practices when writing or modifying code:**

1. **Run linters before committing changes**
   - Use `ruff check . --fix` to auto-fix issues
   - Use `ruff format .` to format code consistently
   - Address any remaining linting errors before committing

2. **Write clean, formatted code from the start**
   - Follow 88 character line length limit
   - Use double quotes for strings
   - Remove unused imports and variables
   - Keep functions focused and simple

3. **Handle linting errors proactively**
   - If pre-commit blocks a commit, fix the issues it reports
   - Don't ignore linting errors - they catch real bugs
   - Use `--fix` flag to auto-fix when possible
   - For mypy errors, add type hints or fix type mismatches

4. **Avoid introducing new linting violations**
   - Check modified files with `ruff check <file>` before saving
   - If editing a file with existing violations, fix them too
   - Don't use `# noqa` or `# type: ignore` unless absolutely necessary

5. **Type annotations (gradual adoption)**
   - Add type hints to new functions and methods
   - Use proper return type annotations
   - Leverage Pydantic models for data validation
   - Mypy warnings won't block commits, but should be addressed

### Common Linting Issues

**Unused imports:**
```python
# ❌ Bad
from rich.layout import Layout  # Imported but never used

# ✅ Good - Remove unused imports
# (removed)
```

**Unnecessary variable assignment before return:**
```python
# ❌ Bad
def get_text():
    text = process_data()
    return text

# ✅ Good
def get_text():
    return process_data()
```

**Line too long (>88 chars):**
```python
# ❌ Bad
really_long_function_name(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10)

# ✅ Good
really_long_function_name(
    arg1, arg2, arg3, arg4, arg5,
    arg6, arg7, arg8, arg9, arg10
)
```

**Missing type hints (mypy warnings):**
```python
# ❌ Bad
def get_pattern_name(pattern_id):
    return PATTERNS.get(pattern_id)

# ✅ Good
def get_pattern_name(pattern_id: str) -> str | None:
    return PATTERNS.get(pattern_id)
```

### Configuration Files

- **pyproject.toml**: Ruff and mypy configuration (line length, rules, exclusions)
- **.pre-commit-config.yaml**: Pre-commit hooks configuration (versions, arguments)
- **.gitignore**: Excludes linter cache directories (`.ruff_cache/`, `.mypy_cache/`)

### Updating Linting Tools

To update to the latest versions:
```bash
# Update Python packages
pip install --upgrade ruff mypy pre-commit

# Update pre-commit hooks
pre-commit autoupdate

# Update requirements.txt with new versions
pip freeze | grep -E "ruff|mypy|pre-commit" >> requirements.txt
```

## Known Limitations

- SQLite database (`coach.db`) not backed up automatically
- Single user support (hardcoded `user_id="default"`)
- AI features require external API keys (costs money)
- No built-in code execution or validation
- Solutions directory not automatically synced or committed
- Legacy `curriculum.py` functions still expect progress dict (use `build_progress_compat()`)
- Agent test harness requires network for AI calls (use `--scenario` for offline structure tests)

## Migration Notes (December 2024)

### From progress.json to SQLite ✅ COMPLETE

The codebase was migrated from JSON-based storage (`progress.json`) to SQLite (`coach.db`).

**Status:** Migration verified and tested (see Testing section above).

**Why:**
- Dashboard and agent were showing inconsistent data (dual data sources)
- JSON doesn't support proper spaced repetition queries
- Need for deep student modeling (mistakes, teaching history, milestones)

**What Changed:**
1. All CLI commands now use `SyncDatabase` context manager
2. All agent tools use async `Database` class
3. `progress.py` is deprecated (emits warnings)
4. `build_progress_compat()` method bridges to legacy functions

**If You See Deprecation Warnings:**
```
DeprecationWarning: load_progress() is deprecated. Use SyncDatabase instead.
```
This means old code is being used. Update to use `SyncDatabase`:
```python
# Old (deprecated)
from dsa_coach.progress import load_progress
progress = load_progress()# New (correct)
from dsa_coach.storage.sync import SyncDatabase
with SyncDatabase() as db:
    progress_compat = db.build_progress_compat()
```
