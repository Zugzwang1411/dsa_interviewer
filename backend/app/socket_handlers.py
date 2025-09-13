from flask_socketio import emit
import asyncio
from datetime import datetime
from .interviewer import LLMPoweredInterviewer
from .utils import generate_session_id
from .session_store import get_session, set_session, has_session

socketio = None

def init_socketio(socketio_instance):
    global socketio
    socketio = socketio_instance
    
    @socketio_instance.on('connect')
    def handle_connect():
        print(f"🔍 Backend: Client connected")
    
    @socketio_instance.on('disconnect')
    def handle_disconnect(data=None):
        print(f"🔍 Backend: Client disconnected")
    
    @socketio_instance.on_error_default
    def default_error_handler(e):
        print(f"🔍 Backend: Socket.IO error: {e}")
        print(f"🔍 Backend: Error type: {type(e)}")
    
    # Test event to see if any custom events are received
    @socketio_instance.on('test')
    def handle_test(data):
        print(f"🔍 Backend: Received test event: {data}")
    
    @socketio_instance.on('start_session')
    def handle_start_session(data):
        try:
            print(f"🔍 Backend: Received start_session data: {data}, type: {type(data)}")
            
            # Handle case where data might be a string or not a dict
            if isinstance(data, str):
                emit('error', {'message': 'Invalid data format received'})
                return
            
            if not isinstance(data, dict):
                emit('error', {'message': f'Expected dict, got {type(data)}'})
                return
                
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
                
            emit('session_started', {
                'session_id': session_id,
                'welcome': welcome,
                'first_question': first_question
            })
            
        except Exception as e:
            emit('error', {'message': f'Failed to start session: {str(e)}'})
    
    @socketio_instance.on('user_message')
    def handle_user_message(data):
        try:
            print(f"🔍 Backend: Received user_message data: {data}, type: {type(data)}")
            
            # Handle case where data might be a string or not a dict
            if isinstance(data, str):
                emit('error', {'message': 'Invalid data format received'})
                return
            
            if not isinstance(data, dict):
                emit('error', {'message': f'Expected dict, got {type(data)}'})
                return
                
            session_id = data.get('session_id')
            message = data.get('message')
            
            if not session_id or not has_session(session_id):
                emit('error', {'message': 'Session not found'})
                return
            
            if not message:
                emit('error', {'message': 'Message is required'})
                return
            
            interviewer = get_session(session_id)
            
            emit('bot_typing', {'session_id': session_id})
            
            def run_async_process():
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
                                'difficulty': interviewer.current_question['difficulty']
                            }
                        })
                    elif interviewer.stage == "questioning":
                        loop.run_until_complete(process_answer_with_events(session_id, interviewer, message, socketio_instance))
                    elif interviewer.stage == "following_up":
                        loop.run_until_complete(process_followup_with_events(session_id, interviewer, message, socketio_instance))
                    
                    interviewer.save_to_file(session_id)
                    
                except Exception as e:
                    socketio_instance.emit('error', {'message': f'Processing error: {str(e)}'})
                finally:
                    loop.close()
            
            socketio_instance.start_background_task(run_async_process)
            
        except Exception as e:
            emit('error', {'message': f'Failed to process message: {str(e)}'})

async def process_answer_with_events(session_id, interviewer, message, socketio_instance):
    print(f"🚀 Backend: process_answer_with_events called with message: '{message[:50]}...'")
    current_q = interviewer.current_question
    
    analysis = await interviewer.analyze_answer_with_llm(
        current_q['question'], 
        message, 
        current_q['key_concepts']
    )
    
    print(f"🔍 Backend: Emitting analysis for session {session_id}, score: {analysis['score']}")
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
    
    print(f"🔍 Backend: Emitting feedback for session {session_id}")
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
    
    print(f"🔍 Backend: Should followup? {should_followup}, score: {analysis['score']}, followup_count: {interviewer.current_followup_count}, max_followups: {interviewer.max_followups}")
    print(f"🔍 Backend: Logic check - should_followup: {should_followup}, can_do_more: {interviewer.current_followup_count < interviewer.max_followups}")
    
    if should_followup and interviewer.current_followup_count < interviewer.max_followups:
        print(f"✅ Backend: Generating follow-up question for low score ({analysis['score']})")
        interviewer.stage = "following_up"
        interviewer.current_followup_count += 1
        followup_q = await interviewer.generate_followup_question_llm(
            current_q['question'],
            message,
            current_q['key_concepts'],
            analysis['raw_analysis']
        )
        
        print(f"✅ Backend: Emitting follow-up question: {followup_q[:50]}...")
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
        print(f"✅ Backend: Good score ({analysis['score']}) - waiting 3s then moving to next question...")
        # Give frontend time to display analysis before moving to next question
        await asyncio.sleep(3)
        await move_to_next_question(session_id, interviewer, socketio_instance)

async def process_followup_with_events(session_id, interviewer, message, socketio_instance):
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
    
    print(f"🔍 Backend: Follow-up processing - Should followup? {should_followup}, score: {analysis['score']}, followup_count: {interviewer.current_followup_count}, max_followups: {interviewer.max_followups}")
    
    if should_followup and interviewer.current_followup_count < interviewer.max_followups:
        interviewer.current_followup_count += 1
        followup_q = await interviewer.generate_followup_question_llm(
            current_q['question'],
            message,
            current_q['key_concepts'],
            analysis['raw_analysis']
        )
        
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
        print(f"🔍 Backend: No followup needed, waiting 3s then moving to next question...")
        # Give frontend time to display analysis before moving to next question
        await asyncio.sleep(3)
        await move_to_next_question(session_id, interviewer, socketio_instance)

async def move_to_next_question(session_id, interviewer, socketio_instance):
    interviewer.current_question_idx += 1
    interviewer.stage = "questioning"
    interviewer.current_followup_count = 0
    
    if interviewer.current_question_idx >= len(interviewer.questions):
        summary = await interviewer.end_interview()
        socketio_instance.emit('interview_summary', {
            'session_id': session_id,
            'summary': summary
        })
        return
    
    interviewer.current_question = interviewer.questions[interviewer.current_question_idx]
    interviewer.questions_asked += 1
    
    socketio_instance.emit('next_question', {
        'session_id': session_id,
        'question': {
            'id': interviewer.current_question['id'],
            'question': interviewer.current_question['question'],
            'difficulty': interviewer.current_question['difficulty']
        }
    })
