"""Pydantic models for database entities.

These models represent the core data structures stored in SQLite.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Session(BaseModel):
    """A coaching session with conversation history."""

    id: str = Field(description="Unique session ID (UUID)")
    user_id: str = Field(default="default", description="User identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    current_pattern: str | None = Field(
        default=None, description="Current pattern being learned"
    )
    current_quest: str | None = Field(
        default=None, description="Current quest being worked on"
    )
    session_type: str = Field(
        default="general", description="Type: general, learn, practice, review"
    )
    metadata: dict = Field(default_factory=dict, description="Additional session data")


class Message(BaseModel):
    """A message in a coaching conversation."""

    id: str = Field(description="Unique message ID (UUID)")
    session_id: str = Field(description="Parent session ID")
    role: str = Field(description="Role: user, assistant, tool_call, tool_result")
    content: str = Field(description="Message content")
    thinking: str | None = Field(
        default=None, description="Extended thinking content (assistant messages only)"
    )
    thinking_signature: str | None = Field(
        default=None, description="Signature for thinking block (required for replay)"
    )
    tool_name: str | None = Field(
        default=None, description="Tool name if tool call/result"
    )
    tool_args: dict | None = Field(
        default=None, description="Tool arguments if tool call"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """User profile with overall progress."""

    id: str = Field(default="default", description="User ID")
    name: str = Field(default="DSA Learner", description="Display name")
    quests_completed: int = Field(default=0, description="Total quests completed")
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)


class PatternProgress(BaseModel):
    """Progress for a specific pattern."""

    id: str = Field(description="Unique ID (user_id + pattern_id)")
    user_id: str = Field(default="default")
    pattern_id: str = Field(description="Pattern identifier (e.g., sliding_window)")
    confidence: int = Field(
        default=0, ge=0, le=100, description="Confidence score 0-100"
    )
    quests_completed: int = Field(
        default=0, description="Quests completed for this pattern"
    )
    quests_total: int = Field(
        default=0, description="Total essential quests for pattern"
    )
    concepts_understood: list[str] = Field(
        default_factory=list, description="Understood concepts"
    )
    concepts_total: int = Field(default=0, description="Total concepts in pattern")
    last_practiced: datetime | None = Field(
        default=None, description="Last practice timestamp"
    )
    next_review: datetime | None = Field(
        default=None, description="Spaced repetition due date"
    )
    mastered: bool = Field(default=False, description="Pattern mastery achieved")


class QuestCompletion(BaseModel):
    """Record of a completed quest."""

    id: str = Field(description="Unique ID (user_id + quest_id)")
    user_id: str = Field(default="default")
    quest_id: str = Field(description="Quest identifier")
    pattern_id: str = Field(description="Pattern this quest belongs to")
    completed_at: datetime = Field(default_factory=datetime.now)
    time_minutes: int | None = Field(default=None, description="Time taken in minutes")
    hints_used: int = Field(default=0, description="Number of hints used")
    success: bool = Field(default=True, description="Completed successfully")
    review_count: int = Field(default=0, description="Number of reviews done")
    last_reviewed: datetime | None = Field(default=None)
    next_review_in: int = Field(default=1, description="Days until next review")


class ConceptUnderstanding(BaseModel):
    """Track understanding of individual concepts within a pattern."""

    id: str = Field(description="Unique ID")
    user_id: str = Field(default="default")
    pattern_id: str = Field(description="Parent pattern")
    concept: str = Field(description="Concept name/description")
    understood: bool = Field(default=False, description="User understands this concept")
    diagnosed_at: datetime | None = Field(default=None, description="When diagnosed")
    taught_at: datetime | None = Field(default=None, description="When taught")
    notes: str = Field(default="", description="Additional notes")


# ==================== Deep Student Model (v4) ====================


class Mistake(BaseModel):
    """Track mistakes for pattern recognition and adaptive coaching."""

    id: str = Field(description="Unique ID (UUID)")
    user_id: str = Field(default="default")
    quest_id: str = Field(description="Quest where mistake occurred")
    pattern_id: str = Field(description="Pattern associated with mistake")
    mistake_type: str = Field(
        description="Type: off_by_one, edge_case, wrong_pattern, complexity, syntax"
    )
    description: str = Field(description="Description of the mistake")
    lesson_learned: str | None = Field(
        default=None, description="What was learned from this"
    )
    logged_at: datetime = Field(default_factory=datetime.now)
    recurrence_count: int = Field(
        default=1, description="How many times this mistake type occurred"
    )


class DailyLog(BaseModel):
    """Daily activity log for engagement tracking."""

    id: str = Field(description="Unique ID (user_id + date)")
    user_id: str = Field(default="default")
    date: str = Field(description="Date in YYYY-MM-DD format")
    problems_solved: int = Field(default=0, description="Problems solved this day")
    time_spent_mins: int = Field(
        default=0, description="Time spent learning in minutes"
    )
    patterns_worked: list[str] = Field(
        default_factory=list, description="Patterns worked on"
    )
    hints_used: int = Field(default=0, description="Hints used this day")


class Milestone(BaseModel):
    """Track achievements and wins for positive reinforcement."""

    id: str = Field(description="Unique ID (UUID)")
    user_id: str = Field(default="default")
    milestone_type: str = Field(
        description="Type: pattern_mastered, streak, no_hints, speed_improvement"
    )
    pattern_id: str | None = Field(
        default=None, description="Associated pattern if applicable"
    )
    quest_id: str | None = Field(
        default=None, description="Associated quest if applicable"
    )
    description: str = Field(description="Human-readable description of achievement")
    achieved_at: datetime = Field(default_factory=datetime.now)


class TeachingHistory(BaseModel):
    """Track what concepts have been taught and student response."""

    id: str = Field(description="Unique ID (user_id + pattern_id + concept)")
    user_id: str = Field(default="default")
    pattern_id: str = Field(description="Pattern this concept belongs to")
    concept: str = Field(description="Concept that was taught")
    explanation_count: int = Field(default=1, description="Number of times explained")
    last_explained: datetime = Field(default_factory=datetime.now)
    student_response: str = Field(
        default="unknown", description="Response: understood, confused, partially"
    )
