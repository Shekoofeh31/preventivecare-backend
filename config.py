import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings"""
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )
    
    # Base settings
    APP_NAME: str = "پیشگامان سلامت API"
    APP_DESCRIPTION: str = "راهکارهای پیشگیری و سلامت جامع - Backend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_PREFIX: str = "/api"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS settings
    FRONTEND_URL: str = "https://www.wellnesssentinel.ir"
    CORS_ORIGINS: List[str] = [
        "*",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://www.wellnesssentinel.ir"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Socket.IO settings
    SOCKETIO_CORS_ORIGINS: List[str] = ["*"]
    
    # Database settings (for future implementation)
    DATABASE_URL: Optional[str] = None
    
    # Proxy settings
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load environment variables explicitly
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.wellnesssentinel.ir")
        self.PORT = int(os.getenv("PORT", 8000))
        
        # Validate critical settings
        self.validate_settings()
    
    def validate_settings(self):
        """Validate critical configuration"""
        if not self.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        elif not self.OPENAI_API_KEY.startswith('sk-'):
            logger.warning("OPENAI_API_KEY format appears invalid")
        
        # Add FRONTEND_URL to CORS_ORIGINS if not already there
        if self.FRONTEND_URL not in self.CORS_ORIGINS and self.FRONTEND_URL != "*":
            self.CORS_ORIGINS.append(self.FRONTEND_URL)
    
    @property
    def has_valid_openai_key(self) -> bool:
        """Check if OpenAI key is present and formatted correctly"""
        return (
            self.OPENAI_API_KEY and 
            self.OPENAI_API_KEY.startswith('sk-') and 
            len(self.OPENAI_API_KEY) > 20
        )

# Create settings instance
settings = Settings()
