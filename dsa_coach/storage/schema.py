"""SQL schema definition for DSA Coach database."""

SCHEMA_SQL = """
    -- Sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        current_pattern TEXT,
        current_quest TEXT,
        session_type TEXT NOT NULL DEFAULT 'general',
        metadata TEXT NOT NULL DEFAULT '{}'
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);

    -- Messages table
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        thinking TEXT,
        thinking_signature TEXT,
        tool_name TEXT,
        tool_args TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
    CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

    -- User profiles table
    CREATE TABLE IF NOT EXISTS user_profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL DEFAULT 'DSA Learner',
        quests_completed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        last_active TEXT NOT NULL
    );

    -- Pattern progress table
    -- Note: 'progress' column (formerly 'confidence') - index created after migration
    CREATE TABLE IF NOT EXISTS pattern_progress (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        pattern_id TEXT NOT NULL,
        progress INTEGER NOT NULL DEFAULT 0,
        quests_completed INTEGER NOT NULL DEFAULT 0,
        quests_total INTEGER NOT NULL DEFAULT 0,
        concepts_understood TEXT NOT NULL DEFAULT '[]',
        concepts_total INTEGER NOT NULL DEFAULT 0,
        last_practiced TEXT,
        next_review TEXT,
        mastered INTEGER NOT NULL DEFAULT 0,
        UNIQUE(user_id, pattern_id)
    );
    CREATE INDEX IF NOT EXISTS idx_pattern_progress_user ON pattern_progress(user_id);

    -- Quest completions table
    CREATE TABLE IF NOT EXISTS quest_completions (
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
    );
    CREATE INDEX IF NOT EXISTS idx_quest_completions_user ON quest_completions(user_id);
    CREATE INDEX IF NOT EXISTS idx_quest_completions_pattern ON quest_completions(pattern_id);

    -- Concept understanding table
    CREATE TABLE IF NOT EXISTS concept_understanding (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        pattern_id TEXT NOT NULL,
        concept TEXT NOT NULL,
        understood INTEGER NOT NULL DEFAULT 0,
        diagnosed_at TEXT,
        taught_at TEXT,
        notes TEXT NOT NULL DEFAULT '',
        UNIQUE(user_id, pattern_id, concept)
    );
    CREATE INDEX IF NOT EXISTS idx_concept_understanding_pattern ON concept_understanding(pattern_id);

    -- ============ Deep Student Model Tables (v4) ============

    -- Mistakes with pattern recognition
    CREATE TABLE IF NOT EXISTS mistakes (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        quest_id TEXT NOT NULL,
        pattern_id TEXT NOT NULL,
        mistake_type TEXT NOT NULL,
        description TEXT NOT NULL,
        lesson_learned TEXT,
        logged_at TEXT NOT NULL,
        recurrence_count INTEGER DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_mistakes_user ON mistakes(user_id);
    CREATE INDEX IF NOT EXISTS idx_mistakes_type ON mistakes(user_id, mistake_type);
    CREATE INDEX IF NOT EXISTS idx_mistakes_pattern ON mistakes(user_id, pattern_id);
    -- Prevent duplicate mistakes for same quest+type (idempotency)
    CREATE UNIQUE INDEX IF NOT EXISTS idx_mistakes_unique
        ON mistakes(user_id, quest_id, mistake_type);

    -- Daily activity logs
    CREATE TABLE IF NOT EXISTS daily_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        date TEXT NOT NULL,
        problems_solved INTEGER NOT NULL DEFAULT 0,
        time_spent_mins INTEGER NOT NULL DEFAULT 0,
        patterns_worked TEXT NOT NULL DEFAULT '[]',
        hints_used INTEGER NOT NULL DEFAULT 0,
        UNIQUE(user_id, date)
    );
    CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, date);

    -- Milestones and wins
    CREATE TABLE IF NOT EXISTS milestones (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        milestone_type TEXT NOT NULL,
        pattern_id TEXT,
        quest_id TEXT,
        description TEXT NOT NULL,
        achieved_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_milestones_user ON milestones(user_id);
    CREATE INDEX IF NOT EXISTS idx_milestones_achieved ON milestones(achieved_at DESC);
    -- Prevent duplicate milestones (idempotency) - use COALESCE for nullable columns
    CREATE UNIQUE INDEX IF NOT EXISTS idx_milestones_unique
        ON milestones(user_id, milestone_type, COALESCE(pattern_id, ''), COALESCE(quest_id, ''));

    -- Teaching history
    CREATE TABLE IF NOT EXISTS teaching_history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default',
        pattern_id TEXT NOT NULL,
        concept TEXT NOT NULL,
        explanation_count INTEGER DEFAULT 1,
        last_explained TEXT NOT NULL,
        student_response TEXT,
        UNIQUE(user_id, pattern_id, concept)
    );
    CREATE INDEX IF NOT EXISTS idx_teaching_history_pattern ON teaching_history(user_id, pattern_id);

    -- Schema version table
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    );
"""
