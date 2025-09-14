"""
FastAPI WebSocket handlers for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from .interviewer import LLMPoweredInterviewer
from .session_manager import session_manager
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)
config = Config()

# Create router for WebSocket endpoints
websocket_router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_id_mapping: Dict[str, str] = {}  # Maps connection_id -> actual_session_id
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept WebSocket connection and store it"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected with connection ID: {connection_id}")
        
        # Send connection confirmation
        await self.send_message(connection_id, {
            "type": "connected",
            "data": {"message": "Connected to DSA Interviewer"}
        })
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Clean up session mapping if exists
            if connection_id in self.session_id_mapping:
                del self.session_id_mapping[connection_id]
            logger.info(f"WebSocket disconnected for connection: {connection_id}")
    
    def map_session_id(self, connection_id: str, session_id: str):
        """Map connection ID to actual session ID"""
        self.session_id_mapping[connection_id] = session_id
        logger.info(f"Mapped connection {connection_id} to session {session_id}")
    
    async def send_message(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to connection {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_all(self, message: dict):
        """Send message to all connected sessions"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_message(connection_id, message)

# Global connection manager
manager = ConnectionManager()

@websocket_router.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    """Main WebSocket endpoint for session communication"""
    await manager.connect(websocket, connection_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "")
            
            # Handle different message types
            if message_type == "ping":
                await handle_ping(connection_id, message_data)
            elif message_type == "start_session":
                await handle_start_session(connection_id, message_data)
            elif message_type == "user_message":
                await handle_user_message(connection_id, message_data)
            else:
                await manager.send_message(connection_id, {
                    "type": "error",
                    "data": {"message": f"Unknown message type: {message_type}"}
                })
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
        await manager.send_message(connection_id, {
            "type": "error",
            "data": {"message": f"WebSocket error: {str(e)}"}
        })
        manager.disconnect(connection_id)

async def handle_ping(connection_id: str, data: dict):
    """Handle ping messages"""
    logger.debug(f"Received ping from connection {connection_id}")
    await manager.send_message(connection_id, {
        "type": "pong",
        "data": {"timestamp": datetime.now().isoformat()}
    })

