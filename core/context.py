"""
Agent上下文和决策数据类
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from db.models import Session, UserProfile


@dataclass
class AgentContext:
    """Agent处理上下文"""
    # 请求信息
    user_id: str
    message: str
    task_type: Optional[str] = None
    subject: Optional[str] = None
    education_level: Optional[str] = None
    
    # 会话信息
    session: Optional[Session] = None
    session_id: Optional[str] = None
    
    # 用户信息
    user_profile: Optional[UserProfile] = None
    
    # 上下文信息
    conversation_history: str = ""
    user_context: str = ""
    
    # 元数据
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecision:
    """Agent决策结果"""
    thinking_mode: str  # fast, slow, both
    needs_tools: bool = False
    tool_names: List[str] = field(default_factory=list)
    adjusted_by_profile: bool = False
    reasoning: str = ""


@dataclass
class ExecutionResult:
    """执行结果"""
    response: str
    thinking_mode: str
    tool_results: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    
    # 慢思考的详细过程（如果有）
    slow_thinking: Optional[str] = None
    fast_answer: Optional[str] = None
