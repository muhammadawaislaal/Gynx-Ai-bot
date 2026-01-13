import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Flask application"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'wixen-secret-key-2026')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Groq API settings
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # LLM settings
    DEFAULT_MODEL = "llama-3.1-8b-instant"
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
        return True
