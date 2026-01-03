from pathlib import Path
from typing import Any

from dsa_coach import paths


def create_solution_file(problem: dict[str, Any]) -> Path:
    """
    Create a solution file for the problem.

    Uses pattern_name for directory structure: solutions/<pattern_name>/<problem_id>.py
    """
    # Use pattern_name if available, else fall back to pattern_id or "misc"
    pattern_name = problem.get("pattern_name", problem.get("pattern_id", "misc"))
    # Sanitize pattern name for filesystem
    pattern_dir = pattern_name.replace(" ", "_").replace("&", "and").lower()

    target_dir = paths.SOLUTIONS_DIR / pattern_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Use problem_id for V2, fall back to 'id' for V1 compatibility
    problem_id = problem.get("problem_id", problem.get("id", "unknown"))
    filename = f"{problem_id}.py"
    filepath = target_dir / filename

    if not filepath.exists():
        # Create file with enhanced template
        template = problem.get("template", "# Your solution here\n")

        # New V2 fields
        problem_name = problem.get("problem_name", problem.get("title", "Unknown"))
        concept_name = problem.get("concept_name", "N/A")
        difficulty = problem.get("difficulty", "N/A")
        url = problem.get("url", problem.get("link", "N/A"))
        estimated_time = problem.get("estimated_time_minutes", "N/A")
        reason = problem.get("reason_for_selection", "")
        approaches = problem.get("solution_approaches", [])

        content = f'''"""
Quest: {problem_name}
Pattern: {pattern_name}
Concept: {concept_name}
Difficulty: {difficulty}
Estimated Time: {estimated_time} minutes
Link: {url}

{f"Why this problem: {reason}" if reason else ""}

{f"Approaches: {', '.join(approaches)}" if approaches else ""}

Use DIVE Protocol:
- D: Decode the problem
- I: Identify the pattern
- V: Visualize with examples
- E: Execute your solution
- E: Evaluate complexity
"""

{template}


# Test your solution
if __name__ == "__main__":
    # Add test cases here
    pass
'''
        with filepath.open("w") as f:
            f.write(content)

    return filepath


def get_solution_path(problem: dict[str, Any]) -> Path:
    """Get the path where a problem's solution file should be stored."""
    pattern_name = problem.get("pattern_name", problem.get("pattern_id", "misc"))
    pattern_dir = pattern_name.replace(" ", "_").replace("&", "and").lower()
    problem_id = problem.get("problem_id", problem.get("id", "unknown"))
    return Path(paths.SOLUTIONS_DIR / pattern_dir / f"{problem_id}.py")
