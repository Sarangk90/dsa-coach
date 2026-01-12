#!/usr/bin/env python3
"""Clean up test data and ensure database consistency."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dsa_coach.storage.db import Database


async def cleanup_and_audit():
    db = Database()
    await db.connect()

    print("🧹 CLEANING UP TEST DATA")
    print("=" * 60)

    # List all users first
    async with db.conn.execute("SELECT id, name FROM user_profiles") as cursor:
        users = await cursor.fetchall()
    print("Current users:")
    for u in users:
        print(f"  - {u['id']}: {u['name']}")

    # Delete test users and their data
    test_users = ["test", "test_claude_v2"]

    for test_user in test_users:
        print(f"\n🗑️  Removing test user: {test_user}")
        await db.conn.execute(
            "DELETE FROM quest_completions WHERE user_id = ?", (test_user,)
        )
        await db.conn.execute(
            "DELETE FROM pattern_progress WHERE user_id = ?", (test_user,)
        )
        await db.conn.execute("DELETE FROM user_profiles WHERE id = ?", (test_user,))
        await db.conn.execute("DELETE FROM sessions WHERE user_id = ?", (test_user,))
        await db.conn.execute(
            "DELETE FROM concept_understanding WHERE user_id = ?", (test_user,)
        )
        await db.conn.execute("DELETE FROM mistakes WHERE user_id = ?", (test_user,))
        await db.conn.execute("DELETE FROM daily_logs WHERE user_id = ?", (test_user,))
        await db.conn.execute("DELETE FROM milestones WHERE user_id = ?", (test_user,))
        await db.conn.execute(
            "DELETE FROM teaching_history WHERE user_id = ?", (test_user,)
        )

    await db.conn.commit()
    print("\n✅ Test data cleaned up")

    # Clean up duplicate milestones for default user
    print("\n🧹 Cleaning duplicate milestones...")
    await db.conn.execute("""
        DELETE FROM milestones
        WHERE user_id = 'default' AND id NOT IN (
            SELECT MIN(id) FROM milestones
            WHERE user_id = 'default'
            GROUP BY milestone_type, COALESCE(pattern_id, '')
        )
    """)
    await db.conn.commit()

    user_id = "default"

    # Now audit just the default user
    print("\n" + "=" * 60)
    print("🔍 AUDITING DEFAULT USER (Sarang)")
    print("=" * 60)

    # Quest completions for default user
    async with db.conn.execute(
        "SELECT COUNT(*) as cnt FROM quest_completions WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        quest_count = row["cnt"]
    print(f"\n📊 Quest completions: {quest_count}")

    # List them
    async with db.conn.execute(
        "SELECT quest_id, pattern_id FROM quest_completions WHERE user_id = ? ORDER BY pattern_id, quest_id",
        (user_id,),
    ) as cursor:
        quests = await cursor.fetchall()

    print("\nCompleted quests:")
    for q in quests:
        print(f"  ✓ {q['quest_id']}")

    # Pattern progress for default user
    async with db.conn.execute(
        "SELECT * FROM pattern_progress WHERE user_id = ? ORDER BY pattern_id",
        (user_id,),
    ) as cursor:
        patterns = await cursor.fetchall()

    print(f"\n📊 Pattern progress records: {len(patterns)}")

    issues = []

    for p in patterns:
        # Count actual quests for this pattern for this user
        async with db.conn.execute(
            "SELECT COUNT(*) as cnt FROM quest_completions WHERE user_id = ? AND pattern_id = ?",
            (user_id, p["pattern_id"]),
        ) as cursor:
            row = await cursor.fetchone()
            actual_quests = row["cnt"]

        if p["quests_completed"] != actual_quests:
            issues.append((p["pattern_id"], p["quests_completed"], actual_quests))

        mastered = "✅ MASTERED" if p["mastered"] else ""
        match = "✓" if p["quests_completed"] == actual_quests else "⚠️"
        print(
            f"  {match} {p['pattern_id']}: {p['quests_completed']}/{p['quests_total']} ({p['confidence']}%) {mastered}"
        )

    # Fix mismatches
    if issues:
        print(f"\n⚠️  Fixing {len(issues)} pattern progress mismatches...")
        for pattern_id, old_count, actual_count in issues:
            # Recalculate confidence
            async with db.conn.execute(
                "SELECT quests_total FROM pattern_progress WHERE user_id = ? AND pattern_id = ?",
                (user_id, pattern_id),
            ) as cursor:
                row = await cursor.fetchone()
                quests_total = row["quests_total"] if row else 0

            if quests_total > 0:
                confidence = min(100, int((actual_count / quests_total) * 100))
                mastered = 1 if actual_count >= quests_total else 0
            else:
                confidence = 80 if pattern_id == "big_o_analysis" else 0
                mastered = 0

            await db.conn.execute(
                """
                UPDATE pattern_progress
                SET quests_completed = ?, confidence = ?, mastered = ?
                WHERE user_id = ? AND pattern_id = ?
            """,
                (actual_count, confidence, mastered, user_id, pattern_id),
            )
            print(f"  Fixed {pattern_id}: {old_count} → {actual_count}")

        await db.conn.commit()

    # Update profile quests_completed
    await db.conn.execute(
        "UPDATE user_profiles SET quests_completed = ? WHERE id = ?",
        (quest_count, user_id),
    )
    await db.conn.commit()
    print(f"\n✓ Updated profile quests_completed to {quest_count}")

    # Check milestones
    async with db.conn.execute(
        "SELECT * FROM milestones WHERE user_id = ?", (user_id,)
    ) as cursor:
        milestones = await cursor.fetchall()
    print(f"\n📊 Milestones: {len(milestones)}")
    for m in milestones:
        print(f"  🏆 {m['description']}")

    # Final verification
    print("\n" + "=" * 60)
    print("🔍 FINAL VERIFICATION")
    print("=" * 60)

    # Re-check everything
    async with db.conn.execute(
        "SELECT * FROM pattern_progress WHERE user_id = ? ORDER BY pattern_id",
        (user_id,),
    ) as cursor:
        patterns = await cursor.fetchall()

    all_good = True
    for p in patterns:
        async with db.conn.execute(
            "SELECT COUNT(*) as cnt FROM quest_completions WHERE user_id = ? AND pattern_id = ?",
            (user_id, p["pattern_id"]),
        ) as cursor:
            row = await cursor.fetchone()
            actual_quests = row["cnt"]

        if p["quests_completed"] != actual_quests:
            print(f"  ❌ {p['pattern_id']}: STILL MISMATCHED")
            all_good = False
        else:
            mastered = "✅" if p["mastered"] else ""
            print(
                f"  ✓ {p['pattern_id']}: {p['quests_completed']}/{p['quests_total']} {mastered}"
            )

    print("\n" + "=" * 60)
    if all_good:
        print("✅ DATABASE IS NOW CLEAN AND CONSISTENT")
    else:
        print("❌ SOME ISSUES REMAIN")
    print("=" * 60)

    await db.close()


if __name__ == "__main__":
    asyncio.run(cleanup_and_audit())
