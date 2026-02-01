"""
用户画像服务
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from db import crud
from db.models import UserProfile, LearningRecord


class UserProfileService:
    """用户画像服务类"""
    
    async def get_profile(self, db: AsyncSession, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        return await crud.get_user_profile(db, user_id)
    
    async def get_or_create_profile(
        self, 
        db: AsyncSession, 
        user_id: str,
        **defaults
    ) -> tuple[UserProfile, bool]:
        """获取或创建用户画像"""
        return await crud.get_or_create_user_profile(db, user_id, **defaults)
    
    async def create_profile(
        self,
        db: AsyncSession,
        user_id: str,
        name: Optional[str] = None,
        education_level: str = "unknown",
        **kwargs
    ) -> UserProfile:
        """创建用户画像"""
        return await crud.create_user_profile(
            db, user_id, name=name, education_level=education_level, **kwargs
        )
    
    async def update_profile(
        self,
        db: AsyncSession,
        user_id: str,
        **updates
    ) -> Optional[UserProfile]:
        """更新用户画像"""
        return await crud.update_user_profile(db, user_id, **updates)
    
    async def record_learning(
        self,
        db: AsyncSession,
        user_id: str,
        task_type: str,
        session_id: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: float = 0.5,
        is_correct: Optional[bool] = None,
        time_spent_seconds: int = 0,
        thinking_mode_used: Optional[str] = None,
        question_summary: Optional[str] = None
    ) -> LearningRecord:
        """记录学习数据"""
        record = await crud.create_learning_record(
            db,
            user_id=user_id,
            task_type=task_type,
            session_id=session_id,
            subject=subject,
            difficulty=difficulty,
            is_correct=is_correct,
            time_spent_seconds=time_spent_seconds,
            thinking_mode_used=thinking_mode_used,
            question_summary=question_summary
        )
        
        # 更新用户统计
        await self._update_statistics(db, user_id)
        
        return record
    
    async def _update_statistics(self, db: AsyncSession, user_id: str):
        """更新用户统计数据"""
        stats = await crud.get_user_statistics(db, user_id)
        await crud.update_user_profile(
            db,
            user_id,
            total_questions=stats["total_questions"],
            correct_rate=stats["correct_rate"],
            avg_difficulty=stats["avg_difficulty"]
        )
    
    async def increment_stats(self, db: AsyncSession, user_id: str):
        """增加用户问答计数"""
        user = await self.get_profile(db, user_id)
        if user:
            await crud.update_user_profile(
                db,
                user_id,
                total_questions=(user.total_questions or 0) + 1
            )
    
    async def get_skill_level(
        self, 
        db: AsyncSession, 
        user_id: str, 
        subject: str
    ) -> float:
        """获取指定学科的能力水平"""
        user = await self.get_profile(db, user_id)
        if not user or not user.skill_levels:
            return 50.0  # 默认中等水平
        return user.skill_levels.get(subject, 50.0)
    
    async def update_skill_level(
        self,
        db: AsyncSession,
        user_id: str,
        subject: str,
        delta: float
    ) -> float:
        """更新学科能力水平"""
        user = await self.get_profile(db, user_id)
        if not user:
            return 50.0
        
        skill_levels = user.skill_levels or {}
        current = skill_levels.get(subject, 50.0)
        new_level = max(0, min(100, current + delta))
        skill_levels[subject] = new_level
        
        await crud.update_user_profile(db, user_id, skill_levels=skill_levels)
        return new_level
    
    async def get_weak_points(self, db: AsyncSession, user_id: str) -> List[str]:
        """获取薄弱知识点"""
        user = await self.get_profile(db, user_id)
        if not user:
            return []
        return user.weak_points or []
    
    async def add_weak_point(
        self, 
        db: AsyncSession, 
        user_id: str, 
        point: str
    ):
        """添加薄弱知识点"""
        user = await self.get_profile(db, user_id)
        if not user:
            return
        
        weak_points = user.weak_points or []
        if point not in weak_points:
            weak_points.append(point)
            await crud.update_user_profile(db, user_id, weak_points=weak_points)
    
    async def suggest_difficulty(
        self, 
        db: AsyncSession, 
        user_id: str, 
        subject: Optional[str] = None
    ) -> float:
        """建议题目难度"""
        user = await self.get_profile(db, user_id)
        if not user:
            return 0.5  # 默认中等难度
        
        # 基于用户正确率和学科能力调整难度
        base_difficulty = user.avg_difficulty or 0.5
        
        if subject and user.skill_levels:
            skill = user.skill_levels.get(subject, 50)
            # 高能力用户适当提高难度
            skill_factor = (skill - 50) / 100  # -0.5 到 0.5
            base_difficulty += skill_factor * 0.2
        
        # 正确率高则提高难度
        if user.correct_rate > 0.8:
            base_difficulty += 0.1
        elif user.correct_rate < 0.4:
            base_difficulty -= 0.1
        
        return max(0.1, min(0.9, base_difficulty))
    
    def get_user_context_prompt(self, user: UserProfile) -> str:
        """生成用户上下文提示词"""
        if not user:
            return ""
        
        parts = []
        
        if user.education_level and user.education_level != "unknown":
            parts.append(f"学制级别：{user.education_level}")
        if user.grade:
            parts.append(f"年级：{user.grade}")
        if user.strong_points:
            parts.append(f"擅长领域：{', '.join(user.strong_points[:3])}")
        if user.weak_points:
            parts.append(f"薄弱环节：{', '.join(user.weak_points[:3])}")
        if user.skill_levels:
            top_skills = sorted(user.skill_levels.items(), key=lambda x: -x[1])[:3]
            skills_str = ', '.join([f"{k}({v:.0f}分)" for k, v in top_skills])
            parts.append(f"能力评估：{skills_str}")
        
        if parts:
            return "## 用户信息\n" + "\n".join(f"- {p}" for p in parts)
        return ""
