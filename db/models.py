"""
SQLAlchemy 数据模型定义
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from db.database import Base


class UserProfile(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    user_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=True)
    education_level = Column(String(20), default="unknown")  # 小学/初中/高中/大学
    grade = Column(String(20), nullable=True)
    subjects = Column(JSON, default=list)  # 关注的学科列表
    
    # 能力评估
    skill_levels = Column(JSON, default=dict)  # {"math": 50, "physics": 60, ...}
    weak_points = Column(JSON, default=list)   # 薄弱知识点
    strong_points = Column(JSON, default=list) # 擅长知识点
    
    # 学习偏好
    preferred_thinking_mode = Column(String(10), default="adaptive")  # fast/slow/adaptive
    preferred_language = Column(String(5), default="zh")  # zh/en
    
    # 统计数据
    total_sessions = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    correct_rate = Column(Float, default=0.0)
    avg_difficulty = Column(Float, default=0.5)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    records = relationship("LearningRecord", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, name={self.name})>"


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("user_profiles.user_id"), nullable=False)
    
    title = Column(String(100), nullable=True)  # 会话标题
    status = Column(String(20), default="active")  # active/completed/expired
    task_type = Column(String(50), nullable=True)
    subject = Column(String(50), nullable=True)
    
    # 统计
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("UserProfile", back_populates="sessions")
    messages = relationship("SessionMessage", back_populates="session", 
                          cascade="all, delete-orphan", order_by="SessionMessage.timestamp")
    
    def __repr__(self):
        return f"<Session(session_id={self.session_id}, status={self.status})>"


class SessionMessage(Base):
    """会话消息表"""
    __tablename__ = "session_messages"
    
    message_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id"), nullable=False)
    
    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    
    # 元数据
    thinking_mode = Column(String(10), nullable=True)  # fast/slow/both
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    tool_calls = Column(JSON, default=list)  # 工具调用记录
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="messages")
    
    def __repr__(self):
        return f"<SessionMessage(message_id={self.message_id}, role={self.role})>"


class LearningRecord(Base):
    """学习记录表"""
    __tablename__ = "learning_records"
    
    record_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("user_profiles.user_id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.session_id"), nullable=True)
    
    # 问题信息
    task_type = Column(String(50), nullable=False)
    subject = Column(String(50), nullable=True)
    difficulty = Column(Float, default=0.5)
    question_summary = Column(String(200), nullable=True)
    
    # 结果信息
    is_correct = Column(Boolean, nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    thinking_mode_used = Column(String(10), nullable=True)
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("UserProfile", back_populates="records")
    
    def __repr__(self):
        return f"<LearningRecord(record_id={self.record_id}, task_type={self.task_type})>"
