"""
Shared session store for the DSA Interviewer application.
This ensures that both REST API routes and Socket.IO handlers
can access the same session data.
"""

from typing import Dict, Any
from .interviewer import LLMPoweredInterviewer

# Global session store
session_store: Dict[str, LLMPoweredInterviewer] = {}

def get_session(session_id: str) -> LLMPoweredInterviewer:
    """Get a session by ID."""
    return session_store.get(session_id)

def set_session(session_id: str, interviewer: LLMPoweredInterviewer) -> None:
    """Set a session by ID."""
    session_store[session_id] = interviewer

def has_session(session_id: str) -> bool:
    """Check if a session exists."""
    return session_id in session_store

def remove_session(session_id: str) -> None:
    """Remove a session by ID."""
    if session_id in session_store:
        del session_store[session_id]

def get_all_sessions() -> Dict[str, LLMPoweredInterviewer]:
    """Get all sessions."""
    return session_store.copy()
