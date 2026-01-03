# DSA Coach

An adaptive CLI for mastering Data Structures, Algorithms, and System Design for Principal Engineer interviews.

## Features

- **Confidence-Based Learning**: Track pattern mastery from 0-100% with adaptive difficulty
- **AI-Powered Mentorship**: Get adaptive hints, code reviews, and interactive system design sessions
- **Spaced Repetition**: Automatic scheduling of review sessions for long-term retention (1, 3, 7, 14 day intervals)
- **Pattern-First Curriculum**: Master 17 core patterns that solve 90%+ of interview problems
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

### Option 1: Interactive Menu (Recommended)

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux: .venv\Scripts\activate on Windows

# Install all dependencies
uv sync

# Set up your API key (optional, for AI features)
cp env.example .env
# Edit .env with your Anthropic or OpenAI API key

# Launch the interactive menu
python coach-menu.py
```

The interactive menu gives you a visual dashboard and numbered options - no need to remember command syntax!

### Option 2: Traditional CLI

```bash
# Start your journey
python coach.py start

# Get your first quest
python coach.py next

# When you're done
python coach.py done
```

## Interactive Menu

Launch the interactive menu for an easy-to-use interface:

```bash
python coach-menu.py
```

**Features:**
- 📊 **Dashboard at a glance**: Progress, current quest, weak patterns
- 🎯 **Smart alerts**: See due spaced repetition items
- 🔢 **Numbered menu**: Just type a number - no need to remember commands
- ♻️  **Auto-refresh**: Clean display after each command
- 💡 **Contextual hints**: Get suggestions based on your confidence level

**Menu Structure:**
```
═══ DAILY WORKFLOW ═══
1. Today's Schedule      → See what's planned for today
2. Next Quest           → Get your optimal next problem
3. Mark Quest Done      → Complete current quest & build confidence
4. View Status          → Full progress overview

═══ LEARNING & HELP ═══
5. Get Hint             → Adaptive hints based on your confidence
6. Learn Pattern        → Interactive teaching session
7. Review Mistakes      → Your mistake journal

═══ AI FEATURES ═══
8. Code Review          → Get AI feedback on your solution
9. System Design        → Practice system design interviews

═══ ADVANCED ═══
10. Spaced Repetition   → Review items due today
11. View Sessions       → Saved AI conversations
12. Full Summary        → Complete progress dump
```

## CLI Commands

For direct command-line usage, all traditional commands still work:

| Command | Description |
|---------|-------------|
| `python coach.py start` | Initialize your profile |
| `python coach.py status` | View your progress, confidence, and weak patterns |
| `python coach.py today` | **Daily schedule** - what to focus on today |
| `python coach.py next` | Get your next optimal quest |
| `python coach.py done` | Mark current quest complete and build confidence |
| `python coach.py hint` | Get an adaptive hint (adjusts to your confidence) |
| `python coach.py review <file>` | Request AI code review |
| `python coach.py recall` | **Spaced repetition** - practice due items |
| `python coach.py learn [pattern]` | **Interactive learning session** (Socratic teaching) |
| `python coach.py design [name]` | Start interactive system design interview |
| `python coach.py summary` | Full progress dump for debugging |
| `python coach.py sessions` | List and manage saved conversation sessions |
| `python coach.py mistakes` | Review your mistake journal |

## Interactive Learning Sessions

The `learn` command starts a conversational session where the AI:

1. **Teaches the pattern** - Concept, visual triggers, code template
2. **Checks understanding** - Asks comprehension questions
3. **Guides practice** - Presents a problem and helps you solve it
4. **Provides feedback** - Reviews your approach

```bash
# Learn a specific pattern
python coach.py learn sliding_window

# Or pick from a menu showing your weakest patterns first
python coach.py learn
```

The teaching adapts to your confidence level:
- **Low confidence**: Detailed walkthrough with pseudocode
- **Medium confidence**: Conceptual explanations with nudges
- **High confidence**: Socratic questioning, treats you as a peer

### Pause & Resume Sessions

Conversations are automatically saved! You can:
- Type `pause` to save and exit
- Press Ctrl+C and it auto-saves
- Resume next day with `python coach.py learn <pattern>`

```bash
# Pause a session
> pause
💾 Session paused and saved!
Resume with: python coach.py learn sliding_window

