from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import json
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Models
class User(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Message(BaseModel):
    sender: str
    content: str
    timestamp: Optional[str] = None

# Fixed ChatRoom model with explicit examples
class ChatRoom(BaseModel):
    room_id: str = Field(..., example="room1")
    name: str = Field(..., example="General Discussion")
    description: Optional[str] = Field(None, example="A room for general health discussion")
    
    class Config:
        schema_extra = {
            "example": {
                "room_id": "room1",
                "name": "General Discussion",
                "description": "A room for general health discussion"
            }
        }

# Mock database (in-memory storage)
users_db = {}
active_sessions = {}
chat_rooms = {}
chat_messages = {}

# Authentication endpoints
@router.post("/register")
async def register_user(user: User):
    """Register a new user for health chat."""
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # In a real app, you would hash the password
    users_db[user.email] = {
        "username": user.username,
        "password": user.password,  # Should be hashed in production
        "created_at": datetime.now().isoformat()
    }
    
    return {"message": "User registered successfully", "username": user.username}

@router.post("/login")
async def login_user(user_login: UserLogin):
    """Log in a user to the health chat."""
    if user_login.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    stored_user = users_db[user_login.email]
    if stored_user["password"] != user_login.password:  # Should use secure comparison in production
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create a session (in a real app, use JWT or other secure token method)
    session_id = f"session_{len(active_sessions) + 1}"
    active_sessions[session_id] = {
        "email": user_login.email,
        "username": stored_user["username"],
        "logged_in_at": datetime.now().isoformat()
    }
    
    return {
        "message": "Login successful",
        "session_id": session_id,
        "username": stored_user["username"]
    }

@router.post("/logout")
async def logout_user(session_id: str):
    """Log out a user from the health chat."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove the session
    username = active_sessions[session_id]["username"]
    del active_sessions[session_id]
    
    return {"message": f"User {username} logged out successfully"}

# Chat room endpoints
@router.post("/rooms", response_model=dict)
async def create_chat_room(room: ChatRoom):
    """Create a new chat room."""
    if room.room_id in chat_rooms:
        raise HTTPException(status_code=400, detail="Room ID already exists")
    
    # Create room data to store
    room_data = {
        "name": room.name,
        "description": room.description,
        "created_at": datetime.now().isoformat()
    }
    
    # Store in chat_rooms dictionary
    chat_rooms[room.room_id] = room_data
    
    # Initialize an empty list for this room's messages
    chat_messages[room.room_id] = []
    
    # Return structured response matching the expected format
    return {
        "message": "Chat room created", 
        "room": {
            "room_id": room.room_id,
            "name": room.name,
            "description": room.description
        }
    }

@router.get("/rooms")
async def list_chat_rooms():
    """List all available chat rooms."""
    return {"rooms": [{"room_id": k, **v} for k, v in chat_rooms.items()]}

@router.get("/rooms/{room_id}")
async def get_chat_room(room_id: str):
    """Get details about a specific chat room."""
    if room_id not in chat_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {"room_id": room_id, **chat_rooms[room_id]}

@router.get("/rooms/{room_id}/messages")
async def get_chat_messages(room_id: str, limit: int = 50):
    """Get messages from a specific chat room."""
    if room_id not in chat_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Return the most recent messages (up to the limit)
    messages = chat_messages.get(room_id, [])
    return {"room_id": room_id, "messages": messages[-limit:]}

@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: str, message: Message):
    """Send a message to a specific chat room."""
    if room_id not in chat_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Add timestamp if not provided
    if not message.timestamp:
        message.timestamp = datetime.now().isoformat()
    
    # Add the message to the room
    if room_id not in chat_messages:
        chat_messages[room_id] = []
    
    chat_messages[room_id].append(message.dict())
    
    return {"message": "Message sent", "room_id": room_id}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time chat in a specific room."""
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the message
            try:
                message_data = json.loads(data)
                message = Message(
                    sender=message_data.get("sender", "Anonymous"),
                    content=message_data.get("content", ""),
                    timestamp=datetime.now().isoformat()
                )
                
                # Save the message
                if room_id not in chat_messages:
                    chat_messages[room_id] = []
                chat_messages[room_id].append(message.dict())
                
                # Broadcast the message to all clients in the room
                await manager.broadcast(json.dumps(message.dict()), room_id)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({"error": "Invalid message format"}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(
            json.dumps({
                "sender": "system",
                "content": "A user has left the chat",
                "timestamp": datetime.now().isoformat()
            }),
            room_id
        )
