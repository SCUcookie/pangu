"""
数据库连接和会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from config import DATABASE_URL, DATABASE_ECHO

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=DATABASE_ECHO,
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from db import models  # noqa
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 数据库初始化完成")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
