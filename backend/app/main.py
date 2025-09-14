from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .config import Config
from .routes import router as api_router
from .websocket_handlers import websocket_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = Config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting DSA Interviewer FastAPI application")
    yield
    # Shutdown
    logger.info("Shutting down DSA Interviewer FastAPI application")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="DSA Interviewer API",
        description="AI-powered Data Structures & Algorithms Interview Platform",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/", response_model=dict)
    async def root():
        return {
            "message": "DSA Interviewer Backend API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "start_session": "POST /api/session/start",
                "send_message": "POST /api/session/{session_id}/message",
                "get_state": "GET /api/session/{session_id}/state",
                "end_session": "POST /api/session/{session_id}/end",
                "export_session": "GET /api/session/{session_id}/export"
            },
            "frontend_url": "http://13.203.226.83:3000",
            "chainlit_url": "http://13.203.226.83:8001"
        }
    
    # Include routers
    app.include_router(api_router, prefix="/api")
    app.include_router(websocket_router)
    
    return app

# Create the FastAPI application
app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
