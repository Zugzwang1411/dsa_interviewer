from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'dev-secret-key')
    
    CORS(app, cors_allowed_origins="*")
    socketio = SocketIO(app, 
                       cors_allowed_origins="*", 
                       async_mode='eventlet',
                       transports=['websocket', 'polling'],
                       allow_upgrades=True)
    
    # Root route
    @app.route('/')
    def root():
        return jsonify({
            "message": "DSA Interviewer Backend API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "start_session": "POST /api/session/start",
                "send_message": "POST /api/session/<session_id>/message",
                "get_state": "GET /api/session/<session_id>/state",
                "end_session": "POST /api/session/<session_id>/end",
                "export_session": "GET /api/session/<session_id>/export"
            },
            "frontend_url": "http://13.203.226.83:3000",
            "chainlit_url": "http://13.203.226.83:8001"
        })
    
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    from . import socket_handlers
    socket_handlers.init_socketio(socketio)
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)
