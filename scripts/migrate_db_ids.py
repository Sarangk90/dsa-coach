#!/usr/bin/env python3
"""
Database migration script to update IDs from ft_* format to human-readable slugs.

Usage:
    python scripts/migrate_db_ids.py

This will:
1. Backup the database
2. Update all IDs in all tables
3. Verify the migration
"""

import json
import shutil
import sqlite3
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

DB_PATH = PROJECT_ROOT / "coach.db"


def migrate_database():
    """Migrate all IDs in the database to human-readable format."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}, skipping DB migration.")
        return

    # Create backup
    backup_path = DB_PATH.with_suffix(".db.bak")
    shutil.copy(DB_PATH, backup_path)
    print(f"Created backup at {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    changes_made = 0

    # 1. Update pattern_progress table
    print("\n1. Migrating pattern_progress...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE pattern_progress SET pattern_id = ? WHERE pattern_id = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(f"   pattern_progress: {old_id} -> {new_id} ({cursor.rowcount} rows)")
            changes_made += cursor.rowcount

    # 2. Update quest_completions table (pattern_id and quest_id)
    print("\n2. Migrating quest_completions...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE quest_completions SET pattern_id = ? WHERE pattern_id = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   quest_completions.pattern_id: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    for old_id, new_id in PROBLEM_ID_MAP.items():
        cursor.execute(
            "UPDATE quest_completions SET quest_id = ? WHERE quest_id = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   quest_completions.quest_id: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    # 3. Update concept_understanding table
    print("\n3. Migrating concept_understanding...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE concept_understanding SET pattern_id = ? WHERE pattern_id = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   concept_understanding.pattern_id: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    for old_id, new_id in CONCEPT_ID_MAP.items():
        cursor.execute(
            "UPDATE concept_understanding SET concept = ? WHERE concept = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   concept_understanding.concept: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    # 4. Update mistakes table
    print("\n4. Migrating mistakes...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE mistakes SET pattern_id = ? WHERE pattern_id = ?", (new_id, old_id)
        )
        if cursor.rowcount > 0:
            print(
                f"   mistakes.pattern_id: {old_id} -> {new_id} ({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    for old_id, new_id in PROBLEM_ID_MAP.items():
        cursor.execute(
            "UPDATE mistakes SET quest_id = ? WHERE quest_id = ?", (new_id, old_id)
        )
        if cursor.rowcount > 0:
            print(
                f"   mistakes.quest_id: {old_id} -> {new_id} ({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    # 5. Update milestones table
    print("\n5. Migrating milestones...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE milestones SET pattern_id = ? WHERE pattern_id = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   milestones.pattern_id: {old_id} -> {new_id} ({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    for old_id, new_id in PROBLEM_ID_MAP.items():
        cursor.execute(
            "UPDATE milestones SET quest_id = ? WHERE quest_id = ?", (new_id, old_id)
        )
        if cursor.rowcount > 0:
            print(
                f"   milestones.quest_id: {old_id} -> {new_id} ({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    # 6. Update teaching_history table
    print("\n6. Migrating teaching_history...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE teaching_history SET pattern_id = ? WHERE pattern_id = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   teaching_history.pattern_id: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    for old_id, new_id in CONCEPT_ID_MAP.items():
        cursor.execute(
            "UPDATE teaching_history SET concept = ? WHERE concept = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   teaching_history.concept: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    # 7. Update sessions table
    print("\n7. Migrating sessions...")
    for old_id, new_id in PATTERN_ID_MAP.items():
        cursor.execute(
            "UPDATE sessions SET current_pattern = ? WHERE current_pattern = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   sessions.current_pattern: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    for old_id, new_id in PROBLEM_ID_MAP.items():
        cursor.execute(
            "UPDATE sessions SET current_quest = ? WHERE current_quest = ?",
            (new_id, old_id),
        )
        if cursor.rowcount > 0:
            print(
                f"   sessions.current_quest: {old_id} -> {new_id} "
                f"({cursor.rowcount} rows)"
            )
            changes_made += cursor.rowcount

    # 8. Update daily_logs.patterns_worked (JSON array)
    print("\n8. Migrating daily_logs.patterns_worked...")
    cursor.execute("SELECT id, patterns_worked FROM daily_logs")
    rows = cursor.fetchall()
    for row_id, patterns_json in rows:
        try:
            patterns = json.loads(patterns_json)
            updated = [PATTERN_ID_MAP.get(p, p) for p in patterns]
            if updated != patterns:
                cursor.execute(
                    "UPDATE daily_logs SET patterns_worked = ? WHERE id = ?",
                    (json.dumps(updated), row_id),
                )
                print(f"   daily_logs: {patterns} -> {updated}")
                changes_made += 1
        except json.JSONDecodeError:
            continue

    # Commit all changes
    conn.commit()

    # Verify: Check for any remaining old IDs
    print("\n--- Verification ---")
    old_ids_found = []

    cursor.execute(
        "SELECT DISTINCT pattern_id FROM pattern_progress WHERE pattern_id LIKE 'ft_%'"
    )
    if cursor.fetchall():
        old_ids_found.append("pattern_progress.pattern_id")

    cursor.execute(
        "SELECT DISTINCT pattern_id FROM quest_completions WHERE pattern_id LIKE 'ft_%'"
    )
    if cursor.fetchall():
        old_ids_found.append("quest_completions.pattern_id")

    cursor.execute(
        "SELECT DISTINCT quest_id FROM quest_completions WHERE quest_id LIKE 'ft_%'"
    )
    if cursor.fetchall():
        old_ids_found.append("quest_completions.quest_id")

    if old_ids_found:
        print(f"⚠️  Warning: Old IDs still found in: {', '.join(old_ids_found)}")
    else:
        print("✅ No old ft_* IDs found in database.")

    conn.close()

    print(f"\n✅ Database migration complete. {changes_made} changes made.")
    print(f"   Backup saved to {backup_path}")


if __name__ == "__main__":
    migrate_database()
