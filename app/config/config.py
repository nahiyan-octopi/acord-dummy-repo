"""
Configuration management for Data Extractor API
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""
    
    # OpenAI Configuration (GPT-4-turbo)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0))
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 4096))
    
    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    APP_NAME = "DCN Ai"
    VERSION = "1.0.0"
    
    # PDF Processing Settings
    PDF_DPI = int(os.getenv('PDF_DPI', 300))
    MAX_PAGES = int(os.getenv('MAX_PAGES', 50))
    
    # File Configuration
    BASE_DIR = Path(__file__).parent.parent
    
    # Vercel uses /tmp for writable storage (serverless environment)
    # Check if running on Vercel - check multiple environment variables
    IS_VERCEL = (
        os.getenv('VERCEL') == '1' or 
        os.getenv('VERCEL_ENV') is not None or
        os.getenv('VERCEL_URL') is not None or
        '/var/task' in str(Path(__file__).resolve())  # Vercel's serverless path
    )
    
    if IS_VERCEL:
        UPLOAD_FOLDER = Path('/tmp/uploads')
        OUTPUT_FOLDER = Path('/tmp/output')
    else:
        UPLOAD_FOLDER = BASE_DIR.parent / 'uploads'
        OUTPUT_FOLDER = BASE_DIR.parent / 'output'
    
    # Maximum file size (50MB)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # CORS Configuration
    CORS_ORIGINS = ["*"]  
    
    @classmethod
    def init_app(cls):
        """Initialize application folders"""
        try:
            cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            cls.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # On Vercel, /tmp folders are created on-demand
            # If we can't create them now, they'll be created when needed
            if cls.IS_VERCEL:
                pass  # Expected in serverless - /tmp folders auto-create on first use
            else:
                raise e  # Re-raise if not on Vercel
    
    @classmethod
    def validate_api_key(cls):
        """Validate that OpenAI API key is configured"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        return True
