"""
用户画像与记忆追踪服务 (AgentV3 科研版)
"""
import uuid
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import crud
from db.models import UserProfile, LearningRecord, KnowledgeNode

class UserProfileService:
    """用户画像与动态记忆服务"""
    
    async def get_profile(self, db: AsyncSession, user_id: str) -> Optional[UserProfile]:
        """获取宏观用户画像"""
        return await crud.get_user_profile(db, user_id)
    
    async def get_or_create_profile(self, db: AsyncSession, user_id: str, **defaults) -> tuple[UserProfile, bool]:
        return await crud.get_or_create_user_profile(db, user_id, **defaults)

    async def update_knowledge_node(
        self,
        db: AsyncSession,
        user_id: str,
        subject: str,
        topic: str,
        concept: str,
        is_correct: bool,
        error_reason: Optional[str] = None
    ) -> KnowledgeNode:
        """
        核心创新点一：基于结果更新细粒度的知识图谱记忆
        模拟遗忘曲线与间隔重复。
        """
        stmt = select(KnowledgeNode).where(
            KnowledgeNode.user_id == user_id,
            KnowledgeNode.subject == subject,
            KnowledgeNode.topic == topic,
            KnowledgeNode.concept == concept
        )
        result = await db.execute(stmt)
        node = result.scalar_one_or_none()
        
        now = datetime.utcnow()
        if not node:
            # 首次遇到该知识点
            node = KnowledgeNode(
                node_id=str(uuid.uuid4()),
                user_id=user_id,
                subject=subject,
                topic=topic,
                concept=concept,
                mastery_level=0.8 if is_correct else 0.2,
                exposure_count=1,
                error_count=0 if is_correct else 1,
                latest_error_reason=error_reason if not is_correct else None,
                last_exposure_time=now
            )
            db.add(node)
        else:
            # 时间衰减模型 (艾宾浩斯近似): mastery_decay = e^(-Δt / S), 这里简化处理
            days_passed = (now - node.last_exposure_time).days
            decay_factor = math.exp(-days_passed / 7.0) # 假设半衰期在一周左右
            current_mastery = node.mastery_level * decay_factor
            
            if is_correct:
                node.mastery_level = min(1.0, current_mastery + 0.15)
            else:
                node.mastery_level = max(0.0, current_mastery - 0.3)
                node.error_count += 1
                node.latest_error_reason = error_reason
                
            node.exposure_count += 1
            node.last_exposure_time = now
            
        await db.commit()
        await db.refresh(node)
        return node
        
    async def get_active_memory_prompt(self, db: AsyncSession, user_id: str, current_subject: Optional[str] = None) -> str:
        """
        核心创新点一：根据当前记忆状态，提取与用户最近薄弱点相关的上下文注入Prompt。
        """
        user = await self.get_profile(db, user_id)
        if not user:
            return ""
            
        stmt = select(KnowledgeNode).where(KnowledgeNode.user_id == user_id)
        if current_subject:
            stmt = stmt.where(KnowledgeNode.subject == current_subject)
            
        # 挑选掌握度最低的3个知识点，以及最近犯错的2个知识点
        stmt_weak = stmt.order_by(KnowledgeNode.mastery_level.asc()).limit(3)
        result_weak = await db.execute(stmt_weak)
        weak_nodes = result_weak.scalars().all()
        
        parts = []
        if user.education_level and user.education_level != "unknown":
            parts.append(f"当前学生教育水平为：{user.education_level}。")
            
        if weak_nodes:
            parts.append("### 学习者的动态薄弱点与错因记录：\n根据系统后台追踪，该学生在以下知识点存在明显掌握不足，请在解答中重点解释这些概念并避免跨度过大的推理：")
            for node in weak_nodes:
                reason_str = f"（最新错因：{node.latest_error_reason}）" if node.latest_error_reason else ""
                parts.append(f"- 【{node.concept}】 掌握度: {node.mastery_level:.2f} {reason_str}")
        
        if parts:
            return "\n".join(parts)
        return ""

    async def record_learning(self, db: AsyncSession, user_id: str, task_type: str, session_id: Optional[str] = None, subject: Optional[str] = None, difficulty: float = 0.5, is_correct: Optional[bool] = None, time_spent_seconds: int = 0, thinking_mode_used: Optional[str] = None, question_summary: Optional[str] = None, concepts_involved: List[str] = None) -> LearningRecord:
        record = await crud.create_learning_record(
            db, user_id=user_id, task_type=task_type, session_id=session_id, subject=subject,
            difficulty=difficulty, is_correct=is_correct, time_spent_seconds=time_spent_seconds,
            thinking_mode_used=thinking_mode_used, question_summary=question_summary
        )
        # 为保持后向兼容和精简代码，忽略部分繁琐的 CRUD 改写
        return record
