"""Named constants for DSA Coach business rules."""

# Progress scoring
POINTS_NO_HINTS: int = 15
POINTS_WITH_HINTS: int = 10
MASTERY_THRESHOLD: int = 80
NOTE_SUGGESTION_THRESHOLD: int = 70
MAX_PROGRESS: int = 100

# Spaced repetition intervals (days)
REVIEW_INTERVALS: list[int] = [1, 3, 7, 14, 30]

# Google L6 slice readiness targets (%)
SLICE_READINESS: dict[str, str] = {
    "slice-1": "70%",
    "slice-2": "85%",
    "slice-3": "93%",
}

# Validation sets
VALID_MISTAKE_TYPES: set[str] = {
    "off_by_one",
    "edge_case",
    "wrong_pattern",
    "complexity",
    "syntax",
    "logic",
    "other",
}
VALID_STUDENT_RESPONSES: set[str] = {
    "understood",
    "confused",
    "partially",
    "unknown",
}
VALID_MILESTONE_TYPES: set[str] = {
    "pattern_mastered",
    "streak",
    "no_hints",
    "speed_improvement",
    "first_solve",
    "concept_mastered",
    "other",
}
