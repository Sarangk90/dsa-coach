#!/usr/bin/env python3
"""Migration script to fix quests_total in pattern_progress table.

This script updates all pattern_progress records where quests_total is 0
by calculating the correct total from quests.json.
"""

import asyncio
import json
from pathlib import Path


def load_quests() -> dict:
    """Load quests.json data."""
    quests_path = Path(__file__).parent / "quests.json"
    with open(quests_path, "r") as f:
        return json.load(f)


def count_total_quests_for_pattern(quests_data: dict, pattern_id: str) -> int:
    """Count total practice problems for a given pattern.

    Handles both V2 pattern IDs (e.g., 'ft_04') and legacy friendly names (e.g., 'sliding_window').
    """
    total = 0

    # Legacy pattern name mappings (old name -> V2 pattern_id)
    LEGACY_PATTERN_MAP = {
        "hash_map": "ft_02",  # Arrays & Hashing
        "sliding_window": "ft_04",  # Sliding Window
        "two_pointers": "ft_03",  # Two Pointers
        "binary_search": "ft_05",  # Binary Search
        "trees": "ft_07",  # Trees
        "graphs": "ft_08",  # Graphs
        "dynamic_programming": "ft_09",  # Dynamic Programming
    }

    # Check if pattern_id is a legacy name that needs mapping
    mapped_pattern_id = LEGACY_PATTERN_MAP.get(pattern_id, pattern_id)

    # Helper to slugify pattern names for matching
    def slugify(text: str) -> str:
        return text.lower().replace(" ", "_").replace("-", "_").replace("&", "and")

    # V2: Check nested curriculum structure
    for mode in ["fast_track", "complete"]:
        curriculum = quests_data.get("curriculum", {}).get(mode, [])
        for pattern in curriculum:
            # Match by pattern_id (e.g., 'ft_04'), mapped ID, or by slugified pattern_name (e.g., 'sliding_window')
            pattern_name_slug = slugify(pattern.get("pattern_name", ""))
            if (pattern.get("pattern_id") == pattern_id or
                pattern.get("pattern_id") == mapped_pattern_id or
                pattern_name_slug == pattern_id):
                for concept in pattern.get("concepts", []):
                    total += len(concept.get("practice_problems", []))
                return total  # Return early once pattern found

    # V1: Fallback to counting quests with matching pattern
    for quest in quests_data.get("quests", []):
        if quest.get("pattern") == pattern_id:
            total += 1

    # If still 0, check days structure (legacy V1)
    if total == 0:
        for day_data in quests_data.get("days", {}).values():
            for quest in day_data.get("quests", []):
                if quest.get("pattern") == pattern_id:
                    total += 1

    return total


async def migrate():
    """Run the migration to fix quests_total values."""
    from dsa_coach.storage.db import Database

    quests_data = load_quests()

    async with Database() as db:
        # Get all pattern progress records
        all_progress = await db.get_all_pattern_progress("default")

        print(f"Found {len(all_progress)} pattern progress records")
        print()

        updated = 0
        for progress in all_progress:
            # Calculate correct total
            correct_total = count_total_quests_for_pattern(quests_data, progress.pattern_id)

            # Check if update needed
            if progress.quests_total != correct_total:
                old_total = progress.quests_total
                progress.quests_total = correct_total
                await db.upsert_pattern_progress(progress)

                print(f"✓ Updated {progress.pattern_id}:")
                print(f"  - quests_total: {old_total} → {correct_total}")
                print(f"  - quests_completed: {progress.quests_completed}")
                print(f"  - completion: {progress.quests_completed}/{correct_total} "
                      f"({100 * progress.quests_completed // correct_total if correct_total > 0 else 0}%)")
                print(f"  - confidence: {progress.confidence}%")
                print()
                updated += 1
            else:
                print(f"✓ {progress.pattern_id} already correct (total={correct_total})")

        print()
        print(f"Migration complete! Updated {updated} records.")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Fix quests_total in pattern_progress")
    print("=" * 60)
    print()
    asyncio.run(migrate())
