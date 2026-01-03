#!/usr/bin/env python3
"""Migration script: V1 to V2 data structure.

This script migrates the database from V1 quest/pattern IDs to V2 IDs:
- V1 quest IDs (e.g., 'two_sum') → V2 quest IDs (e.g., 'ft_02_c1_p1')
- V1 pattern IDs (e.g., 'hash_map') → V2 pattern IDs (e.g., 'ft_02')

Matches quests by LeetCode URL for accurate mapping.
"""

import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse


def load_quests_v2() -> dict:
    """Load V2 quests.json."""
    quests_path = Path(__file__).parent / "quests.json"
    with open(quests_path, "r") as f:
        return json.load(f)


def load_quests_v1_backup() -> dict:
    """Load V1 backup for reference."""
    backup_path = Path(__file__).parent / "quests_v1_backup.json"
    if backup_path.exists():
        with open(backup_path, "r") as f:
            return json.load(f)
    return {}


def normalize_url(url: str) -> str:
    """Normalize LeetCode URL for comparison."""
    if not url:
        return ""
    # Remove trailing slash, convert to lowercase
    parsed = urlparse(url.lower().rstrip('/'))
    # Extract just the path (e.g., /problems/two-sum)
    return parsed.path


def build_v1_to_v2_mapping() -> dict:
    """Build mapping from V1 quest IDs to V2 quest IDs using URLs."""
    v1_quests = load_quests_v1_backup()
    v2_quests = load_quests_v2()

    # Build V2 URL → quest mapping
    v2_url_map = {}
    for mode in ["fast_track", "complete"]:
        curriculum = v2_quests.get("curriculum", {}).get(mode, [])
        for pattern in curriculum:
            for concept in pattern.get("concepts", []):
                for problem in concept.get("practice_problems", []):
                    url = normalize_url(problem.get("url", ""))
                    if url:
                        v2_url_map[url] = {
                            "quest_id": problem["problem_id"],
                            "pattern_id": pattern["pattern_id"],
                            "problem_name": problem["problem_name"],
                            "pattern_name": pattern["pattern_name"],
                        }

    # Build V1 → V2 mapping
    mapping = {}
    if "quests" in v1_quests:
        for v1_quest in v1_quests["quests"]:
            v1_id = v1_quest.get("id")
            v1_url = normalize_url(v1_quest.get("link", ""))

            if v1_url in v2_url_map:
                v2_data = v2_url_map[v1_url]
                mapping[v1_id] = {
                    "v2_quest_id": v2_data["quest_id"],
                    "v2_pattern_id": v2_data["pattern_id"],
                    "v1_pattern_id": v1_quest.get("pattern"),
                    "url": v1_quest.get("link"),
                    "title": v1_quest.get("title"),
                }

    return mapping


# Legacy pattern name mappings
LEGACY_PATTERN_MAP = {
    "hash_map": "ft_02",  # Arrays & Hashing
    "sliding_window": "ft_04",  # Sliding Window
    "two_pointers": "ft_03",  # Two Pointers
    "binary_search": "ft_05",  # Binary Search
    "trees": "ft_07",  # Trees
    "graphs": "ft_08",  # Graphs
    "dynamic_programming": "ft_09",  # Dynamic Programming
    "recursion": "ft_06",  # Recursion Fundamentals
}


def get_v2_pattern_id(v1_pattern_id: str) -> str:
    """Convert V1 pattern ID to V2 pattern ID."""
    return LEGACY_PATTERN_MAP.get(v1_pattern_id, v1_pattern_id)


