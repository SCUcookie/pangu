"""
记忆管理器 - 统一管理短期和长期记忆
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory


class MemoryManager:
    """统一记忆管理器"""
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.short_term = ShortTermMemory(session_id)
        self.long_term = LongTermMemory(user_id)
    
    def get_full_context(self, user_profile=None) -> str:
        """获取完整上下文（短期+长期）"""
        parts = []
        
        # 用户画像上下文
        if user_profile:
            user_context = self._build_user_context(user_profile)
            if user_context:
                parts.append(user_context)
        
        # 获取对话历史
        conversation = self.short_term.get_context()
        if conversation:
            parts.append("## 对话历史\n" + conversation)
        
        return "\n\n".join(parts)
    
    def _build_user_context(self, user_profile) -> str:
        """从用户画像构建上下文"""
        lines = ["## 用户信息"]
        
        if user_profile.education_level:
            lines.append(f"- 学制级别: {user_profile.education_level}")
        if user_profile.grade:
            lines.append(f"- 年级: {user_profile.grade}")
        if user_profile.subjects:
            lines.append(f"- 关注学科: {', '.join(user_profile.subjects)}")
        if False:
            lines.append(f"- 薄弱环节: {', '.join(user_profile.weak_points[:3])}")
        if False:
            lines.append(f"- 擅长领域: {', '.join(user_profile.strong_points[:3])}")
        
        return "\n".join(lines) if len(lines) > 1 else ""
    
    async def get_full_context_async(self, db: AsyncSession) -> str:
        """异步获取完整上下文（短期+长期）"""
        # 获取用户画像上下文
        user_context = await self.long_term.get_user_context(db)
        
        # 获取对话历史
        conversation = self.short_term.get_context()
        
        parts = []
        if user_context:
            parts.append(user_context)
        if conversation:
            parts.append("## 对话历史\n" + conversation)
        
        return "\n\n".join(parts)
    
    def add_user_message(self, content: str, **metadata):
        """添加用户消息"""
        return self.short_term.add_user_message(content, **metadata)
    
    def add_assistant_message(self, content: str, **metadata):
        """添加助手消息"""
        return self.short_term.add_assistant_message(content, **metadata)
    
    async def add_turn(
        self,
        db: AsyncSession,
        user_msg: str,
        assistant_msg: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加一轮对话"""
        metadata = metadata or {}
        
        # 添加到短期记忆
        self.short_term.add_user_message(user_msg)
        self.short_term.add_assistant_message(assistant_msg, **metadata)
        
        # 存储到长期记忆
        await self.long_term.store_interaction(
            db,
            task_type=metadata.get("task_type", "question_answering"),
            subject=metadata.get("subject"),
            difficulty=metadata.get("difficulty", 0.5),
            session_id=self.session_id,
            question_summary=user_msg[:100] if len(user_msg) > 100 else user_msg,
            thinking_mode_used=metadata.get("thinking_mode")
        )
    
    def load_history(self, messages: list):
        """加载历史消息"""
        self.short_term.load_from_messages(messages)
    
    def get_conversation_context(self) -> str:
        """获取对话上下文"""
        return self.short_term.get_context()
    
    async def get_user_context(self, db: AsyncSession) -> str:
        """获取用户上下文"""
        return await self.long_term.get_user_context(db)
    
    @property
    def message_count(self) -> int:
        """消息数量"""
        return self.short_term.message_count
