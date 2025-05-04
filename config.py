import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, List, Any

class Settings(BaseSettings):
    """Application settings"""
    # Base settings
    APP_NAME: str = "پیشگامان سلامت API"
    APP_DESCRIPTION: str = "راهکارهای پیشگیری و سلامت جامع - Backend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_PREFIX: str = "/api"
    
    # CORS settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://www.wellnesssentinel.ir")
    CORS_ORIGINS: List[str] = ["*", "http://localhost:3000"]  # Will include FRONTEND_URL in application
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Socket.IO settings
    SOCKETIO_CORS_ORIGINS: List[str] = ["*"]  # For production, use specific origins
    
    # Database settings (for future implementation)
    DATABASE_URL: Optional[str] = None
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"

    # Add these to allow extra variables
    OPENAI_API_KEY: Optional[str] = None  # Add this
    HTTP_PROXY: Optional[str] = None     # Add this
    HTTPS_PROXY: Optional[str] = None    # Add this

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow" # or "ignore" , decide what to do with extra variables, allow raises warnings, ignore does nothing

# Create settings instance
settings = Settings()