async def handle_start_session(connection_id: str, data: dict):
    """Handle session start requests"""
    try:
        logger.info(f"Received start_session request for connection {connection_id}: {data}")
        
        # Validate input data
        if not isinstance(data, dict):
            await manager.send_message(connection_id, {
                "type": "error",
                "data": {"message": "Invalid data format received"}
            })
            return
            
        candidate_name = data.get("data", {}).get("candidate_name", "Candidate")
        
        # Create new session using session manager
        new_session_id, interviewer = session_manager.create_session()
        
        # Map connection ID to session ID
        manager.map_session_id(connection_id, new_session_id)
        
        # Initialize interview state
        interviewer.stage = "questioning"
        interviewer.current_question = interviewer.questions[0]
        interviewer.questions_asked = 1
        
        # Save initial state
        session_manager.save_session(new_session_id)
        
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
        
        logger.info(f"Started session {new_session_id} for candidate: {candidate_name}")
        
        await manager.send_message(connection_id, {
            "type": "session_started",
            "data": {
                "session_id": new_session_id,
                "welcome": welcome,
                "first_question": first_question,
                "candidate_name": candidate_name
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        await manager.send_message(connection_id, {
            "type": "error",
            "data": {"message": f"Failed to start session: {str(e)}"}
        })

async def handle_user_message(connection_id: str, data: dict):
    """Handle user messages with enhanced error handling and logging"""
    try:
        logger.info(f"Received user message for connection {connection_id}: {data}")
        
        # Get actual session ID from connection mapping
        session_id = manager.session_id_mapping.get(connection_id)
        if not session_id:
            await manager.send_message(connection_id, {
                "type": "error",
                "data": {"message": "Session not found. Please start a new session."}
            })
            return
        
        # Validate input data
        if not isinstance(data, dict):
            await manager.send_message(connection_id, {
                "type": "error",
                "data": {"message": "Invalid data format received"}
            })
            return
            
        message = data.get("data", {}).get("message", "")
        
        if not message or not message.strip():
            await manager.send_message(connection_id, {
                "type": "error",
                "data": {"message": "Message is required and cannot be empty"}
            })
            return
        
        # Get session using session manager
        interviewer = session_manager.get_session(session_id)
        if not interviewer:
            await manager.send_message(connection_id, {
                "type": "error",
                "data": {"message": "Session not found"}
            })
            return
        
        logger.info(f"Processing message for session {session_id}: {len(message)} characters")
        
        # Send typing indicator
        await manager.send_message(connection_id, {
            "type": "bot_typing",
            "data": {"session_id": session_id}
        })
        
        # Process message based on current stage
        if interviewer.stage == "greeting":
            response = await interviewer.process_greeting(message)
            await manager.send_message(connection_id, {
                "type": "next_question",
                "data": {
                    "session_id": session_id,
                    "question": {
                        "id": interviewer.current_question['id'],
                        "question": interviewer.current_question['question'],
                        "difficulty": interviewer.current_question['difficulty'],
                        "key_concepts": interviewer.current_question['key_concepts']
                    }
                }
            })
        elif interviewer.stage == "questioning":
            await process_answer_with_events(connection_id, session_id, interviewer, message)
        elif interviewer.stage == "following_up":
            await process_followup_with_events(connection_id, session_id, interviewer, message)
        
        # Save session state
        session_manager.save_session(session_id)
        
    except Exception as e:
        logger.error(f"Failed to process user message: {e}")
        await manager.send_message(connection_id, {
            "type": "error",
            "data": {"message": f"Failed to process message: {str(e)}"}
        })

async def process_answer_with_events(connection_id: str, session_id: str, interviewer: LLMPoweredInterviewer, message: str):
    """Process answer with real-time WebSocket events"""
    logger.info(f"Processing answer for session {session_id}: {message[:50]}...")
    current_q = interviewer.current_question
    
    analysis = await interviewer.analyze_answer_with_llm(
        current_q['question'], 
        message, 
        current_q['key_concepts']
    )
    
    logger.info(f"Emitting analysis for session {session_id}, score: {analysis['score']}")
    await manager.send_message(connection_id, {
        "type": "analysis",
        "data": {
            "session_id": session_id,
            "analysis": analysis
        }
    })
    
    feedback = await interviewer.generate_feedback_with_llm(
        current_q['question'],
        message,
        analysis['raw_analysis'],
        analysis['score'],
        interviewer.current_question_idx
    )
    
    logger.info(f"Emitting feedback for session {session_id}")
    await manager.send_message(connection_id, {
        "type": "feedback",
        "data": {
            "session_id": session_id,
            "feedback": feedback
        }
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
        await manager.send_message(connection_id, {
            "type": "followup_question",
            "data": {
                "session_id": session_id,
                "question": {
                    "id": current_q['id'],
                    "question": followup_q
                }
            }
        })
        
        interviewer.conversation_history.append({"role": "assistant", "content": followup_q})
    else:
        interviewer.current_followup_count = 0
        logger.info(f"Good score ({analysis['score']}) - moving to next question")
        # Give frontend time to display analysis before moving to next question
        await asyncio.sleep(3)
        await move_to_next_question(connection_id, session_id, interviewer)

async def process_followup_with_events(connection_id: str, session_id: str, interviewer: LLMPoweredInterviewer, message: str):
    """Process follow-up answer with real-time WebSocket events"""
    logger.info(f"Processing follow-up for session {session_id}: {message[:50]}...")
    current_q = interviewer.current_question
    
    analysis = await interviewer.analyze_answer_with_llm(
        current_q['follow_ups'][interviewer.current_followup_count - 1],
        message,
        current_q['key_concepts']
    )
    
    await manager.send_message(connection_id, {
        "type": "analysis",
        "data": {
            "session_id": session_id,
            "analysis": analysis
        }
    })
    
    feedback = await interviewer.generate_feedback_with_llm(
        current_q['follow_ups'][interviewer.current_followup_count - 1],
        message,
        analysis['raw_analysis'],
        analysis['score'],
        interviewer.current_question_idx
    )
    
    await manager.send_message(connection_id, {
        "type": "feedback",
        "data": {
            "session_id": session_id,
            "feedback": feedback
        }
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
        await manager.send_message(connection_id, {
            "type": "followup_question",
            "data": {
                "session_id": session_id,
                "question": {
                    "id": current_q['id'],
                    "question": followup_q
                }
            }
        })
        
        interviewer.conversation_history.append({"role": "assistant", "content": followup_q})
    else:
        interviewer.current_followup_count = 0
        logger.info("No follow-up needed, moving to next question")
        # Give frontend time to display analysis before moving to next question
        await asyncio.sleep(3)
        await move_to_next_question(connection_id, session_id, interviewer)

async def move_to_next_question(connection_id: str, session_id: str, interviewer: LLMPoweredInterviewer):
    """Move to the next question or end interview"""
    interviewer.current_question_idx += 1
    interviewer.stage = "questioning"
    interviewer.current_followup_count = 0
    
    if interviewer.current_question_idx >= len(interviewer.questions):
        logger.info(f"Interview completed for session {session_id}")
        summary = await interviewer.end_interview()
        await manager.send_message(connection_id, {
            "type": "interview_summary",
            "data": {
                "session_id": session_id,
                "summary": summary
            }
        })
        return
    
    interviewer.current_question = interviewer.questions[interviewer.current_question_idx]
    interviewer.questions_asked += 1
    
    logger.info(f"Moving to question {interviewer.questions_asked} for session {session_id}")
    await manager.send_message(connection_id, {
        "type": "next_question",
        "data": {
            "session_id": session_id,
            "question": {
                "id": interviewer.current_question['id'],
                "question": interviewer.current_question['question'],
                "difficulty": interviewer.current_question['difficulty'],
                "key_concepts": interviewer.current_question['key_concepts']
            }
        }
    })
