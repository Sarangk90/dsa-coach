#!/usr/bin/env python3
import sys

print(
    "⚠️  DEPRECATED: This script is no longer valid after the slug ID migration (January 2025)."
)
print(
    "   Canonical IDs are now human-readable slugs (e.g., 'sliding_window', 'arrays_hashing_two_sum')."
)
print("   See dsa_coach/id_mappings.py for the mapping from old ft_* IDs to new slugs.")
sys.exit(1)

"""Cleanup script: Remove V1 records after migration.

This script removes old V1 quest and pattern records that have been migrated to V2.
"""

import asyncio  # noqa: E402

# V1 pattern IDs to remove
V1_PATTERN_IDS = [
    "hash_map",
    "sliding_window",
    "two_pointers",
    "binary_search",
    "trees",
    "graphs",
    "dynamic_programming",
    "recursion",
]

# V1 quest IDs to remove (those that were successfully migrated)
V1_QUEST_IDS_TO_REMOVE = [
    "two_sum",
    "minimum_window_substring",
    "longest_substring_without_repeating",
    "container_with_most_water",
    # Add more as needed
]


async def cleanup_database():
    """Remove duplicate V1 records."""
    from dsa_coach.storage.db import Database

    print("=" * 70)
    print("Cleanup: Remove V1 Records")
    print("=" * 70)
    print()

    async with Database() as db:
        # Clean up pattern_progress
        print("Cleaning up pattern_progress table...")
        print("-" * 70)

        removed_patterns = 0
        for v1_pattern in V1_PATTERN_IDS:
            # Check if V1 pattern exists
            progress = await db.get_pattern_progress("default", v1_pattern)
            if progress:
                # Delete by executing raw SQL (no delete method in db.py)
                await db.conn.execute(
                    "DELETE FROM pattern_progress WHERE user_id = ? AND pattern_id = ?",
                    ("default", v1_pattern),
                )
                await db.conn.commit()
                print(f"  ✓ Removed: {v1_pattern}")
                removed_patterns += 1

        print()
        print("Cleaning up quest_completions table...")
        print("-" * 70)

        # Get all quest completions to identify V1 quests to remove
        completions = await db.get_completed_quests("default")

        removed_quests = 0
        for completion in completions:
            quest_id = completion.quest_id

            # Remove if it's in the V1 list or doesn't start with ft_
            if quest_id in V1_QUEST_IDS_TO_REMOVE or (
                not quest_id.startswith("ft_")
                and quest_id not in ["max_consecutive_ones", "two_sum_ii"]
            ):
                await db.conn.execute(
                    "DELETE FROM quest_completions WHERE user_id = ? AND quest_id = ?",
                    ("default", quest_id),
                )
                await db.conn.commit()
                print(f"  ✓ Removed: {quest_id}")
                removed_quests += 1

    print()
    print("=" * 70)
    print("Cleanup Summary")
    print("=" * 70)
    print(f"Pattern progress records removed: {removed_patterns}")
    print(f"Quest completion records removed: {removed_quests}")
    print()
    print("✅ Cleanup complete!")


if __name__ == "__main__":
    asyncio.run(cleanup_database())
