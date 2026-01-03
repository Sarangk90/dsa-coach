#!/usr/bin/env python3
"""Seed test data for DSA Coach - simulates realistic progress."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from dsa_coach.storage.db import Database
from dsa_coach.storage.models import UserProfile, PatternProgress, QuestCompletion


async def seed_test_data():
    """Seed the database with test data for testing."""
    print("🌱 Seeding test data...\n")

    db_path = Path("coach.db")
    db = Database(db_path)
    await db.connect()

    try:
        user_id = "default"
        now = datetime.now()

        # 1. Create user profile
        # First ensure profile exists, then update it
        await db.get_or_create_profile(user_id)

        profile = UserProfile(
            id=user_id,
            name="Test User",
            quests_completed=6,  # 6 quest completions below
            created_at=now - timedelta(days=7),
            last_active=now,
        )
        await db.update_profile(profile)
        print(f"✅ Created profile: {profile.name}")

        # 2. Add pattern progress
        patterns = [
            ("sliding_window", 35, 3),  # Low confidence, 3 quests done
            ("two_pointers", 55, 2),     # Medium confidence, 2 quests done
            ("hash_map", 10, 1),         # Very low confidence, 1 quest
        ]

        for pattern_id, confidence, quests_done in patterns:
            progress = PatternProgress(
                id=f"{user_id}_{pattern_id}",
                user_id=user_id,
                pattern_id=pattern_id,
                confidence=confidence,
                quests_completed=quests_done,
                last_practiced=now - timedelta(days=2),
            )
            await db.upsert_pattern_progress(progress)
            print(f"✅ Pattern: {pattern_id} - {confidence}% confidence, {quests_done} quests")

        # 3. Add completed quests with different review statuses
        completed_quests = [
            # Sliding Window quests (for testing review)
            {
                "quest_id": "longest_substring_without_repeating",
                "pattern_id": "sliding_window",
                "completed_at": now - timedelta(days=3),  # Due for 3-day review
                "hints_used": 1,
                "time_minutes": 25,
                "last_reviewed": now - timedelta(days=3),
                "review_count": 0,
                "next_review_in": 3,  # Should be due today!
            },
            {
                "quest_id": "max_consecutive_ones",
                "pattern_id": "sliding_window",
                "completed_at": now - timedelta(days=1),  # Due for 1-day review
                "hints_used": 0,
                "time_minutes": 15,
                "last_reviewed": now - timedelta(days=1),
                "review_count": 0,
                "next_review_in": 1,  # Should be due today!
            },
            {
                "quest_id": "minimum_window_substring",
                "pattern_id": "sliding_window",
                "completed_at": now - timedelta(days=5),
                "hints_used": 2,
                "time_minutes": 40,
                "last_reviewed": now - timedelta(days=5),
                "review_count": 0,
                "next_review_in": 1,  # Overdue!
            },
            # Two Pointers quests
            {
                "quest_id": "two_sum_ii",
                "pattern_id": "two_pointers",
                "completed_at": now - timedelta(days=2),
                "hints_used": 0,
                "time_minutes": 20,
                "last_reviewed": now - timedelta(days=2),
                "review_count": 0,
                "next_review_in": 3,  # Not due yet
            },
            {
                "quest_id": "container_with_most_water",
                "pattern_id": "two_pointers",
                "completed_at": now - timedelta(days=4),
                "hints_used": 1,
                "time_minutes": 30,
                "last_reviewed": now - timedelta(days=4),
                "review_count": 1,
                "next_review_in": 7,  # Reviewed once, not due yet
            },
            # Hash Map quest
            {
                "quest_id": "two_sum",
                "pattern_id": "hash_map",
                "completed_at": now - timedelta(days=6),
                "hints_used": 3,
                "time_minutes": 45,
                "last_reviewed": now - timedelta(days=6),
                "review_count": 0,
                "next_review_in": 1,  # Very overdue!
            },
        ]

        for quest_data in completed_quests:
            completion = QuestCompletion(
                id=f"{user_id}_{quest_data['quest_id']}",
                user_id=user_id,
                quest_id=quest_data["quest_id"],
                pattern_id=quest_data["pattern_id"],
                completed_at=quest_data["completed_at"],
                time_minutes=quest_data.get("time_minutes"),
                hints_used=quest_data["hints_used"],
                success=True,
                review_count=quest_data.get("review_count", 0),
                last_reviewed=quest_data.get("last_reviewed"),
                next_review_in=quest_data["next_review_in"],
            )
            await db.upsert_quest_completion(completion)

            # Calculate if due
            days_since_review = (now - quest_data["last_reviewed"]).days
            is_due = days_since_review >= quest_data["next_review_in"]
            status = "🔴 DUE" if is_due else "⏰ Not due yet"

            print(f"✅ Quest: {quest_data['quest_id'][:30]:30} | {quest_data['pattern_id']:15} | {status}")

        print(f"\n📊 Summary:")
        print(f"   • Total quests completed: {len(completed_quests)}")
        print(f"   • Patterns with progress: {len(patterns)}")
        print(f"   • Items due for review: 3 (sliding_window x2, hash_map x1)")

        # Get due reviews to verify
        due_reviews = await db.get_due_reviews(user_id)
        print(f"\n🔍 Verified {len(due_reviews)} items due for spaced repetition review:")
        for review in due_reviews:
            print(f"   • {review.quest_id} ({review.pattern_id})")

    finally:
        await db.close()

    print("\n✅ Test data seeded successfully!")
    print("\nYou can now test:")
    print("  • 'Show me items for review' - should show 3+ items")
    print("  • 'Let's review sliding window' - should find 2 problems")
    print("  • 'What are my weak patterns?' - should show hash_map (10%) and sliding_window (35%)")


if __name__ == "__main__":
    asyncio.run(seed_test_data())
