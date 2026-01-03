"""AI mentorship module for DSA Coach."""

from dsa_coach.ai.client import check_ai_available, get_ai_response
from dsa_coach.ai.hints import get_adaptive_hint
from dsa_coach.ai.learning import (
    continue_conversation,
    interactive_learning_session,
    start_design_session,
    start_learning_session,
)
from dsa_coach.ai.prompts import get_mentor_system_prompt
from dsa_coach.ai.review import review_code
from dsa_coach.ai.session import (
    delete_conversation,
    list_saved_conversations,
    load_conversation,
    save_conversation,
)
from dsa_coach.ai.ui import print_ai_response

__all__ = [
    "save_conversation",
    "load_conversation",
    "delete_conversation",
    "list_saved_conversations",
    "get_ai_response",
    "check_ai_available",
    "get_mentor_system_prompt",
    "print_ai_response",
    "get_adaptive_hint",
    "review_code",
    "interactive_learning_session",
    "start_learning_session",
    "start_design_session",
    "continue_conversation",
]
