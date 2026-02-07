# DSA Coach

An adaptive CLI for mastering Data Structures, Algorithms, and System Design for Principal Engineer interviews.

## Features

- **Progress-Based Learning**: Track pattern mastery from 0-100% with adaptive difficulty
- **AI-Powered Mentorship**: Get adaptive hints, code reviews, and interactive system design sessions
- **Spaced Repetition**: Automatic scheduling of review sessions for long-term retention (1, 3, 7, 14 day intervals)
- **Pattern-First Curriculum**: Master 16 core patterns that solve 90%+ of interview problems
- **Zero Friction**: Solution files are auto-created, LeetCode links auto-open

## Quick Start

### Prerequisites

Install uv (fast Python package manager):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Setup

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux: .venv\Scripts\activate on Windows

# Install all dependencies
uv sync

# Set up your API key (optional, for AI features)
cp env.example .env
# Edit .env with your Anthropic or OpenAI API key

# Launch the AI coaching agent (recommended)
python coach.py
```

The agent provides natural conversation-based coaching with automatic tool use for progress tracking, quest management, hints, and more.

### Commands

The project now uses an agent-first interface:

| Command | Description |
|---------|-------------|
| `python coach.py` | Start the interactive AI DSA coach |
| `python coach.py dashboard` | Open the Streamlit progress dashboard |
| `python coach.py dashboard --daemon` | Run dashboard in background |
| `python coach.py dashboard --stop` | Stop background dashboard |

### In-Session Controls

Inside the agent session:
- `help` shows available commands
- `dashboard` refreshes and shows your current dashboard state
- `/resume` lists previous sessions and lets you resume one
- `quit` (or `Ctrl+D`) exits

## Progress-Based Learning System

### Pattern Progress (0-100%)

Your progress per pattern drives the entire learning experience:

| Progress Level | What It Means | Hint Style |
|---------------|---------------|------------|
| **0-40%** (Learning) | Building fundamentals | Detailed walkthrough with pseudocode |
| **40-70%** (Developing) | Understanding core concepts | Conceptual nudges and guiding questions |
| **70-100%** (Mastered) | Pattern internalized | Socratic questions, edge case challenges |

### How Progress Builds

- Complete a problem **without hints**: +15 points
- Complete a problem **with hints**: +10 points
- **Pattern Mastery**: 70%+ progress + all problems complete
- Progress caps at 100% per pattern

### Spaced Repetition Schedule

Completed problems automatically schedule for review:
- **1st review**: 1 day after completion
- **2nd review**: 3 days later
- **3rd review**: 7 days later
- **Long-term**: 14 day intervals

## Adaptive Learning

The coach adapts to you:

1. **Pattern Progress Tracking**: Every problem updates your progress score (0-100%) per pattern
2. **Intelligent Quest Selection**:
   - **Priority 1**: Spaced repetition items due today
   - **Priority 2**: Weakest patterns (lowest progress)
   - **Priority 3**: Next unstarted problem in curriculum
3. **Adaptive Hints**:
   - **Low progress (<40%)**: Detailed walkthrough with pseudocode
   - **Medium progress (40-70%)**: Conceptual nudges
   - **High progress (>70%)**: Socratic questions, edge cases
4. **AI Teaching Adaptation**:
   - Adjusts teaching style based on your pattern progress
   - More encouragement when learning, more challenge when mastering

## Core Patterns

The curriculum covers 16 essential patterns:

| Category | Patterns |
|----------|----------|
| **Arrays & Strings** | Sliding Window, Two Pointers, Prefix Sum |
| **Data Structures** | Hash Map, Stack, Linked List, Heap |
| **Pointers** | Fast/Slow Pointers |
| **Intervals** | Merge Intervals |
| **Recursion** | Backtracking, Dynamic Programming |
| **Graphs & Trees** | BFS, DFS, Topological Sort, Dijkstra |
| **Search** | Binary Search, Union Find |

Each pattern includes:
- Core concept explanation
- Essential practice problems
- System design connections
- Progressive difficulty levels

## Files

```
dsa-coach/
├── coach.py              # Agent entrypoint
├── dsa_coach/            # Core package (agent, tools, storage, web)
├── quests.json           # Pattern curriculum and problems
├── coach.db              # Your progress (SQLite database, auto-generated)
├── pyproject.toml        # Dependencies and project config
├── env.example           # API key template
├── solutions/            # Auto-created solution files by pattern
└── scripts/
    └── hydrate_test_data.py  # Test data management
```

## Development & Testing

### Test Data Management

Test data is isolated from your real progress using separate user IDs:
- `default` - Your real progress (used by the agent)
- `test` - Isolated test data for development/testing

```bash
# Hydrate test data (uses "test" user by default)
python scripts/hydrate_test_data.py

# Reset and re-hydrate test data
python scripts/hydrate_test_data.py --reset

# Clear test data only (no hydration)
python scripts/hydrate_test_data.py --clear-only

# Use a custom user ID
python scripts/hydrate_test_data.py --user my_custom_test
```

Test data includes realistic scenarios: multiple patterns at different mastery levels, quest completions, spaced repetition items due for review, mistakes, milestones, and teaching history.

## Setting Up AI

The coach works without AI, but for the best experience:

1. Get an API key from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)
2. Create `.env` file:
   ```
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
3. The agent will now provide:
   - Intelligent hints based on your history
   - Code reviews with actionable feedback
   - Interactive system design interviews

## Configuration (optional)

```bash
# Terminal reading width used by Rich rendering (default: 88)
COACH_WIDTH=88

# Extended thinking token budget (default: 10000)
THINKING_BUDGET=10000
```

## The DIVE Protocol

For every problem, follow DIVE:

```
D - DECODE (2 min)   → Read, clarify inputs/outputs/constraints
I - IDENTIFY (2 min) → Map to a pattern
V - VISUALIZE (3 min)→ Draw small example, walk through logic
E - EXECUTE (15 min) → Write clean code, think aloud
E - EVALUATE (3 min) → Time/Space complexity, dry-run edge case
```

## Tips for Success

1. **Consistency > Intensity**: 2 hours daily beats 14 hours on weekends
2. **Focus on Progress**: Aim for 70%+ on each pattern for mastery
3. **Speak Aloud**: Practice explaining your thought process
4. **Review Mistakes**: The mistake journal is your secret weapon
5. **Trust the System**: The adaptive algorithm prioritizes your weak patterns
6. **Don't Skip Reviews**: Spaced repetition builds long-term retention

## License

MIT - Use it, modify it, ace your interviews!

---

**Remember**: The goal isn't to memorize solutions. It's to internalize patterns so deeply that you can derive solutions from first principles under pressure.

Good luck, future Principal Engineer! 🚀
