import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration class with environment-based settings"""
    
    # Core Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///dsa_interviewer.db')
    
    # LLM Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.4'))
    MAX_FOLLOWUPS = int(os.getenv('MAX_FOLLOWUPS', '2'))
    
    # Interview settings
    QUESTIONS_PER_SESSION = int(os.getenv('QUESTIONS_PER_SESSION', '5'))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '1800'))  # 30 minutes
    
    # WebSocket settings
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def get_config(cls):
        """Return configuration as dictionary for backward compatibility"""
        return {
            'OPENAI_API_KEY': cls.OPENAI_API_KEY,
            'FLASK_ENV': cls.FLASK_ENV,
            'FLASK_SECRET': cls.SECRET_KEY,
            'LLM_MODEL': cls.LLM_MODEL,
            'DATABASE_URL': cls.DATABASE_URL,
            'LLM_TEMPERATURE': cls.LLM_TEMPERATURE,
            'MAX_FOLLOWUPS': cls.MAX_FOLLOWUPS,
            'QUESTIONS_PER_SESSION': cls.QUESTIONS_PER_SESSION,
            'SESSION_TIMEOUT': cls.SESSION_TIMEOUT,
        }

def get_config():
    """Legacy function for backward compatibility"""
    return Config.get_config()