# Next day, just run the same command to resume
python coach.py learn sliding_window
# 📂 Found saved session from 2025-12-23
# Resume previous conversation? [Y/n] y
```

View all saved sessions:
```bash
python coach.py sessions
```

## Confidence-Based Learning System

### Pattern Confidence (0-100%)

Your confidence per pattern drives the entire learning experience:

| Confidence Level | What It Means | Hint Style |
|-----------------|---------------|------------|
| **0-40%** (Learning) | Building fundamentals | Detailed walkthrough with pseudocode |
| **40-70%** (Developing) | Understanding core concepts | Conceptual nudges and guiding questions |
| **70-100%** (Mastered) | Pattern internalized | Socratic questions, edge case challenges |

### How Confidence Builds

- Complete a problem **without hints**: +15% confidence
- Complete a problem **with hints**: +10% confidence
- **Pattern Mastery**: 70%+ confidence + all problems complete
- Confidence caps at 100% per pattern

### Spaced Repetition Schedule

Completed problems automatically schedule for review:
- **1st review**: 1 day after completion
- **2nd review**: 3 days later
- **3rd review**: 7 days later
- **Long-term**: 14 day intervals

## Adaptive Learning

The coach adapts to you:

1. **Pattern Confidence Tracking**: Every problem updates your confidence score (0-100%) per pattern
2. **Intelligent Quest Selection**:
   - **Priority 1**: Spaced repetition items due today
   - **Priority 2**: Weakest patterns (lowest confidence)
   - **Priority 3**: Next unstarted problem in curriculum
3. **Adaptive Hints**:
   - **Low confidence (<40%)**: Detailed walkthrough with pseudocode
   - **Medium confidence (40-70%)**: Conceptual nudges
   - **High confidence (>70%)**: Socratic questions, edge cases
4. **AI Teaching Adaptation**:
   - Adjusts teaching style based on your pattern confidence
   - More encouragement when learning, more challenge when mastering

## Core Patterns

The curriculum covers 17 essential patterns:

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
├── coach.py              # Main CLI
├── mentor.py             # AI integration
├── quests.json           # All problems and system designs
├── coach.db              # Your progress (SQLite database, auto-generated)
├── requirements.txt      # Dependencies
├── env.example           # API key template
├── .gitignore
├── solutions/            # Your code (auto-created)
│   ├── day1/
│   ├── day2/
│   └── ...
├── final-plan.md         # The synthesized 7-day plan
├── execution-framework.md # Detailed daily templates
└── scripts/
    └── hydrate_test_data.py  # Test data management
```

## Development & Testing

### Test Data Management

Test data is isolated from your real progress using separate user IDs:
- `default` - Your real progress (used by CLI commands)
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

## Setting Up AI Mentor

The coach works without AI, but for the best experience:

1. Get an API key from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)
2. Create `.env` file:
   ```
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
3. The mentor will now provide:
   - Intelligent hints based on your history
   - Code reviews with actionable feedback
   - Interactive system design interviews

## UI & Session Tuning (optional)

Defaults (no env vars needed):
- Discord-like chat bubbles for learn sessions (when `rich` is installed)
- Auto-save after each exchange
- On resume, show the last 25 messages (tail) to avoid dumping huge logs

Optional overrides:

```
# Switch back to classic style
COACH_CHAT_STYLE=classic

# Disable autosave-after-each-exchange
COACH_AUTOSAVE=0

# On resume, show everything (or only the last message)
COACH_RESUME_SHOW=all
# COACH_RESUME_SHOW=last

# Change how many messages are shown when COACH_RESUME_SHOW=tail (default: 25)
COACH_RESUME_TAIL=50

# Terminal reading width used by Rich rendering (default: 88)
COACH_WIDTH=88
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
2. **Focus on Confidence**: Aim for 70%+ on each pattern for mastery
3. **Speak Aloud**: Practice explaining your thought process
4. **Review Mistakes**: The mistake journal is your secret weapon
5. **Trust the System**: The adaptive algorithm prioritizes your weak patterns
6. **Don't Skip Reviews**: Spaced repetition builds long-term retention

## License

MIT - Use it, modify it, ace your interviews!

---

**Remember**: The goal isn't to memorize solutions. It's to internalize patterns so deeply that you can derive solutions from first principles under pressure.

Good luck, future Principal Engineer! 🚀