async def migrate_database():
    """Run the full migration."""
    from dsa_coach.storage.db import Database

    print("=" * 70)
    print("V1 → V2 Migration Script")
    print("=" * 70)
    print()

    # Build mapping
    print("Building V1 → V2 quest ID mapping...")
    mapping = build_v1_to_v2_mapping()

    print(f"Found {len(mapping)} quest mappings")
    print()

    # Show mapping
    print("Quest ID Mappings:")
    print("-" * 70)
    for v1_id, data in sorted(mapping.items()):
        print(f"  {v1_id:40} → {data['v2_quest_id']}")
    print()

    # Migrate database
    async with Database() as db:
        print("Migrating quest_completions table...")
        print("-" * 70)

        # Get all quest completions
        completions = await db.get_completed_quests("default")

        quest_updates = 0
        pattern_updates = 0
        unmapped = []

        for completion in completions:
            v1_quest_id = completion.quest_id
            v1_pattern_id = completion.pattern_id

            # Check if quest ID needs migration
            if v1_quest_id in mapping:
                v2_data = mapping[v1_quest_id]
                completion.quest_id = v2_data["v2_quest_id"]
                completion.id = f"{completion.user_id}_{v2_data['v2_quest_id']}"

                # Also update pattern ID
                completion.pattern_id = v2_data["v2_pattern_id"]

                await db.upsert_quest_completion(completion)
                print(f"  ✓ {v1_quest_id:40} → {v2_data['v2_quest_id']}")
                quest_updates += 1
                pattern_updates += 1
            else:
                # Quest not in mapping, but check if pattern needs update
                v2_pattern = get_v2_pattern_id(v1_pattern_id)
                if v2_pattern != v1_pattern_id:
                    completion.pattern_id = v2_pattern
                    await db.upsert_quest_completion(completion)
                    print(f"  ✓ Pattern only: {v1_pattern_id} → {v2_pattern} (quest: {v1_quest_id})")
                    pattern_updates += 1
                else:
                    unmapped.append(v1_quest_id)
                    print(f"  ⚠️  No mapping found: {v1_quest_id} (keeping as-is)")

        print()
        print("Migrating pattern_progress table...")
        print("-" * 70)

        # Get all pattern progress
        all_progress = await db.get_all_pattern_progress("default")

        pattern_progress_updates = 0
        for progress in all_progress:
            v1_pattern_id = progress.pattern_id
            v2_pattern_id = get_v2_pattern_id(v1_pattern_id)

            if v2_pattern_id != v1_pattern_id:
                # Check if V2 pattern already exists
                existing_v2 = await db.get_pattern_progress("default", v2_pattern_id)

                if existing_v2:
                    # Merge: keep the one with more progress
                    if progress.quests_completed > existing_v2.quests_completed:
                        print(f"  ⚠️  {v1_pattern_id} → {v2_pattern_id} (V2 exists, keeping V1 data)")
                        progress.pattern_id = v2_pattern_id
                        progress.id = f"default_{v2_pattern_id}"
                        await db.upsert_pattern_progress(progress)
                    else:
                        print(f"  ✓ {v1_pattern_id} → {v2_pattern_id} (V2 exists, keeping V2 data)")

                    # Delete old V1 record manually (not automatic)
                    # We'll leave this for now to be safe
                else:
                    # Simple migration
                    progress.pattern_id = v2_pattern_id
                    progress.id = f"default_{v2_pattern_id}"
                    await db.upsert_pattern_progress(progress)
                    print(f"  ✓ {v1_pattern_id:40} → {v2_pattern_id}")

                pattern_progress_updates += 1

    print()
    print("=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"Quest completions updated:    {quest_updates}")
    print(f"Pattern IDs updated:          {pattern_updates}")
    print(f"Pattern progress updated:     {pattern_progress_updates}")
    print(f"Unmapped quests (kept as-is): {len(unmapped)}")

    if unmapped:
        print()
        print("⚠️  Unmapped quests:")
        for qid in unmapped:
            print(f"  - {qid}")
        print()
        print("These quests may need manual review or are custom additions.")

    print()
    print("✅ Migration complete!")
    print()
    print("Next steps:")
    print("  1. Run: sqlite3 coach.db 'SELECT * FROM quest_completions;'")
    print("  2. Verify quest IDs are now V2 format (e.g., ft_02_c1_p1)")
    print("  3. Run: python coach-menu.py")
    print("  4. Test that everything works")


if __name__ == "__main__":
    asyncio.run(migrate_database())
