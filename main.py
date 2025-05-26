from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional, Any
import socketio
import uvicorn
import json
import logging
import os
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv

# Explicitly load environment variables from .env file
load_dotenv(dotenv_path=".env")
print("Loaded ENV variables:", dict(os.environ))  # More readable debugging

# Import config
from config import settings

# Import routers from original application
from routes.health_chat import router as health_chat_router
from routes.risk_assessment import router as risk_assessment_router
from routes.preventive_featured import router as preventive_featured_router
from routes.search import router as search_router
from routes.symptom_checker import router as symptom_checker_router
from routes.health_exploration import router as health_exploration_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add global exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now().isoformat()
        }
    )

# Include routers from original application with explicit tags and prefixes
app.include_router(
    health_chat_router,
    prefix=f"{settings.API_PREFIX}/health-chat",
    tags=["Health Chat"]
)

app.include_router(
    risk_assessment_router,
    prefix=f"{settings.API_PREFIX}/risk-assessment",
    tags=["Risk Assessment"]
)

app.include_router(
    preventive_featured_router,
    prefix=f"{settings.API_PREFIX}/preventive-featured",
    tags=["Preventive Featured"]
)

app.include_router(
    search_router,
    prefix=f"{settings.API_PREFIX}/search",
    tags=["Search"]
)

app.include_router(
    symptom_checker_router,
    prefix=f"{settings.API_PREFIX}/symptom-checker",
    tags=["Symptom Checker"]
)

app.include_router(
    health_exploration_router,
    prefix=f"{settings.API_PREFIX}/health-exploration",
    tags=["Health Exploration"]
)

# Create a Socket.IO instance
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.SOCKETIO_CORS_ORIGINS
)

# Create a Socket.IO app
socket_app = socketio.ASGIApp(sio)

# Mount the Socket.IO app
app.mount("/socket.io", socket_app)

# Global variables to store connected users and chat history
connected_users = {}
chat_history = []

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} - {settings.APP_DESCRIPTION}",
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get(f"{settings.API_PREFIX}/health", tags=["Health Check"])
async def health_check():
    """Enhanced health check with system status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "openai_configured": settings.has_valid_openai_key,
        "cors_origins": settings.CORS_ORIGINS,
        "api_prefix": settings.API_PREFIX
    }

@app.get("/debug/config", tags=["Debug"])
async def debug_config():
    """Debug endpoint to check configuration (remove in production)"""
    return {
        "frontend_url": settings.FRONTEND_URL,
        "cors_origins": settings.CORS_ORIGINS,
        "has_openai_key": settings.has_valid_openai_key,
        "api_prefix": settings.API_PREFIX,
        "port": settings.PORT,
        "host": settings.HOST
    }

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    connected_users[sid] = {"connected_at": datetime.now().isoformat()}
    await sio.emit('user_count', len(connected_users))

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    if sid in connected_users:
        del connected_users[sid]
    await sio.emit('user_count', len(connected_users))

@sio.event
async def chat_message(sid, data):
    logger.info(f"Message from {sid}: {data}")
    user = connected_users.get(sid, {}).get("username", "Anonymous")
    message = {
        "user": user,
        "message": data.get("message", ""),
        "timestamp": datetime.now().isoformat()
    }
    chat_history.append(message)
    await sio.emit('chat_message', message)

@sio.event
async def set_username(sid, data):
    username = data.get("username", "Anonymous")
    if sid in connected_users:
        connected_users[sid]["username"] = username
    logger.info(f"User {sid} set username to {username}")
    await sio.emit('user_joined', {"username": username})

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"OpenAI API configured: {settings.has_valid_openai_key}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
