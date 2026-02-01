"""
依赖注入
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Agent核心实例 (延迟导入避免循环依赖)
_agent_core = None

async def get_agent():
    """获取Agent核心实例"""
    global _agent_core
    if _agent_core is None:
        from core.agent import AgentCore
        _agent_core = AgentCore()
    return _agent_core
