import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
        'FLASK_SECRET': os.getenv('FLASK_SECRET', 'dev-secret-key'),
        'LLM_MODEL': os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
    }
