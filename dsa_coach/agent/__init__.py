"""Agent core module for DSA Coach."""


def get_coach_agent():
    """Return the primary agent class."""
    from .sdk_agent import SDKCoachAgent

    return SDKCoachAgent


def get_session_manager():
    from .session import SessionManager

    return SessionManager


__all__ = ["get_coach_agent", "get_session_manager"]
