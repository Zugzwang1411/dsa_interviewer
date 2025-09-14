from flask_socketio import emit
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .interviewer import LLMPoweredInterviewer
from .session_manager import session_manager
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)
config = Config()

socketio = None

def init_socketio(socketio_instance):
    """Initialize WebSocket handlers with enhanced error handling and logging"""
    global socketio
    socketio = socketio_instance
    
    @socketio_instance.on('connect')
    def handle_connect():
        logger.info("Client connected to WebSocket")
        emit('connected', {'message': 'Connected to DSA Interviewer'})
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected from WebSocket")
    
    @socketio_instance.on_error_default
    def default_error_handler(e):
        logger.error(f"Socket.IO error: {e}")
        emit('error', {'message': f'WebSocket error: {str(e)}'})
    
    @socketio_instance.on('ping')
    def handle_ping(data):
        """Handle ping for connection health check"""
        logger.debug("Received ping from client")
        emit('pong', {'timestamp': datetime.now().isoformat()})
    
    @socketio_instance.on('start_session')
    def handle_start_session(data: Dict[str, Any]):
        """Handle session start with enhanced error handling"""
        try:
            logger.info(f"Received start_session request: {data}")
            
            # Validate input data
            if not isinstance(data, dict):
                emit('error', {'message': 'Invalid data format received'})
                return
                
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
                "id": interviewer.questions[0]['id'],
                "question": interviewer.questions[0]['question'],
                "difficulty": interviewer.questions[0]['difficulty'],
                "key_concepts": interviewer.questions[0]['key_concepts']
            }
            
            logger.info(f"Started session {session_id} for candidate: {candidate_name}")
            
            emit('session_started', {
                'session_id': session_id,
                'welcome': welcome,
                'first_question': first_question,
                'candidate_name': candidate_name
            })
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            emit('error', {'message': f'Failed to start session: {str(e)}'})
    
    @socketio_instance.on('user_message')
    def handle_user_message(data: Dict[str, Any]):
        """Handle user messages with enhanced error handling and logging"""
        try:
            logger.info(f"Received user message: {data}")
            
            # Validate input data
            if not isinstance(data, dict):
                emit('error', {'message': 'Invalid data format received'})
                return
                
            session_id = data.get('session_id')
            message = data.get('message')
            
            if not session_id:
                emit('error', {'message': 'Session ID is required'})
                return
                
            if not message or not message.strip():
                emit('error', {'message': 'Message is required and cannot be empty'})
                return
            
            # Get session using session manager
            interviewer = session_manager.get_session(session_id)
            if not interviewer:
                emit('error', {'message': 'Session not found'})
                return
            
            logger.info(f"Processing message for session {session_id}: {len(message)} characters")
            
            emit('bot_typing', {'session_id': session_id})
            
            def run_async_process():
                """Run async processing in background task"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if interviewer.stage == "greeting":
                        response = loop.run_until_complete(interviewer.process_greeting(message))
                        socketio_instance.emit('next_question', {
                            'session_id': session_id,
                            'question': {
                                'id': interviewer.current_question['id'],
                                'question': interviewer.current_question['question'],
                                'difficulty': interviewer.current_question['difficulty'],
                                'key_concepts': interviewer.current_question['key_concepts']
                            }
                        })
                    elif interviewer.stage == "questioning":
                        loop.run_until_complete(process_answer_with_events(session_id, interviewer, message, socketio_instance))
                    elif interviewer.stage == "following_up":
                        loop.run_until_complete(process_followup_with_events(session_id, interviewer, message, socketio_instance))
                    
                    # Save session state
                    session_manager.save_session(session_id)
                    
                except Exception as e:
                    logger.error(f"Error processing message for session {session_id}: {e}")
                    socketio_instance.emit('error', {'message': f'Processing error: {str(e)}'})
                finally:
                    loop.close()
            
            socketio_instance.start_background_task(run_async_process)
            
        except Exception as e:
            logger.error(f"Failed to process user message: {e}")
            emit('error', {'message': f'Failed to process message: {str(e)}'})

async def process_answer_with_events(session_id: str, interviewer: LLMPoweredInterviewer, message: str, socketio_instance):
    """Process answer with real-time WebSocket events"""
    logger.info(f"Processing answer for session {session_id}: {message[:50]}...")
    current_q = interviewer.current_question
    
    analysis = await interviewer.analyze_answer_with_llm(
        current_q['question'], 
        message, 
        current_q['key_concepts']
    )
    
    logger.info(f"Emitting analysis for session {session_id}, score: {analysis['score']}")
    socketio_instance.emit('analysis', {
        'session_id': session_id,
        'analysis': analysis
    })
    
    feedback = await interviewer.generate_feedback_with_llm(
        current_q['question'],
        message,
        analysis['raw_analysis'],
        analysis['score'],
        interviewer.current_question_idx
    )
    
    logger.info(f"Emitting feedback for session {session_id}")
    socketio_instance.emit('feedback', {
        'session_id': session_id,
        'feedback': feedback
    })
    
    interviewer.performance_data.append({
        "question_id": current_q['id'],
        "question": current_q['question'],
        "answer": message,
        "analysis": analysis,
        "feedback": feedback,
        "timestamp": datetime.now().isoformat(),
        "is_followup": False
    })
    
    interviewer.conversation_history.append({"role": "user", "content": message})
    interviewer.conversation_history.append({"role": "assistant", "content": feedback})
    
    should_followup = await interviewer.should_ask_followup_llm(
        current_q['question'],
        message,
        analysis['score'],
        analysis['raw_analysis']
    )
    
    logger.info(f"Follow-up decision: {should_followup}, score: {analysis['score']}, followup_count: {interviewer.current_followup_count}, max_followups: {interviewer.max_followups}")
    
    if should_followup and interviewer.current_followup_count < interviewer.max_followups:
        logger.info(f"Generating follow-up question for score {analysis['score']}")
        interviewer.stage = "following_up"
        interviewer.current_followup_count += 1
        followup_q = await interviewer.generate_followup_question_llm(
            current_q['question'],
            message,
            current_q['key_concepts'],
            analysis['raw_analysis']
        )
        
        logger.info(f"Emitting follow-up question: {followup_q[:50]}...")
        socketio_instance.emit('followup_question', {
            'session_id': session_id,
            'question': {
                'id': current_q['id'],
                'question': followup_q
            }
        })
        
        interviewer.conversation_history.append({"role": "assistant", "content": followup_q})
    else:
        interviewer.current_followup_count = 0
        logger.info(f"Good score ({analysis['score']}) - moving to next question")
        # Give frontend time to display analysis before moving to next question
        await asyncio.sleep(3)
        await move_to_next_question(session_id, interviewer, socketio_instance)

async def process_followup_with_events(session_id: str, interviewer: LLMPoweredInterviewer, message: str, socketio_instance):
    """Process follow-up answer with real-time WebSocket events"""
    logger.info(f"Processing follow-up for session {session_id}: {message[:50]}...")
    current_q = interviewer.current_question
    
    analysis = await interviewer.analyze_answer_with_llm(
        current_q['follow_ups'][interviewer.current_followup_count - 1],
        message,
        current_q['key_concepts']
    )
    
    socketio_instance.emit('analysis', {
        'session_id': session_id,
        'analysis': analysis
    })
    
    feedback = await interviewer.generate_feedback_with_llm(
        current_q['follow_ups'][interviewer.current_followup_count - 1],
        message,
        analysis['raw_analysis'],
        analysis['score'],
        interviewer.current_question_idx
    )
    
    socketio_instance.emit('feedback', {
        'session_id': session_id,
        'feedback': feedback
    })
    
    interviewer.performance_data.append({
        "question_id": current_q['id'],
        "question": current_q['follow_ups'][interviewer.current_followup_count - 1],
        "answer": message,
        "analysis": analysis,
        "feedback": feedback,
        "timestamp": datetime.now().isoformat(),
        "is_followup": True
    })
    
    interviewer.conversation_history.append({"role": "user", "content": message})
    interviewer.conversation_history.append({"role": "assistant", "content": feedback})
    
    should_followup = await interviewer.should_ask_followup_llm(
        current_q['follow_ups'][interviewer.current_followup_count - 1],
        message,
        analysis['score'],
        analysis['raw_analysis']
    )
    
    logger.info(f"Follow-up processing - Should followup? {should_followup}, score: {analysis['score']}, followup_count: {interviewer.current_followup_count}, max_followups: {interviewer.max_followups}")
    
    if should_followup and interviewer.current_followup_count < interviewer.max_followups:
        interviewer.current_followup_count += 1
        followup_q = await interviewer.generate_followup_question_llm(
            current_q['question'],
            message,
            current_q['key_concepts'],
            analysis['raw_analysis']
        )
        
        logger.info(f"Emitting follow-up question: {followup_q[:50]}...")
        socketio_instance.emit('followup_question', {
            'session_id': session_id,
            'question': {
                'id': current_q['id'],
                'question': followup_q
            }
        })
        
        interviewer.conversation_history.append({"role": "assistant", "content": followup_q})
    else:
        interviewer.current_followup_count = 0
        logger.info("No follow-up needed, moving to next question")
        # Give frontend time to display analysis before moving to next question
        await asyncio.sleep(3)
        await move_to_next_question(session_id, interviewer, socketio_instance)

async def move_to_next_question(session_id: str, interviewer: LLMPoweredInterviewer, socketio_instance):
    """Move to the next question or end interview"""
    interviewer.current_question_idx += 1
    interviewer.stage = "questioning"
    interviewer.current_followup_count = 0
    
    if interviewer.current_question_idx >= len(interviewer.questions):
        logger.info(f"Interview completed for session {session_id}")
        summary = await interviewer.end_interview()
        socketio_instance.emit('interview_summary', {
            'session_id': session_id,
            'summary': summary
        })
        return
    
    interviewer.current_question = interviewer.questions[interviewer.current_question_idx]
    interviewer.questions_asked += 1
    
    logger.info(f"Moving to question {interviewer.questions_asked} for session {session_id}")
    socketio_instance.emit('next_question', {
        'session_id': session_id,
        'question': {
            'id': interviewer.current_question['id'],
            'question': interviewer.current_question['question'],
            'difficulty': interviewer.current_question['difficulty'],
            'key_concepts': interviewer.current_question['key_concepts']
        }
    })
