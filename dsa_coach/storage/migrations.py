"""Database migrations for DSA Coach.

Handles migration from JSON files to SQLite and schema upgrades.
"""

import json
from datetime import datetime
from pathlib import Path

from .db import Database
from .models import PatternProgress, QuestCompletion, UserProfile


async def migrate_from_json(
    db: Database,
    progress_json_path: Path | None = None,
    user_id: str = "default",
) -> dict:
    """
    Migrate data from progress.json to SQLite database.

    Returns a summary of migrated records.
    """
    if progress_json_path is None:
        progress_json_path = Path(__file__).parent.parent.parent / "progress.json"

    if not progress_json_path.exists():
        return {"status": "skipped", "reason": "progress.json not found"}

    try:
        with progress_json_path.open() as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"status": "error", "reason": f"Invalid JSON: {e}"}

    summary: dict[str, bool | int | str] = {
        "status": "success",
        "profile_migrated": False,
        "patterns_migrated": 0,
        "quests_migrated": 0,
    }

    # Migrate user profile
    profile_data = data.get("profile", {})
    if profile_data:
        created_at = datetime.fromisoformat(
            profile_data.get("created_at", datetime.now().isoformat())
        )
        profile = UserProfile(
            id=user_id,
            name=profile_data.get("name", "DSA Learner"),
            quests_completed=len(data.get("completed_quests", {})),
            created_at=created_at,
            last_active=datetime.now(),
        )

        # Check if profile already exists
        existing_profile = await db.get_or_create_profile(user_id)
        if existing_profile.quests_completed < profile.quests_completed:
            # Only update if JSON has more progress
            await db.update_profile(profile)
            summary["profile_migrated"] = True

    # Migrate pattern confidence
    pattern_confidence = data.get("pattern_confidence", {})
    for pattern_id, confidence in pattern_confidence.items():
        progress = PatternProgress(
            id=f"{user_id}_{pattern_id}",
            user_id=user_id,
            pattern_id=pattern_id,
            confidence=confidence,
        )
        existing_pattern = await db.get_pattern_progress(user_id, pattern_id)
        if not existing_pattern or existing_pattern.confidence < confidence:
            await db.upsert_pattern_progress(progress)
            summary["patterns_migrated"] = int(summary["patterns_migrated"]) + 1

    # Migrate completed quests
    completed_quests = data.get("completed_quests", {})
    for quest_id, quest_data in completed_quests.items():
        # Determine pattern from quest data or default
        pattern_id = quest_data.get("pattern", "unknown")

        completed_at = datetime.fromisoformat(
            quest_data.get("completed_at", datetime.now().isoformat())
        )

        completion = QuestCompletion(
            id=f"{user_id}_{quest_id}",
            user_id=user_id,
            quest_id=quest_id,
            pattern_id=pattern_id,
            completed_at=completed_at,
            hints_used=quest_data.get("hints_used", 0),
            success=True,
            review_count=quest_data.get("review_count", 0),
            last_reviewed=datetime.fromisoformat(quest_data["last_reviewed"])
            if quest_data.get("last_reviewed")
            else None,
            next_review_in=quest_data.get("next_review_in", 1),
        )

        existing_quest = await db.get_quest_completion(user_id, quest_id)
        if not existing_quest:
            await db.upsert_quest_completion(completion)
            summary["quests_migrated"] = int(summary["quests_migrated"]) + 1

    return summary


async def check_migration_needed(
    db: Database,
    progress_json_path: Path | None = None,
    user_id: str = "default",
) -> bool:
    """Check if migration from JSON is needed."""
    if progress_json_path is None:
        progress_json_path = Path(__file__).parent.parent.parent / "progress.json"

    if not progress_json_path.exists():
        return False

    # Check if database has data
    profile = await db.get_or_create_profile(user_id)
    if profile.quests_completed > 0:
        # Already has data, compare with JSON
        try:
            with progress_json_path.open() as f:
                data = json.load(f)
            json_quests = len(data.get("completed_quests", {}))
            # Only migrate if JSON has more progress
            return json_quests > profile.quests_completed
        except Exception:
            return False

    # No data in database, check if JSON has data
    try:
        with progress_json_path.open() as f:
            data = json.load(f)
        return bool(data.get("profile") or data.get("completed_quests"))
    except Exception:
        return False


async def migrate_remove_gamification_v3(db: Database) -> dict:
    """
    Remove gamification columns from database schema.
    Migration v2 -> v3: Remove XP, ranks, achievements, streaks.

    SQLite doesn't support DROP COLUMN directly, so we recreate tables.
    """
    async with db.conn.cursor() as cursor:
        # 1. Recreate user_profiles without gamification columns
        await cursor.execute("""
            CREATE TABLE user_profiles_new (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT 'DSA Learner',
                quests_completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL
            )
        """)

        await cursor.execute("""
            INSERT INTO user_profiles_new (id, name, quests_completed, created_at, last_active)
            SELECT id, name, quests_completed, created_at, last_active
            FROM user_profiles
        """)

        await cursor.execute("DROP TABLE user_profiles")
        await cursor.execute("ALTER TABLE user_profiles_new RENAME TO user_profiles")

        # 2. Recreate quest_completions without xp_earned column
        await cursor.execute("""
            CREATE TABLE quest_completions_new (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                quest_id TEXT NOT NULL,
                pattern_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                time_minutes INTEGER,
                hints_used INTEGER NOT NULL DEFAULT 0,
                success INTEGER NOT NULL DEFAULT 1,
                review_count INTEGER NOT NULL DEFAULT 0,
                last_reviewed TEXT,
                next_review_in INTEGER NOT NULL DEFAULT 1,
                UNIQUE(user_id, quest_id)
            )
        """)

        await cursor.execute("""
            INSERT INTO quest_completions_new
            SELECT id, user_id, quest_id, pattern_id, completed_at,
                   time_minutes, hints_used, success, review_count,
                   last_reviewed, next_review_in
            FROM quest_completions
        """)

        await cursor.execute("DROP TABLE quest_completions")
        await cursor.execute(
            "ALTER TABLE quest_completions_new RENAME TO quest_completions"
        )

        # Recreate indexes
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quest_completions_user ON quest_completions(user_id)"
        )
        await cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quest_completions_pattern ON quest_completions(pattern_id)"
        )

        await db.conn.commit()

    return {"status": "success", "migration": "remove_gamification_v3"}
