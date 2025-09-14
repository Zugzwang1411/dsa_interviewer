import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration class with environment-based settings"""
    
    # Core FastAPI settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    APP_ENV = os.getenv('APP_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
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
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))
    
    @classmethod
    def get_config(cls):
        """Return configuration as dictionary for backward compatibility"""
        return {
            'OPENAI_API_KEY': cls.OPENAI_API_KEY,
            'APP_ENV': cls.APP_ENV,
            'SECRET_KEY': cls.SECRET_KEY,
            'LLM_MODEL': cls.LLM_MODEL,
            'DATABASE_URL': cls.DATABASE_URL,
            'LLM_TEMPERATURE': cls.LLM_TEMPERATURE,
            'MAX_FOLLOWUPS': cls.MAX_FOLLOWUPS,
            'QUESTIONS_PER_SESSION': cls.QUESTIONS_PER_SESSION,
            'SESSION_TIMEOUT': cls.SESSION_TIMEOUT,
            'DEBUG': cls.DEBUG,
            'HOST': cls.HOST,
            'PORT': cls.PORT,
        }

def get_config():
    """Legacy function for backward compatibility"""
    return Config.get_config()
