"""
记忆基类定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Message:
    """消息数据类"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata
        }


@dataclass
class ConversationBuffer:
    """对话缓冲区"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    max_messages: int = 20
    max_tokens: int = 4096
    
    def add(self, message: Message):
        """添加消息"""
        self.messages.append(message)
        self._trim()
    
    def _trim(self):
        """修剪超出限制的消息"""
        # 保留system消息
        system_msgs = [m for m in self.messages if m.role == "system"]
        other_msgs = [m for m in self.messages if m.role != "system"]
        
        # 如果超出限制，移除最早的消息
        while len(other_msgs) > self.max_messages:
            other_msgs.pop(0)
        
        self.messages = system_msgs + other_msgs
    
    def get_recent(self, n: int = None) -> List[Message]:
        """获取最近n条消息"""
        if n is None:
            return self.messages.copy()
        return self.messages[-n:]
    
    def to_context_string(self) -> str:
        """转换为上下文字符串"""
        parts = []
        for msg in self.messages:
            if msg.role == "system":
                continue
            role_label = "用户" if msg.role == "user" else "助手"
            parts.append(f"{role_label}：{msg.content}")
        return "\n\n".join(parts)
    
    def clear(self):
        """清空缓冲区"""
        self.messages.clear()
    
    def __len__(self) -> int:
        return len(self.messages)
