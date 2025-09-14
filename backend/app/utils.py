import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def generate_session_id() -> str:
    """Generate a unique session ID using UUID4"""
    session_id = str(uuid.uuid4())
    logger.debug(f"Generated session ID: {session_id}")
    return session_id

def format_response(success: bool, data: Any = None, message: str = None) -> Dict[str, Any]:
    """Format API response with consistent structure"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return response

def validate_session_id(session_id: str) -> bool:
    """Validate session ID format"""
    try:
        uuid.UUID(session_id)
        return True
    except ValueError:
        logger.warning(f"Invalid session ID format: {session_id}")
        return False

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not isinstance(text, str):
        return ""
    
    # Remove potentially dangerous characters
    sanitized = text.strip()
    # Add more sanitization as needed
    return sanitized
