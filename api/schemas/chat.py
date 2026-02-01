"""
对话相关Schema
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatContext(BaseModel):
    """对话上下文"""
    subject: Optional[str] = None
    education_level: Optional[str] = None
    additional: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """对话请求"""
    user_id: str
    session_id: Optional[str] = None
    message: str
    task_type: Optional[str] = None
    context: Optional[ChatContext] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "session_id": None,
                "message": "1+1等于多少？",
                "task_type": "question_answering",
                "context": {
                    "subject": "数学",
                    "education_level": "小学"
                }
            }
        }


class ChatMetadata(BaseModel):
    """对话元数据"""
    tokens_used: int = 0
    latency_ms: int = 0
    tool_calls: List[str] = []


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message_id: str
    response: str
    thinking_mode: str
    metadata: ChatMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess-456",
                "message_id": "msg-789",
                "response": "1+1等于2。",
                "thinking_mode": "fast",
                "metadata": {
                    "tokens_used": 50,
                    "latency_ms": 200,
                    "tool_calls": []
                }
            }
        }
