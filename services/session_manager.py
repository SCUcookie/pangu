"""
会话管理服务
"""
import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from db import crud
from db.models import Session, SessionMessage
from config import SESSION_EXPIRE_HOURS, SESSION_TITLE_MAX_LENGTH


class SessionManager:
    """会话管理服务类"""
    
    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        task_type: Optional[str] = None,
        subject: Optional[str] = None,
        title: Optional[str] = None
    ) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        session = await crud.create_session(
            db,
            user_id=user_id,
            session_id=session_id,
            task_type=task_type,
            subject=subject,
            title=title
        )
        
        return session
    
    async def get_session(self, db: AsyncSession, session_id: str) -> Optional[Session]:
        """获取会话"""
        return await crud.get_session(db, session_id)
    
    async def get_or_create_session(
        self,
        db: AsyncSession,
        user_id: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> tuple[Session, bool]:
        """获取或创建会话"""
        if session_id:
            session = await self.get_session(db, session_id)
            if session:
                return session, False
        
        session = await self.create_session(db, user_id, **kwargs)
        return session, True
    
    async def close_session(self, db: AsyncSession, session_id: str) -> Optional[Session]:
        """关闭会话"""
        return await crud.update_session(db, session_id, status="completed")
    
    async def get_user_sessions(
        self,
        db: AsyncSession,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Session]:
        """获取用户的会话列表"""
        return await crud.get_user_sessions(db, user_id, status=status, limit=limit)
    
    async def add_message(
        self,
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        thinking_mode: Optional[str] = None,
        tokens_used: int = 0,
        latency_ms: int = 0,
        tool_calls: Optional[List[str]] = None
    ) -> SessionMessage:
        """添加消息到会话"""
        message_id = str(uuid.uuid4())
        
        message = await crud.create_message(
            db,
            session_id=session_id,
            role=role,
            content=content,
            message_id=message_id,
            thinking_mode=thinking_mode,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            tool_calls=tool_calls or []
        )
        
        # 如果是第一条用户消息，生成会话标题
        session = await self.get_session(db, session_id)
        if session and not session.title and role == "user":
            title = self._generate_title(content)
            await crud.update_session(db, session_id, title=title)
        
        return message
    
    async def get_messages(
        self,
        db: AsyncSession,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[SessionMessage]:
        """获取会话消息"""
        return await crud.get_session_messages(db, session_id, limit=limit)
    
    async def get_conversation_context(
        self,
        db: AsyncSession,
        session_id: str,
        max_messages: int = 20
    ) -> str:
        """获取对话上下文字符串"""
        messages = await self.get_messages(db, session_id, limit=max_messages)
        
        if not messages:
            return ""
        
        context_parts = []
        for msg in messages:
            role_label = "用户" if msg.role == "user" else "助手"
            context_parts.append(f"{role_label}：{msg.content}")
        
        return "\n\n".join(context_parts)
    
    def _generate_title(self, first_message: str) -> str:
        """根据第一条消息生成会话标题"""
        # 简单截取，后续可以用LLM生成更好的标题
        title = first_message.strip()
        
        # 移除换行
        title = title.replace("\n", " ")
        
        # 截断
        if len(title) > SESSION_TITLE_MAX_LENGTH:
            title = title[:SESSION_TITLE_MAX_LENGTH - 3] + "..."
        
        return title
    
    async def update_title(self, db: AsyncSession, session_id: str, title: str) -> Optional[Session]:
        """更新会话标题"""
        truncated_title = self._generate_title(title)
        return await crud.update_session(db, session_id, title=truncated_title)
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """清理过期会话"""
        threshold = datetime.utcnow() - timedelta(hours=SESSION_EXPIRE_HOURS)
        
        from sqlalchemy import update as sql_update
        from db.models import Session as SessionModel
        
        result = await db.execute(
            sql_update(SessionModel)
            .where(SessionModel.updated_at < threshold)
            .where(SessionModel.status == "active")
            .values(status="expired")
        )
        
        return result.rowcount
    
    async def restore_session(
        self,
        db: AsyncSession,
        session_id: str
    ) -> Optional[dict]:
        """恢复会话状态"""
        session = await self.get_session(db, session_id)
        if not session:
            return None
        
        messages = await self.get_messages(db, session_id)
        context = await self.get_conversation_context(db, session_id)
        
        return {
            "session": session,
            "messages": messages,
            "context": context
        }
