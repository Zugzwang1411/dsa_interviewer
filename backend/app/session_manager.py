import os
import json
from typing import Dict, Optional
from .interviewer import LLMPoweredInterviewer

class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, LLMPoweredInterviewer] = {}
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def create_session(self, session_id: str) -> LLMPoweredInterviewer:
        interviewer = LLMPoweredInterviewer()
        self.active_sessions[session_id] = interviewer
        
        file_path = os.path.join(self.data_dir, f'{session_id}.json')
        if os.path.exists(file_path):
            try:
                interviewer.load_from_file(session_id)
            except Exception as e:
                print(f"Failed to load session {session_id}: {e}")
        
        return interviewer
    
    def get_session(self, session_id: str) -> Optional[LLMPoweredInterviewer]:
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        file_path = os.path.join(self.data_dir, f'{session_id}.json')
        if os.path.exists(file_path):
            interviewer = LLMPoweredInterviewer()
            try:
                interviewer.load_from_file(session_id)
                self.active_sessions[session_id] = interviewer
                return interviewer
            except Exception as e:
                print(f"Failed to load session {session_id}: {e}")
        
        return None
    
    def save_session(self, session_id: str):
        if session_id in self.active_sessions:
            try:
                self.active_sessions[session_id].save_to_file(session_id)
            except Exception as e:
                print(f"Failed to save session {session_id}: {e}")
    
    def delete_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        file_path = os.path.join(self.data_dir, f'{session_id}.json')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete session file {session_id}: {e}")
    
    def export_session_data(self, session_id: str) -> Optional[dict]:
        interviewer = self.get_session(session_id)
        if interviewer:
            return {
                'session_id': session_id,
                'state': interviewer.get_state(),
                'export_timestamp': json.dumps(None, default=str)
            }
        return None

session_manager = SessionManager()
