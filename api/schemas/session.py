"""
会话相关Schema
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    session_id: str
    role: str
    content: str
    thinking_mode: Optional[str]
    tokens_used: int
    latency_ms: int
    tool_calls: List[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    user_id: str
    title: Optional[str]
    status: str
    task_type: Optional[str]
    subject: Optional[str]
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionResponse]
    total: int
