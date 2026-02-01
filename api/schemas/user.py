"""
用户相关Schema
"""
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel


class UserProfileCreate(BaseModel):
    """创建用户请求"""
    user_id: str
    name: Optional[str] = None
    education_level: str = "unknown"
    grade: Optional[str] = None
    subjects: Optional[List[str]] = None
    preferred_language: str = "zh"


class UserProfileUpdate(BaseModel):
    """更新用户请求"""
    name: Optional[str] = None
    education_level: Optional[str] = None
    grade: Optional[str] = None
    subjects: Optional[List[str]] = None
    skill_levels: Optional[Dict[str, float]] = None
    weak_points: Optional[List[str]] = None
    strong_points: Optional[List[str]] = None
    preferred_thinking_mode: Optional[str] = None
    preferred_language: Optional[str] = None


class UserProfileResponse(BaseModel):
    """用户画像响应"""
    user_id: str
    name: Optional[str]
    education_level: str
    grade: Optional[str]
    subjects: List[str]
    skill_levels: Dict[str, float]
    weak_points: List[str]
    strong_points: List[str]
    preferred_thinking_mode: str
    preferred_language: str
    total_sessions: int
    total_questions: int
    correct_rate: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserStatisticsResponse(BaseModel):
    """用户统计响应"""
    total_questions: int
    correct_count: int
    correct_rate: float
    avg_difficulty: float
