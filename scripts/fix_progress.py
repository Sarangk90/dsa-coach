#!/usr/bin/env python3
"""Fix progress data based on user's ACTUAL completion.

From user's explicit message:
- Big-O: Done (conceptual)
- Arrays & Hashing: 4/6 (Two Sum, Group Anagrams, Top K, Subarray Sum)
- Two Pointers: 1/4 (only Linked List Cycle)
- Sliding Window: 3/3 all done
- Binary Search: 3/4 (1-3 done, not Capacity)
- Recursion: NOT done
- Trees: NOT done
- Graphs: NOT done
- DP: NOT done
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dsa_coach.storage.db import Database

# Define ONLY completed quests with staggered completion dates
COMPLETED_QUESTS = {
    # Arrays & Hashing - 4/6 done
    "arrays_hashing": [
        ("arrays_hashing_two_sum", 14),
        ("arrays_hashing_group_anagrams", 12),
        ("arrays_hashing_top_k_frequent_elements", 10),
        ("arrays_hashing_subarray_sum_equals_k", 8),
    ],
    # Two Pointers - 1/4 done
    "two_pointers": [
        ("two_pointers_linked_list_cycle", 7),
    ],
    # Sliding Window - 3/3 done
    "sliding_window": [
        ("sliding_window_longest_substring_without_repeating", 18),
        ("sliding_window_minimum_window_substring", 16),
        ("sliding_window_permutation_in_string", 14),
    ],
    # Binary Search - 3/4 done
    "binary_search": [
        ("binary_search_basic", 6),
        ("binary_search_rotated_sorted_array", 5),
        ("binary_search_koko_eating_bananas", 4),
    ],
}

# Pattern metadata (total quests per pattern)
PATTERN_TOTALS = {
    "big_o_analysis": {"quests_total": 0, "concepts_total": 2},
    "arrays_hashing": {"quests_total": 6, "concepts_total": 3},
    "two_pointers": {"quests_total": 4, "concepts_total": 2},
    "sliding_window": {"quests_total": 3, "concepts_total": 2},
    "binary_search": {"quests_total": 4, "concepts_total": 2},
    "recursion": {"quests_total": 5, "concepts_total": 2},
    "trees": {"quests_total": 9, "concepts_total": 4},
    "graphs": {"quests_total": 8, "concepts_total": 4},
    "dynamic_programming": {"quests_total": 7, "concepts_total": 3},
}


async def fix_progress():
    """Clear and rebuild progress from scratch."""
    db = Database()
    await db.connect()

    user_id = "default"
    now = datetime.now()

    print("🗑️  Clearing existing progress data...")

    # Clear existing data
    await db.conn.execute("DELETE FROM quest_completions WHERE user_id = ?", (user_id,))
    await db.conn.execute("DELETE FROM pattern_progress WHERE user_id = ?", (user_id,))
    await db.conn.execute("DELETE FROM milestones WHERE user_id = ?", (user_id,))
    await db.conn.commit()

    print("✅ Cleared existing data")

    total_quests = 0
    review_day_offset = 0

    print("\n📝 Adding quest completions...")

    for pattern_id, quests in COMPLETED_QUESTS.items():
        for quest_id, days_ago in quests:
            completed_at = now - timedelta(days=days_ago)

            # Stagger reviews across different days
            if days_ago > 7:
                future_review_day = (review_day_offset % 7) + 1
                last_reviewed = now - timedelta(days=1)
                next_review_in = future_review_day
                review_count = 1
            else:
                last_reviewed = None
                next_review_in = (review_day_offset % 3) + 1
                review_count = 0

            review_day_offset += 1

            await db.conn.execute(
                """
                INSERT INTO quest_completions
                (id, user_id, quest_id, pattern_id, completed_at, time_minutes, hints_used, success, review_count, last_reviewed, next_review_in)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{user_id}_{quest_id}",
                    user_id,
                    quest_id,
                    pattern_id,
                    completed_at.isoformat(),
                    30,
                    0,
                    1,
                    review_count,
                    last_reviewed.isoformat() if last_reviewed else None,
                    next_review_in,
                ),
            )
            total_quests += 1
            review_status = (
                f"reviewed, next in {next_review_in}d"
                if last_reviewed
                else f"first review in {next_review_in}d"
            )
            print(f"  ✓ {quest_id} ({review_status})")

    await db.conn.commit()
    print(f"\n✅ Added {total_quests} quest completions")

    # Update pattern progress
    print("\n📊 Updating pattern progress...")

    for pattern_id, meta in PATTERN_TOTALS.items():
        quests_in_pattern = COMPLETED_QUESTS.get(pattern_id, [])
        quests_completed = len(quests_in_pattern)
        quests_total = meta["quests_total"]

        # Calculate confidence
        if quests_total == 0:
            confidence = 80 if pattern_id == "big_o_analysis" else 0
        else:
            completion_pct = quests_completed / quests_total
            confidence = min(100, int(completion_pct * 100))

        mastered = quests_completed >= quests_total and quests_total > 0

        last_practiced = None
        if quests_in_pattern:
            min_days_ago = min(days for _, days in quests_in_pattern)
            last_practiced = now - timedelta(days=min_days_ago)

        next_review = None
        if mastered:
            review_offsets = {"sliding_window": 3}
            offset = review_offsets.get(pattern_id, 7)
            next_review = now + timedelta(days=offset)

        await db.conn.execute(
            """
            INSERT INTO pattern_progress
            (id, user_id, pattern_id, confidence, quests_completed, quests_total, concepts_understood, concepts_total, last_practiced, next_review, mastered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, pattern_id) DO UPDATE SET
                confidence = excluded.confidence,
                quests_completed = excluded.quests_completed,
                quests_total = excluded.quests_total,
                last_practiced = excluded.last_practiced,
                next_review = excluded.next_review,
                mastered = excluded.mastered
            """,
            (
                f"{user_id}_{pattern_id}",
                user_id,
                pattern_id,
                confidence,
                quests_completed,
                quests_total,
                "[]",
                meta["concepts_total"],
                last_practiced.isoformat() if last_practiced else None,
                next_review.isoformat() if next_review else None,
                1 if mastered else 0,
            ),
        )

        if mastered:
            status = "✅ MASTERED"
        elif quests_completed > 0:
            status = f"📝 {quests_completed}/{quests_total}"
        else:
            status = f"🔒 {quests_completed}/{quests_total}"
        print(f"  {pattern_id}: {confidence}% confidence, {status}")

    await db.conn.commit()

    # Update user profile
    print("\n👤 Updating user profile...")
    await db.conn.execute(
        """
        UPDATE user_profiles SET quests_completed = ?, last_active = ?
        WHERE id = ?
        """,
        (total_quests, now.isoformat(), user_id),
    )
    await db.conn.commit()

    # Add milestones for mastered patterns
    print("\n🏆 Adding milestones...")
    mastered_patterns = [
        p
        for p, m in PATTERN_TOTALS.items()
        if len(COMPLETED_QUESTS.get(p, [])) >= m["quests_total"]
        and m["quests_total"] > 0
    ]

    for pattern in mastered_patterns:
        await db.conn.execute(
            """
            INSERT INTO milestones (id, user_id, milestone_type, pattern_id, description, achieved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                user_id,
                "pattern_mastered",
                pattern,
                f"Mastered {pattern.replace('_', ' ').title()} pattern!",
                now.isoformat(),
            ),
        )
        print(f"  🏆 Pattern mastered: {pattern}")

    if not mastered_patterns:
        print("  (no patterns mastered yet)")

    await db.conn.commit()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 PROGRESS SUMMARY")
    print("=" * 60)
    print(f"Total quests completed: {total_quests}")
    print(f"Patterns mastered: {len(mastered_patterns)}")

    print("\n📅 Review schedule (staggered):")
    due_reviews = await db.get_due_reviews(user_id)
    if due_reviews:
        for review in due_reviews[:5]:
            print(f"  - {review.quest_id}")
        if len(due_reviews) > 5:
            print(f"  ... and {len(due_reviews) - 5} more")
    else:
        print("  Reviews will come on different days")

    print("\n✅ Progress fixed successfully!")

    await db.close()


if __name__ == "__main__":
    asyncio.run(fix_progress())
