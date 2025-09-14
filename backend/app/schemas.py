"""
Pydantic models for request/response validation in FastAPI
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SessionStartRequest(BaseModel):
    """Request model for starting a new session"""
    candidate_name: Optional[str] = Field(default="Candidate", description="Name of the candidate")


class MessageRequest(BaseModel):
    """Request model for sending a message"""
    message: str = Field(..., min_length=1, description="Message content")


class SessionStartResponse(BaseModel):
    """Response model for session start"""
    session_id: str
    welcome: str
    first_question: Dict[str, Any]
    candidate_name: str


class MessageResponse(BaseModel):
    """Response model for message acceptance"""
    status: str
    processing: bool
    message_length: int


class AnalysisData(BaseModel):
    """Analysis data structure"""
    raw_analysis: str
    score: int
    normalized_score: float
    concepts_covered: List[str]
    missing_concepts: List[str]
    quality: str
    depth: str
    detailed_analysis: str


class PerformanceEntry(BaseModel):
    """Performance entry structure"""
    question_id: int
    question: str
    answer: str
    analysis: AnalysisData
    feedback: str
    timestamp: str
    is_followup: bool


class InterviewState(BaseModel):
    """Interview state structure"""
    current_question_idx: int
    questions_asked: int
    stage: str
    current_question: Optional[Dict[str, Any]]
    current_followup_count: int
    performance_data: List[PerformanceEntry]
    conversation_history: List[Dict[str, str]]


class SessionStateResponse(BaseModel):
    """Response model for session state"""
    success: bool
    data: InterviewState
    timestamp: str


class SessionMetadata(BaseModel):
    """Session metadata structure"""
    created_at: str
    last_activity: str
    status: str
    questions_answered: int
    followups_answered: int


class SessionEndResponse(BaseModel):
    """Response model for session end"""
    session_id: str
    average_score: float
    total_questions: int
    followups_count: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class SessionExportResponse(BaseModel):
    """Response model for session export"""
    success: bool
    data: Dict[str, Any]
    timestamp: str


class SessionStats(BaseModel):
    """Session statistics"""
    active_sessions: int
    total_sessions: int
    data_directory: str


class SessionStatsResponse(BaseModel):
    """Response model for session stats"""
    success: bool
    data: SessionStats
    timestamp: str


class CleanupResponse(BaseModel):
    """Response model for session cleanup"""
    success: bool
    data: Dict[str, int]
    timestamp: str




# WebSocket messages are handled as plain dictionaries for simplicity
