from flask import Blueprint, request, jsonify
from .interviewer import LLMPoweredInterviewer
from .utils import generate_session_id, format_response
from .session_manager import session_manager
from .config import Config
import asyncio
import json
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)
config = Config()

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/session/start', methods=['POST'])
def start_session():
    """Start a new interview session with enhanced error handling"""
    try:
        data = request.get_json() or {}
        candidate_name = data.get('candidate_name', 'Candidate')
        
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
        
        return jsonify({
            "session_id": session_id,
            "welcome": welcome,
            "first_question": first_question,
            "candidate_name": candidate_name
        })
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        return jsonify(format_response(False, message=f"Failed to start session: {str(e)}")), 500

@bp.route('/session/<session_id>/message', methods=['POST'])
def send_message(session_id):
    """Handle incoming messages for a session (WebSocket handles actual processing)"""
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            return jsonify(format_response(False, message="Session not found")), 404
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify(format_response(False, message="Message is required")), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify(format_response(False, message="Message cannot be empty")), 400
        
        logger.info(f"Received message for session {session_id}: {len(message)} characters")
        
        return jsonify({
            "status": "accepted",
            "processing": True,
            "message_length": len(message)
        })
        
    except Exception as e:
        logger.error(f"Failed to process message for session {session_id}: {e}")
        return jsonify(format_response(False, message=f"Failed to process message: {str(e)}")), 500

@bp.route('/session/<session_id>/state', methods=['GET'])
def get_session_state(session_id):
    """Get current state of a session"""
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            return jsonify(format_response(False, message="Session not found")), 404
        
        state = interviewer.get_state()
        metadata = session_manager.session_metadata.get(session_id, {})
        
        # Add session metadata to state
        state['session_metadata'] = metadata
        
        logger.info(f"Retrieved state for session {session_id}")
        return jsonify(format_response(True, data=state))
        
    except Exception as e:
        logger.error(f"Failed to get session state for {session_id}: {e}")
        return jsonify(format_response(False, message=f"Failed to get session state: {str(e)}")), 500

@bp.route('/session/<session_id>/end', methods=['POST'])
def end_session(session_id):
    try:
        if not has_session(session_id):
            return jsonify(format_response(False, message="Session not found")), 404
        
        interviewer = get_session(session_id)
        
        if not interviewer.performance_data:
            return jsonify({
                "session_id": session_id,
                "average_score": 0,
                "total_questions": 0,
                "followups_count": 0,
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            })
        
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
            
        return jsonify({
            "session_id": session_id,
            "average_score": round(avg_score, 1),
            "total_questions": total_questions,
            "followups_count": followups_count,
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:3],
            "recommendations": recommendations[:3]
        })
        
    except Exception as e:
        return jsonify(format_response(False, message=f"Failed to end session: {str(e)}")), 500

@bp.route('/session/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export comprehensive session data"""
    try:
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            return jsonify(format_response(False, message="Session not found")), 404
        
        export_data = session_manager.export_session_data(session_id)
        if not export_data:
            return jsonify(format_response(False, message="Failed to export session data")), 500
        
        logger.info(f"Exported session data for {session_id}")
        return jsonify(format_response(True, data=export_data))
        
    except Exception as e:
        logger.error(f"Failed to export session {session_id}: {e}")
        return jsonify(format_response(False, message=f"Failed to export session: {str(e)}")), 500

@bp.route('/sessions/stats', methods=['GET'])
def get_session_stats():
    """Get overall session statistics"""
    try:
        stats = session_manager.get_session_stats()
        logger.info("Retrieved session statistics")
        return jsonify(format_response(True, data=stats))
        
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        return jsonify(format_response(False, message=f"Failed to get session stats: {str(e)}")), 500

@bp.route('/sessions/cleanup', methods=['POST'])
def cleanup_sessions():
    """Clean up expired sessions"""
    try:
        cleaned_count = session_manager.cleanup_expired_sessions()
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return jsonify(format_response(True, data={"cleaned_sessions": cleaned_count}))
        
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}")
        return jsonify(format_response(False, message=f"Failed to cleanup sessions: {str(e)}")), 500
