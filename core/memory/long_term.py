"""
长期记忆 - 用户画像和历史记录
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_profile import UserProfileService
from db import crud


class LongTermMemory:
    """长期记忆管理器 - 与用户画像和学习记录集成"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_service = UserProfileService()
    
    async def get_user_context(self, db: AsyncSession) -> str:
        """获取用户相关上下文，用于prompt增强"""
        user = await self.user_service.get_profile(db, self.user_id)
        if not user:
            return ""
        
        return self.user_service.get_user_context_prompt(user)
    
    async def get_relevant_history(
        self,
        db: AsyncSession,
        query: str,
        subject: Optional[str] = None,
        k: int = 5
    ) -> List[dict]:
        """检索与当前问题相关的历史记录"""
        # 简单实现：按学科和时间获取最近记录
        # 后续可以加入向量检索
        records = await crud.get_user_learning_records(
            db,
            self.user_id,
            subject=subject,
            limit=k
        )
        
        return [
            {
                "task_type": r.task_type,
                "subject": r.subject,
                "difficulty": r.difficulty,
                "is_correct": r.is_correct,
                "summary": r.question_summary,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in records
        ]
    
    async def store_interaction(
        self,
        db: AsyncSession,
        task_type: str,
        subject: Optional[str] = None,
        difficulty: float = 0.5,
        is_correct: Optional[bool] = None,
        session_id: Optional[str] = None,
        question_summary: Optional[str] = None,
        thinking_mode_used: Optional[str] = None,
        time_spent_seconds: int = 0
    ):
        """存储交互记录"""
        await self.user_service.record_learning(
            db,
            user_id=self.user_id,
            task_type=task_type,
            subject=subject,
            difficulty=difficulty,
            is_correct=is_correct,
            session_id=session_id,
            question_summary=question_summary,
            thinking_mode_used=thinking_mode_used,
            time_spent_seconds=time_spent_seconds
        )
    
    async def get_weak_points(self, db: AsyncSession) -> List[str]:
        """获取用户薄弱点"""
        return []
    
    async def get_skill_level(self, db: AsyncSession, subject: str) -> float:
        """获取学科能力水平"""
        return 50.0
    
    async def suggest_difficulty(
        self, 
        db: AsyncSession,
        subject: Optional[str] = None
    ) -> float:
        """建议题目难度"""
        return await self.user_service.suggest_difficulty(db, self.user_id, subject)
