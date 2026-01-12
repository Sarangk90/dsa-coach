#!/usr/bin/env python3
"""
Script to migrate IDs in quests.json from cryptic ft_* format to human-readable slugs.

Usage:
    python scripts/migrate_ids.py

This will:
1. Read quests.json
2. Replace all IDs with human-readable versions
3. Write to quests.json (backup created at quests.json.bak)
"""

import json
import shutil
import sys
from pathlib import Path

# Get project root and add to path for local imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dsa_coach.id_mappings import (  # noqa: E402
    CONCEPT_ID_MAP,
    PATTERN_ID_MAP,
    PROBLEM_ID_MAP,
)

QUESTS_FILE = PROJECT_ROOT / "quests.json"


def migrate_quests_json():
    """Migrate all IDs in quests.json to human-readable format."""
    # Create backup
    backup_path = QUESTS_FILE.with_suffix(".json.bak")
    shutil.copy(QUESTS_FILE, backup_path)
    print(f"Created backup at {backup_path}")

    # Read current quests
    with QUESTS_FILE.open() as f:
        data = json.load(f)

    # Migrate curriculum patterns
    for mode in ["fast_track", "complete"]:
        if mode not in data.get("curriculum", {}):
            continue

        patterns = data["curriculum"][mode]
        if not isinstance(patterns, list):
            continue

        for pattern in patterns:
            old_pattern_id = pattern.get("pattern_id")
            if old_pattern_id and old_pattern_id in PATTERN_ID_MAP:
                new_pattern_id = PATTERN_ID_MAP[old_pattern_id]
                pattern["pattern_id"] = new_pattern_id
                print(f"Pattern: {old_pattern_id} -> {new_pattern_id}")

            # Update prerequisites
            if "prerequisites" in pattern:
                pattern["prerequisites"] = [
                    PATTERN_ID_MAP.get(p, p) for p in pattern["prerequisites"]
                ]

            # Update unlocks
            if "unlocks" in pattern:
                pattern["unlocks"] = [
                    PATTERN_ID_MAP.get(p, p) for p in pattern["unlocks"]
                ]

            # Migrate concepts
            for concept in pattern.get("concepts", []):
                old_concept_id = concept.get("concept_id")
                if old_concept_id and old_concept_id in CONCEPT_ID_MAP:
                    new_concept_id = CONCEPT_ID_MAP[old_concept_id]
                    concept["concept_id"] = new_concept_id
                    print(f"  Concept: {old_concept_id} -> {new_concept_id}")

                # Migrate problems
                for problem in concept.get("practice_problems", []):
                    old_problem_id = problem.get("problem_id")
                    if old_problem_id and old_problem_id in PROBLEM_ID_MAP:
                        new_problem_id = PROBLEM_ID_MAP[old_problem_id]
                        problem["problem_id"] = new_problem_id
                        print(f"    Problem: {old_problem_id} -> {new_problem_id}")

    # Write updated quests
    with QUESTS_FILE.open("w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Successfully migrated {QUESTS_FILE}")
    print(f"   Backup saved to {backup_path}")


if __name__ == "__main__":
    migrate_quests_json()
