"""Code tools for DSA Coach agent.

Tools for managing solution files and code review.
"""

import json
from pathlib import Path

from ..storage.db import Database
from .registry import ToolResult, tool

# Cache for quests.json data
_quests_cache: dict | None = None


def _load_quests() -> dict:
    """Load and cache quests.json data."""
    global _quests_cache
    if _quests_cache is None:
        quests_path = Path(__file__).parent.parent.parent / "quests.json"
        with quests_path.open() as f:
            _quests_cache = json.load(f)
    return _quests_cache


def _find_quest(quest_id: str, mode: str = "fast_track") -> dict | None:
    """Find a quest/problem by ID in V2 curriculum structure."""
    quests = _load_quests()

    # Search through V2 curriculum structure
    for curriculum_mode in [mode, "fast_track", "complete"]:
        curriculum = quests.get("curriculum", {}).get(curriculum_mode, [])
        for pattern in curriculum:
            pattern_id = pattern.get("pattern_id")
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    if problem.get("problem_id") == quest_id:
                        # Return enriched problem data with V1-compatible fields
                        return {
                            "id": problem.get("problem_id"),
                            "title": problem.get("problem_name"),
                            "pattern": pattern_id,
                            "difficulty": problem.get("difficulty", "medium"),
                            "link": problem.get("url", ""),
                            "template": problem.get("template", ""),
                            "hints": problem.get("hints", {}),
                            # Include V2 fields as well
                            "problem_id": problem.get("problem_id"),
                            "problem_name": problem.get("problem_name"),
                            "url": problem.get("url", ""),
                            "pattern_id": pattern_id,
                            "pattern_name": pattern.get("pattern_name", ""),
                            "concept_id": concept.get("concept_id"),
                            "concept_name": concept.get("concept_name"),
                        }

    return None


def _get_solutions_dir() -> Path:
    """Get the solutions directory path."""
    return Path(__file__).parent.parent.parent / "solutions"


@tool(
    name="create_solution_file",
    description="Create a solution file for a quest with the problem template.",
    category="code",
)
async def create_solution_file(
    db: Database,
    quest_id: str,
) -> ToolResult:
    """
    Create a solution file for a quest.

    :param quest_id: The quest to create a solution file for
    :return: Path to the created file
    """
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    solutions_dir = _get_solutions_dir()
    pattern = quest.get("pattern", "unknown")
    target_dir = solutions_dir / pattern
    target_dir.mkdir(parents=True, exist_ok=True)

    solution_file = target_dir / f"{quest_id}.py"

    if solution_file.exists():
        return ToolResult(
            success=True,
            data={
                "path": str(solution_file),
                "existed": True,
            },
            message=f"Solution file already exists: {solution_file}",
        )

    template = quest.get(
        "template",
        f"# Solution for {quest.get('title', quest_id)}\n\n# Your code here\n",
    )
    header = f'''"""
{quest.get("title", quest_id)}
{"=" * len(quest.get("title", quest_id))}

Difficulty: {quest.get("difficulty", "medium").upper()}
Pattern: {quest.get("pattern", "unknown")}
Link: {quest.get("link", "")}

DIVE Protocol:
1. Decode: Understand the problem completely
2. Identify: Recognize the pattern
3. Visualize: Draw examples and edge cases
4. Execute: Write clean code
5. Evaluate: Test with examples
"""

{template}
'''
    solution_file.write_text(header)

    return ToolResult(
        success=True,
        data={
            "path": str(solution_file),
            "existed": False,
        },
        message=f"Created solution file: {solution_file}",
    )


@tool(
    name="read_solution_file",
    description="Read the contents of a solution file for a quest.",
    category="code",
)
async def read_solution_file(
    db: Database,
    quest_id: str,
) -> ToolResult:
    """
    Read the solution file for a quest.

    :param quest_id: The quest to read solution for
    :return: File contents and metadata
    """
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    solutions_dir = _get_solutions_dir()
    pattern = quest.get("pattern", "unknown")
    solution_file = solutions_dir / pattern / f"{quest_id}.py"

    # Fallback search if not found in pattern dir (for backward compatibility)
    if not solution_file.exists():
        found = list(solutions_dir.glob(f"**/{quest_id}.py"))
        if found:
            solution_file = found[0]

    if not solution_file.exists():
        return ToolResult(
            success=False,
            error=f"Solution file not found: {solution_file}",
        )

    content = solution_file.read_text()
    lines = content.split("\n")

    return ToolResult(
        success=True,
        data={
            "path": str(solution_file),
            "content": content,
            "lines": len(lines),
            "size_bytes": len(content.encode("utf-8")),
        },
    )


@tool(
    name="list_solution_files",
    description="List all solution files in the solutions directory.",
    category="code",
)
async def list_solution_files(
    db: Database,
) -> ToolResult:
    """
    List all solution files.

    :return: List of solution files with metadata
    """
    solutions_dir = _get_solutions_dir()

    if not solutions_dir.exists():
        return ToolResult(
            success=True,
            data=[],
            message="No solutions directory found",
        )

    files = []
    # Recursively find all python files in solutions dir
    for solution_file in sorted(solutions_dir.glob("**/*.py")):
        if solution_file.is_file():
            quest_id = solution_file.stem
            parent_dir = solution_file.parent.name
            content = solution_file.read_text()

            files.append(
                {
                    "quest_id": quest_id,
                    "category": parent_dir,  # Was day, now pattern or whatever dir
                    "path": str(solution_file),
                    "lines": len(content.split("\n")),
                    "size_bytes": len(content.encode("utf-8")),
                }
            )

    return ToolResult(
        success=True,
        data=files,
        message=f"Found {len(files)} solution files",
    )


@tool(
    name="review_code",
    description="Analyze submitted code for a quest and provide feedback on correctness, time/space complexity, and style.",
    category="code",
)
async def review_code(
    db: Database,
    code: str,
    quest_id: str,
) -> ToolResult:
    """
    Review code for a quest.

    Note: This is a placeholder that returns review prompts.
    The actual review is done by the LLM using this context.

    :param code: The code to review
    :param quest_id: The quest the code is for
    :return: Review context and hints
    """
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    # Provide context for LLM to do the review
    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("title", quest_id),
            "pattern": quest.get("pattern", "unknown"),
            "difficulty": quest.get("difficulty", "medium"),
            "code_to_review": code,
            "review_aspects": [
                "Correctness: Does the solution handle all cases?",
                "Time Complexity: What's the Big-O?",
                "Space Complexity: How much extra memory?",
                "Edge Cases: Empty input, single element, duplicates, etc.",
                "Code Style: Readability, naming, structure",
                "Pattern Usage: Does it properly use the intended pattern?",
            ],
            "hints": quest.get("hints", {}),
        },
        message="Ready for code review. Use the context to provide feedback.",
    )


@tool(
    name="get_solution_template",
    description="Get the starter template for a quest's solution.",
    category="code",
)
async def get_solution_template(
    db: Database,
    quest_id: str,
) -> ToolResult:
    """
    Get the solution template for a quest.

    :param quest_id: The quest to get template for
    :return: Template code and quest info
    """
    quest = _find_quest(quest_id)
    if not quest:
        return ToolResult(
            success=False,
            error=f"Quest '{quest_id}' not found",
        )

    template = quest.get("template", "# No template provided\n")

    return ToolResult(
        success=True,
        data={
            "quest_id": quest_id,
            "title": quest.get("title", quest_id),
            "pattern": quest.get("pattern", "unknown"),
            "template": template,
        },
    )
