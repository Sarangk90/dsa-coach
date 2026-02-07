"""User profile database operations mixin."""

from __future__ import annotations

from datetime import datetime

import aiosqlite

from .models import UserProfile


class ProfileMixin:
    """Mixin providing user profile CRUD operations."""

    conn: aiosqlite.Connection

    async def get_or_create_profile(self, user_id: str = "default") -> UserProfile:
        """Get user profile, creating if it doesn't exist."""
        async with self.conn.execute(
            "SELECT * FROM user_profiles WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserProfile(
                    id=row["id"],
                    name=row["name"],
                    quests_completed=row["quests_completed"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_active=datetime.fromisoformat(row["last_active"]),
                )

        # Create new profile
        now = datetime.now()
        profile = UserProfile(id=user_id, created_at=now, last_active=now)
        await self.conn.execute(
            """
            INSERT INTO user_profiles (id, name, quests_completed, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                profile.id,
                profile.name,
                profile.quests_completed,
                profile.created_at.isoformat(),
                profile.last_active.isoformat(),
            ),
        )
        await self.conn.commit()
        return profile

    async def update_profile(self, profile: UserProfile) -> None:
        """Update user profile."""
        profile.last_active = datetime.now()
        await self.conn.execute(
            """
            UPDATE user_profiles SET
                name = ?, quests_completed = ?, last_active = ?
            WHERE id = ?
            """,
            (
                profile.name,
                profile.quests_completed,
                profile.last_active.isoformat(),
                profile.id,
            ),
        )
        await self.conn.commit()
