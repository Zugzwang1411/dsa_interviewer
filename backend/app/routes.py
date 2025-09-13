from flask import Blueprint, request, jsonify
from .interviewer import LLMPoweredInterviewer
from .utils import generate_session_id, format_response
from .session_store import get_session, set_session, has_session
import asyncio
import json
import os

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/session/start', methods=['POST'])
def start_session():
    try:
        data = request.get_json() or {}
        candidate_name = data.get('candidate_name', 'Candidate')
        
        session_id = generate_session_id()
        interviewer = LLMPoweredInterviewer()
        set_session(session_id, interviewer)
        
        try:
            interviewer.load_from_file(session_id)
        except:
            pass
        
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
            "question": "What's the difference between arrays and linked lists? When would you use each?",
            "difficulty": "medium"
        }
        
        interviewer.stage = "questioning"
        interviewer.current_question = interviewer.questions[0]
        interviewer.questions_asked = 1
        
        interviewer.save_to_file(session_id)
        
        return jsonify({
            "session_id": session_id,
            "welcome": welcome,
            "first_question": first_question
        })
        
    except Exception as e:
        return jsonify(format_response(False, message=f"Failed to start session: {str(e)}")), 500

@bp.route('/session/<session_id>/message', methods=['POST'])
def send_message(session_id):
    try:
        if not has_session(session_id):
            return jsonify(format_response(False, message="Session not found")), 404
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify(format_response(False, message="Message is required")), 400
        
        return jsonify({
            "status": "accepted",
            "processing": True
        })
        
    except Exception as e:
        return jsonify(format_response(False, message=f"Failed to process message: {str(e)}")), 500

@bp.route('/session/<session_id>/state', methods=['GET'])
def get_session_state(session_id):
    try:
        if not has_session(session_id):
            return jsonify(format_response(False, message="Session not found")), 404
        
        interviewer = get_session(session_id)
        state = interviewer.get_state()
        
        return jsonify(format_response(True, data=state))
        
    except Exception as e:
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
    try:
        if not has_session(session_id):
            return jsonify(format_response(False, message="Session not found")), 404
        
        interviewer = get_session(session_id)
        state = interviewer.get_state()
        
        return jsonify(format_response(True, data=state))
        
    except Exception as e:
        return jsonify(format_response(False, message=f"Failed to export session: {str(e)}")), 500
