"""
Migration script to convert V1 progress.json to V2 schema.

This script safely migrates existing user progress to the new curriculum structure.
Run once: python migrate_to_v2.py
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


# Quest ID mappings from V1 to V2
# Format: {"old_quest_id": "new_problem_id"}
QUEST_TO_PROBLEM_MAP = {
    # These will be populated as we identify quests in the new structure
    # For now, we'll use a best-effort approach based on problem names
}


def load_json(filepath: Path) -> dict:
    """Load JSON file."""
    if not filepath.exists():
        return {}
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath: Path, data: dict) -> None:
    """Save JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def backup_file(filepath: Path) -> None:
    """Create backup of file."""
    if filepath.exists():
        backup_path = filepath.with_suffix(".backup.json")
        shutil.copy(filepath, backup_path)
        print(f"✅ Backed up {filepath} to {backup_path}")


def migrate_progress(progress: dict) -> dict:
    """Migrate V1 progress to V2 schema."""
    print("\n🔄 Migrating progress to V2 schema...")
    
    # Check if already migrated
    if "patterns_completed" in progress:
        print("⚠️ Progress appears to already be V2 format. Skipping migration.")
        return progress
    
    # Add V2 fields to profile
    profile = progress.setdefault("profile", {})
    if "active_mode" not in profile:
        profile["active_mode"] = "fast_track"
        print("  ✓ Set active_mode to fast_track")
    
    if "current_pattern_id" not in profile:
        profile["current_pattern_id"] = None
    if "current_concept_id" not in profile:
        profile["current_concept_id"] = None
    
    # Migrate completed_quests to problems_solved
    progress.setdefault("problems_solved", {})
    if isinstance(progress.get("completed_quests"), dict):
        for quest_id, quest_data in progress["completed_quests"].items():
            # Try to map to V2 problem_id
            problem_id = QUEST_TO_PROBLEM_MAP.get(quest_id, quest_id)
            
            if problem_id not in progress["problems_solved"]:
                progress["problems_solved"][problem_id] = {
                    "completed_at": quest_data.get("completed_at", datetime.now().isoformat()),
                    "attempts": 1,
                    "time_spent_mins": 0  # Unknown for migrated data
                }
        print(f"  ✓ Migrated {len(progress['completed_quests'])} completed quests to problems_solved")
    
    # Infer patterns_completed from completed quests
    progress.setdefault("patterns_completed", [])
    progress.setdefault("patterns_in_progress", [])
    
    # Map old pattern proficiency to determine which patterns were worked on
    pattern_prof = progress.get("pattern_proficiency", {})
    for pattern, prof in pattern_prof.items():
        if prof.get("successes", 0) > 0:
            # User has successfully completed problems in this pattern
            # For now, we can't determine the V2 pattern_id, so we'll leave this for manual review
            pass
    
    # Add time_spent_hours
    if "time_spent_hours" not in progress:
        # Convert total_time_mins to hours
        total_mins = progress.get("total_time_mins", 0)
        progress["time_spent_hours"] = {
            "total": total_mins / 60.0,
            "by_pattern": {}
        }
        print(f"  ✓ Converted {total_mins} minutes to {total_mins/60.0:.1f} hours")
    
    # Add daily_study_log
    if "daily_study_log" not in progress:
        progress["daily_study_log"] = []
    
    # Add milestones_achieved
    if "milestones_achieved" not in progress:
        progress["milestones_achieved"] = []
    
    # Add last_study_date
    if "last_study_date" not in progress:
        progress["last_study_date"] = profile.get("last_session")
    
    print("  ✓ Added all V2 fields")
    
    return progress


def main():
    """Run migration."""
    print("=" * 70)
    print("DSA Coach V2 Migration Script")
    print("=" * 70)
    
    # Find progress.json
    progress_file = Path("progress.json")
    if not progress_file.exists():
        print("\n❌ progress.json not found in current directory.")
        print("   Please run this script from the dsa-coach project root.")
        return
    
    # Backup original file
    backup_file(progress_file)
    
    # Load progress
    progress = load_json(progress_file)
    
    if not progress:
        print("\n⚠️ progress.json is empty. Nothing to migrate.")
        return
    
    # Migrate
    migrated = migrate_progress(progress)
    
    # Save migrated progress
    save_json(progress_file, migrated)
    print(f"\n✅ Migration complete! Saved to {progress_file}")
    
    print("\n" + "=" * 70)
    print("📋 Migration Summary:")
    print("=" * 70)
    print(f"  • Profile: {migrated['profile'].get('name', 'Unknown')}")
    print(f"  • Mode: {migrated['profile'].get('active_mode', 'fast_track')}")
    print(f"  • XP: {migrated['profile'].get('xp', 0)}")
    print(f"  • Streak: {migrated['profile'].get('streak_days', 0)} days")
    print(f"  • Problems solved: {len(migrated.get('problems_solved', {}))}")
    print(f"  • Total time: {migrated.get('time_spent_hours', {}).get('total', 0):.1f} hours")
    print(f"  • Patterns completed: {len(migrated.get('patterns_completed', []))}")
    print(f"  • Patterns in progress: {len(migrated.get('patterns_in_progress', []))}")
    
    print("\n" + "=" * 70)
    print("⚠️  IMPORTANT NOTES:")
    print("=" * 70)
    print("  1. Your old quest IDs have been preserved in problems_solved.")
    print("  2. Pattern completion status may need manual review.")
    print("  3. A backup was created: progress.backup.json")
    print("  4. Test the new system with: python coach.py status")
    print("\n  If anything goes wrong, restore from backup:")
    print("    mv progress.backup.json progress.json")
    
    print("\n✨ You're ready to use DSA Coach V2!")
    print("   Run: python coach.py status")
    print("=" * 70)


if __name__ == "__main__":
    main()



