from pydantic import BaseModel
from typing import List, Optional
from fastapi import File, UploadFile


class User(BaseModel):
    id: str
    # username: str
    # email: str


class Message(BaseModel):
    role: User
    content: str


class Conversation(BaseModel):
    id: int
    user: User
    messages: List[Message]


class AIResponseRequest(BaseModel):
    conversation_id: str
    user_response: str
    get_audio_response: bool = False


class TTSRequest(BaseModel):
    text: str


class STTRequest(BaseModel):
    audio_base64: str


class AgentVerdictRequest(BaseModel):
    agent_prompt: str
    user_response: str


class UserAuth(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    phone: Optional[str] = None
    provider: str = "google"


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    user: UserAuth


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int