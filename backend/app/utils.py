import uuid
from typing import Dict, Any

def generate_session_id() -> str:
    return str(uuid.uuid4())

def format_response(success: bool, data: Any = None, message: str = None) -> Dict[str, Any]:
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return response
