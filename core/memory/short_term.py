"""
短期记忆 - 对话历史管理
"""
from typing import List, Optional
from datetime import datetime

from core.memory.base import Message, ConversationBuffer
from config import MEMORY_MAX_MESSAGES, MEMORY_MAX_TOKENS


class ShortTermMemory:
    """短期记忆管理器 - 管理当前会话的对话历史"""
    
    def __init__(
        self, 
        session_id: str,
        max_messages: int = MEMORY_MAX_MESSAGES,
        max_tokens: int = MEMORY_MAX_TOKENS
    ):
        self.session_id = session_id
        self.buffer = ConversationBuffer(
            session_id=session_id,
            max_messages=max_messages,
            max_tokens=max_tokens
        )
    
    def add_message(self, role: str, content: str, **metadata) -> Message:
        """添加消息"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        self.buffer.add(message)
        return message
    
    def add_user_message(self, content: str, **metadata) -> Message:
        """添加用户消息"""
        return self.add_message("user", content, **metadata)
    
    def add_assistant_message(self, content: str, **metadata) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content, **metadata)
    
    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        return self.add_message("system", content)
    
    def get_messages(self, n: Optional[int] = None) -> List[Message]:
        """获取消息列表"""
        return self.buffer.get_recent(n)
    
    def get_context(self) -> str:
        """获取上下文字符串"""
        return self.buffer.to_context_string()
    
    def get_last_user_message(self) -> Optional[Message]:
        """获取最后一条用户消息"""
        for msg in reversed(self.buffer.messages):
            if msg.role == "user":
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """获取最后一条助手消息"""
        for msg in reversed(self.buffer.messages):
            if msg.role == "assistant":
                return msg
        return None
    
    def clear(self):
        """清空记忆"""
        self.buffer.clear()
    
    def load_from_messages(self, messages: list):
        """从消息列表加载"""
        self.buffer.clear()
        for msg in messages:
            if hasattr(msg, 'role'):
                # SessionMessage对象
                self.add_message(msg.role, msg.content)
            elif isinstance(msg, dict):
                self.add_message(msg.get('role', 'user'), msg.get('content', ''))
    
    def add_message_from_db(self, db_message):
        """从数据库消息对象添加"""
        if hasattr(db_message, 'role') and hasattr(db_message, 'content'):
            self.add_message(db_message.role, db_message.content)
    
    @property
    def message_count(self) -> int:
        """消息数量"""
        return len(self.buffer)
    
    def __len__(self) -> int:
        return len(self.buffer)
