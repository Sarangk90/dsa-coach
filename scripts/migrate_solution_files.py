#!/usr/bin/env python3
"""
Script to rename solution files from old ft_* format to human-readable slugs.

Usage:
    python scripts/migrate_solution_files.py

This will:
1. Scan solutions/ directory
2. Rename directories from ft_XX to pattern slugs
3. Rename files from ft_XX_cY_pZ.py to problem slugs
"""

import shutil
import sys
from pathlib import Path

# Get project root and add to path for local imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dsa_coach.id_mappings import PATTERN_ID_MAP, PROBLEM_ID_MAP  # noqa: E402

SOLUTIONS_DIR = PROJECT_ROOT / "solutions"


def migrate_solution_files():
    """Migrate solution files to new naming convention."""
    if not SOLUTIONS_DIR.exists():
        print(f"Solutions directory not found at {SOLUTIONS_DIR}, nothing to migrate.")
        return

    changes_made = 0

    # 1. First, rename files within directories (before renaming directories)
    print("1. Renaming solution files...")
    for pattern_dir in SOLUTIONS_DIR.iterdir():
        if not pattern_dir.is_dir():
            continue

        for file_path in pattern_dir.glob("*.py"):
            old_problem_id = file_path.stem  # filename without extension
            if old_problem_id in PROBLEM_ID_MAP:
                new_problem_id = PROBLEM_ID_MAP[old_problem_id]
                new_file_path = file_path.parent / f"{new_problem_id}.py"

                if not new_file_path.exists():
                    shutil.move(str(file_path), str(new_file_path))
                    print(f"   {file_path.name} -> {new_file_path.name}")
                    changes_made += 1
                else:
                    print(
                        f"   ⚠️  Skipping {file_path.name} -> {new_file_path.name} "
                        f"(target exists)"
                    )

    # 2. Rename directories
    print("\n2. Renaming solution directories...")
    for pattern_dir in list(SOLUTIONS_DIR.iterdir()):
        if not pattern_dir.is_dir():
            continue

        old_pattern_id = pattern_dir.name
        if old_pattern_id in PATTERN_ID_MAP:
            new_pattern_id = PATTERN_ID_MAP[old_pattern_id]
            new_pattern_dir = SOLUTIONS_DIR / new_pattern_id

            if new_pattern_dir.exists():
                # Merge directories
                print(
                    f"   Merging {old_pattern_id}/ into existing {new_pattern_id}/..."
                )
                for file_path in pattern_dir.glob("*"):
                    target = new_pattern_dir / file_path.name
                    if not target.exists():
                        shutil.move(str(file_path), str(target))
                        print(f"      Moved {file_path.name}")
                        changes_made += 1
                # Remove empty old directory
                try:
                    pattern_dir.rmdir()
                    print(f"   Removed empty directory {old_pattern_id}/")
                except OSError:
                    print(f"   ⚠️  Could not remove {old_pattern_id}/ (not empty)")
            else:
                shutil.move(str(pattern_dir), str(new_pattern_dir))
                print(f"   {old_pattern_id}/ -> {new_pattern_id}/")
                changes_made += 1

    print(f"\n✅ Solution file migration complete. {changes_made} changes made.")


if __name__ == "__main__":
    migrate_solution_files()
