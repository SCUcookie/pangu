"""
数据库 CRUD 操作
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserProfile, Session, SessionMessage, LearningRecord


# ============================================================
# UserProfile CRUD
# ============================================================

async def create_user_profile(
    db: AsyncSession,
    user_id: str,
    name: Optional[str] = None,
    education_level: str = "unknown",
    **kwargs
) -> UserProfile:
    """创建用户画像"""
    user = UserProfile(
        user_id=user_id,
        name=name,
        education_level=education_level,
        **kwargs
    )
    db.add(user)
    await db.flush()
    return user


async def get_user_profile(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
    """获取用户画像"""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_user_profile(
    db: AsyncSession, 
    user_id: str,
    **defaults
) -> tuple[UserProfile, bool]:
    """获取或创建用户画像，返回(user, created)"""
    user = await get_user_profile(db, user_id)
    if user:
        return user, False
    user = await create_user_profile(db, user_id, **defaults)
    return user, True


async def update_user_profile(
    db: AsyncSession,
    user_id: str,
    **updates
) -> Optional[UserProfile]:
    """更新用户画像"""
    updates["updated_at"] = datetime.utcnow()
    await db.execute(
        update(UserProfile)
        .where(UserProfile.user_id == user_id)
        .values(**updates)
    )
    return await get_user_profile(db, user_id)


# ============================================================
# Session CRUD
# ============================================================

async def create_session(
    db: AsyncSession,
    user_id: str,
    session_id: Optional[str] = None,
    **kwargs
) -> Session:
    """创建会话"""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    session = Session(
        session_id=session_id,
        user_id=user_id,
        **kwargs
    )
    db.add(session)
    await db.flush()
    return session


async def get_session(db: AsyncSession, session_id: str) -> Optional[Session]:
    """获取会话"""
    result = await db.execute(
        select(Session).where(Session.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def get_user_sessions(
    db: AsyncSession,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Session]:
    """获取用户的会话列表"""
    query = select(Session).where(Session.user_id == user_id)
    if status:
        query = query.where(Session.status == status)
    query = query.order_by(Session.updated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_session(
    db: AsyncSession,
    session_id: str,
    **updates
) -> Optional[Session]:
    """更新会话"""
    updates["updated_at"] = datetime.utcnow()
    await db.execute(
        update(Session)
        .where(Session.session_id == session_id)
        .values(**updates)
    )
    return await get_session(db, session_id)


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    """删除会话"""
    result = await db.execute(
        delete(Session).where(Session.session_id == session_id)
    )
    return result.rowcount > 0


# ============================================================
# SessionMessage CRUD
# ============================================================

async def create_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None,
    **kwargs
) -> SessionMessage:
    """创建消息"""
    if message_id is None:
        message_id = str(uuid.uuid4())
    
    message = SessionMessage(
        message_id=message_id,
        session_id=session_id,
        role=role,
        content=content,
        **kwargs
    )
    db.add(message)
    await db.flush()
    
    # 更新会话消息计数
    await db.execute(
        update(Session)
        .where(Session.session_id == session_id)
        .values(
            message_count=Session.message_count + 1,
            updated_at=datetime.utcnow()
        )
    )
    
    return message


async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    limit: Optional[int] = None
) -> List[SessionMessage]:
    """获取会话的消息列表"""
    query = (
        select(SessionMessage)
        .where(SessionMessage.session_id == session_id)
        .order_by(SessionMessage.timestamp.asc())
    )
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


# ============================================================
# LearningRecord CRUD
# ============================================================

async def create_learning_record(
    db: AsyncSession,
    user_id: str,
    task_type: str,
    record_id: Optional[str] = None,
    **kwargs
) -> LearningRecord:
    """创建学习记录"""
    if record_id is None:
        record_id = str(uuid.uuid4())
    
    record = LearningRecord(
        record_id=record_id,
        user_id=user_id,
        task_type=task_type,
        **kwargs
    )
    db.add(record)
    await db.flush()
    return record


async def get_user_learning_records(
    db: AsyncSession,
    user_id: str,
    task_type: Optional[str] = None,
    subject: Optional[str] = None,
    limit: int = 50
) -> List[LearningRecord]:
    """获取用户的学习记录"""
    query = select(LearningRecord).where(LearningRecord.user_id == user_id)
    
    if task_type:
        query = query.where(LearningRecord.task_type == task_type)
    if subject:
        query = query.where(LearningRecord.subject == subject)
    
    query = query.order_by(LearningRecord.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_statistics(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """获取用户统计数据"""
    records = await get_user_learning_records(db, user_id, limit=1000)
    
    if not records:
        return {
            "total_questions": 0,
            "correct_count": 0,
            "correct_rate": 0.0,
            "avg_difficulty": 0.5
        }
    
    total = len(records)
    correct = sum(1 for r in records if r.is_correct is True)
    avg_diff = sum(r.difficulty for r in records) / total
    
    return {
        "total_questions": total,
        "correct_count": correct,
        "correct_rate": correct / total if total > 0 else 0.0,
        "avg_difficulty": avg_diff
    }
