import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from .interviewer import LLMPoweredInterviewer
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)

class SessionManager:
    """Enhanced session manager with timeout handling and analytics"""
    
    def __init__(self):
        self.active_sessions: Dict[str, LLMPoweredInterviewer] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.config = Config()
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"SessionManager initialized with data directory: {self.data_dir}")
    
    def create_session(self, session_id: Optional[str] = None) -> tuple[str, LLMPoweredInterviewer]:
        """Create a new interview session with optional custom session ID"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        interviewer = LLMPoweredInterviewer()
        self.active_sessions[session_id] = interviewer
        
        # Initialize session metadata
        self.session_metadata[session_id] = {
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'status': 'active',
            'questions_answered': 0,
            'followups_answered': 0
        }
        
        # Try to load existing session data
        file_path = os.path.join(self.data_dir, f'{session_id}.json')
        if os.path.exists(file_path):
            try:
                interviewer.load_from_file(session_id)
                logger.info(f"Loaded existing session data for {session_id}")
            except Exception as e:
                logger.warning(f"Failed to load session {session_id}: {e}")
        
        logger.info(f"Created new session: {session_id}")
        return session_id, interviewer
    
    def get_session(self, session_id: str) -> Optional[LLMPoweredInterviewer]:
        """Get an active session, loading from disk if necessary"""
        if session_id in self.active_sessions:
            # Update last activity
            if session_id in self.session_metadata:
                self.session_metadata[session_id]['last_activity'] = datetime.now().isoformat()
            return self.active_sessions[session_id]
        
        # Try to load from disk
        file_path = os.path.join(self.data_dir, f'{session_id}.json')
        if os.path.exists(file_path):
            interviewer = LLMPoweredInterviewer()
            try:
                interviewer.load_from_file(session_id)
                self.active_sessions[session_id] = interviewer
                
                # Initialize metadata if not exists
                if session_id not in self.session_metadata:
                    self.session_metadata[session_id] = {
                        'created_at': datetime.now().isoformat(),
                        'last_activity': datetime.now().isoformat(),
                        'status': 'active',
                        'questions_answered': 0,
                        'followups_answered': 0
                    }
                
                logger.info(f"Loaded session from disk: {session_id}")
                return interviewer
            except Exception as e:
                logger.error(f"Failed to load session {session_id}: {e}")
        
        logger.warning(f"Session not found: {session_id}")
        return None
    
    def save_session(self, session_id: str) -> bool:
        """Save session data to disk with error handling"""
        if session_id in self.active_sessions:
            try:
                self.active_sessions[session_id].save_to_file(session_id)
                logger.info(f"Saved session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to save session {session_id}: {e}")
                return False
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from memory and disk"""
        success = True
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Removed session from memory: {session_id}")
        
        # Remove metadata
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        
        # Remove from disk
        file_path = os.path.join(self.data_dir, f'{session_id}.json')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted session file: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete session file {session_id}: {e}")
                success = False
        
        return success
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up sessions that have exceeded the timeout period"""
        timeout_seconds = self.config.SESSION_TIMEOUT
        cutoff_time = datetime.now() - timedelta(seconds=timeout_seconds)
        cleaned_count = 0
        
        expired_sessions = []
        for session_id, metadata in self.session_metadata.items():
            last_activity = datetime.fromisoformat(metadata['last_activity'])
            if last_activity < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        active_count = len(self.active_sessions)
        total_metadata = len(self.session_metadata)
        
        return {
            'active_sessions': active_count,
            'total_sessions': total_metadata,
            'data_directory': self.data_dir
        }
    
    def export_session_data(self, session_id: str) -> Optional[dict]:
        """Export comprehensive session data for analysis"""
        interviewer = self.get_session(session_id)
        if interviewer:
            metadata = self.session_metadata.get(session_id, {})
            return {
                'session_id': session_id,
                'state': interviewer.get_state(),
                'metadata': metadata,
                'export_timestamp': datetime.now().isoformat()
            }
        return None

session_manager = SessionManager()
