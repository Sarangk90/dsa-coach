#!/usr/bin/env python3
"""Migration script to remove gamification fields from progress.json.

This script removes XP, ranks, achievements, and streaks from existing
progress files while preserving all learning data (confidence, spaced repetition, etc.).

Usage:
    python migrate_remove_gamification.py
    python migrate_remove_gamification.py --path /path/to/progress.json
    python migrate_remove_gamification.py --dry-run  # Preview changes without saving
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime


def migrate_progress_json(progress_path: Path, dry_run: bool = False) -> dict:
    """Remove gamification fields from progress.json.

    Args:
        progress_path: Path to progress.json file
        dry_run: If True, don't save changes, just return what would be changed

    Returns:
        dict: Migrated progress data
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating: {progress_path}")

    # Load existing progress
    if not progress_path.exists():
        print(f"Error: File not found: {progress_path}")
        sys.exit(1)

    with open(progress_path, 'r') as f:
        progress = json.load(f)

    # Track what we're removing
    removed_fields = []

    # Clean profile
    profile = progress.get("profile", {})
    gamification_profile_fields = ["xp", "level", "rank", "streak_days", "current_day"]

    for field in gamification_profile_fields:
        if field in profile:
            removed_fields.append(f"profile.{field} = {profile[field]}")
            profile.pop(field)

    # Clean root fields
    root_gamification_fields = ["achievements", "hints_used"]

    for field in root_gamification_fields:
        if field in progress:
            value = progress[field]
            removed_fields.append(f"{field} = {value}")
            progress.pop(field)

    # Report what was found
    if removed_fields:
        print("\n  Removed gamification fields:")
        for field in removed_fields:
            print(f"    - {field}")
    else:
        print("  ✓ No gamification fields found (already migrated?)")

    # Verify learning data is preserved
    print("\n  Preserving learning data:")
    print(f"    ✓ Pattern proficiency: {len(progress.get('pattern_proficiency', {}))} patterns")
    print(f"    ✓ Completed quests: {len(progress.get('completed_quests', {}))} quests")
    print(f"    ✓ Spaced repetition queue: {len(progress.get('spaced_repetition_queue', []))} items")
    print(f"    ✓ Problems solved: {len(progress.get('problems_solved', {}))} problems")

    # Save if not dry run
    if not dry_run:
        # Backup original
        backup_path = progress_path.with_suffix('.json.backup')
        with open(backup_path, 'w') as f:
            json.dump(progress, f, indent=2)
        print(f"\n  ✓ Backup saved: {backup_path}")

        # Save migrated version
        with open(progress_path, 'w') as f:
            json.dump(progress, f, indent=2)
        print(f"  ✓ Migrated file saved: {progress_path}")
    else:
        print("\n  [DRY RUN] No changes saved.")

    return progress


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Remove gamification fields from DSA Coach progress.json"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("progress.json"),
        help="Path to progress.json file (default: ./progress.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving"
    )

    args = parser.parse_args()

    print("="*70)
    print("DSA Coach - Remove Gamification Migration")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run migration
    migrate_progress_json(args.path, dry_run=args.dry_run)

    print("\n" + "="*70)
    print("Migration complete!")
    print("="*70)

    if args.dry_run:
        print("\nTo apply changes, run without --dry-run flag:")
        print(f"  python migrate_remove_gamification.py --path {args.path}")
    else:
        print("\n✓ Gamification removed")
        print("✓ Learning data preserved")
        print("✓ Backup created")
        print("\nYou can now use the updated DSA Coach!")


if __name__ == "__main__":
    main()
