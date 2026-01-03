"""Agent core module for DSA Coach.

This module contains the CoachAgent class and related components
for the AI-powered coaching experience.
"""

# Defer imports to avoid circular dependencies at module load time
def get_coach_agent():
    from .agent import CoachAgent
    return CoachAgent

def get_session_manager():
    from .session import SessionManager
    return SessionManager

__all__ = ["get_coach_agent", "get_session_manager"]

