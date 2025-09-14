from fastapi import APIRouter, HTTPException
from .interviewer import LLMPoweredInterviewer
from .session_manager import session_manager
from .config import Config
from .schemas import (
    SessionStartRequest, SessionStartResponse, MessageRequest, MessageResponse,
    SessionStateResponse, SessionEndResponse, SessionExportResponse,
    SessionStatsResponse, CleanupResponse
)
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
config = Config()

router = APIRouter()

@router.post('/session/start', response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """Start a new interview session with enhanced error handling"""
    try:
        candidate_name = request.candidate_name
        
        # Create new session using session manager
        session_id, interviewer = session_manager.create_session()
        
        # Initialize interview state
        interviewer.stage = "questioning"
        interviewer.current_question = interviewer.questions[0]
        interviewer.questions_asked = 1
        
        # Save initial state
        session_manager.save_session(session_id)
        
        welcome = """Welcome to your AI-driven Data Structures & Algorithms interview!

🧠 Powered by Advanced AI:
- Dynamic feedback tailored to your specific answers  
- Smart follow-up questions based on your performance
- Intelligent conversation that adapts to your responses

📋 Interview Format:
- 5 DSA questions covering core concepts
- AI analyzes each answer for technical accuracy and depth
- Personalized feedback with improvement suggestions
- Up to 2 follow-up questions per topic to deepen understanding
- Comprehensive AI-generated performance summary

Ready to begin? Let's start this intelligent interview experience!"""
        
        first_question = {
            "id": 1,
            "question": interviewer.questions[0]['question'],
            "difficulty": interviewer.questions[0]['difficulty'],
            "key_concepts": interviewer.questions[0]['key_concepts']
        }
        
        logger.info(f"Started new session: {session_id} for candidate: {candidate_name}")
        
        return SessionStartResponse(
            session_id=session_id,
            welcome=welcome,
            first_question=first_question,
            candidate_name=candidate_name
        )
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@router.post('/session/{session_id}/message', response_model=MessageResponse)
async def send_message(session_id: str, request: MessageRequest):
    """Handle incoming messages for a session (WebSocket handles actual processing)"""
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            raise HTTPException(status_code=404, detail="Session not found")
        
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Received message for session {session_id}: {len(message)} characters")
        
        return MessageResponse(
            status="accepted",
            processing=True,
            message_length=len(message)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get('/session/{session_id}/state', response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Get current state of a session"""
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = interviewer.get_state()
        metadata = session_manager.session_metadata.get(session_id, {})
        
        # Add session metadata to state
        state['session_metadata'] = metadata
        
        logger.info(f"Retrieved state for session {session_id}")
        return SessionStateResponse(
            success=True,
            data=state,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session state for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session state: {str(e)}")

@router.post('/session/{session_id}/end', response_model=SessionEndResponse)
async def end_session(session_id: str):
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not interviewer.performance_data:
            return SessionEndResponse(
                session_id=session_id,
                average_score=0,
                total_questions=0,
                followups_count=0,
                strengths=[],
                weaknesses=[],
                recommendations=[]
            )
        
        main_scores = [p['analysis']['score'] for p in interviewer.performance_data if not p['is_followup']]
        avg_score = sum(main_scores) / len(main_scores) if main_scores else 0
        
        total_questions = len([p for p in interviewer.performance_data if not p['is_followup']])
        followups_count = len([p for p in interviewer.performance_data if p['is_followup']])
        
        strengths = []
        weaknesses = []
        recommendations = []
        
        for perf in interviewer.performance_data:
            if not perf['is_followup']:
                if perf['analysis']['score'] >= 7:
                    strengths.append(f"Good understanding of {perf['question']}")
                else:
                    weaknesses.append(f"Needs improvement in {', '.join(perf['analysis']['missing_concepts'])}")
        
        if avg_score < 6:
            recommendations.append("Review fundamental DSA concepts")
            recommendations.append("Practice more coding problems")
        if avg_score >= 6:
            recommendations.append("Continue practicing advanced problems")
            
        return SessionEndResponse(
            session_id=session_id,
            average_score=round(avg_score, 1),
            total_questions=total_questions,
            followups_count=followups_count,
            strengths=strengths[:3],
            weaknesses=weaknesses[:3],
            recommendations=recommendations[:3]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

@router.get('/session/{session_id}/export', response_model=SessionExportResponse)
async def export_session(session_id: str):
    """Export comprehensive session data"""
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            raise HTTPException(status_code=404, detail="Session not found")
        
        export_data = session_manager.export_session_data(session_id)
        if not export_data:
            raise HTTPException(status_code=500, detail="Failed to export session data")
        
        logger.info(f"Exported session data for {session_id}")
        return SessionExportResponse(
            success=True,
            data=export_data,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")

@router.get('/sessions/stats', response_model=SessionStatsResponse)
async def get_session_stats():
    """Get overall session statistics"""
    try:
        stats = session_manager.get_session_stats()
        logger.info("Retrieved session statistics")
        return SessionStatsResponse(
            success=True,
            data=stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")

@router.post('/sessions/cleanup', response_model=CleanupResponse)
async def cleanup_sessions():
    """Clean up expired sessions"""
    try:
        cleaned_count = session_manager.cleanup_expired_sessions()
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return CleanupResponse(
            success=True,
            data={"cleaned_sessions": cleaned_count},
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup sessions: {str(e)}")
