"""
会话路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas.session import (
    SessionResponse,
    SessionListResponse,
    MessageResponse
)
from db import crud

router = APIRouter()


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情"""
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse.model_validate(session, from_attributes=True)


@router.get("/session/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息历史"""
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await crud.get_session_messages(db, session_id, limit=limit)
    return [MessageResponse.model_validate(m, from_attributes=True) for m in messages]


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除会话"""
    success = await crud.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted"}


@router.get("/sessions/user/{user_id}", response_model=SessionListResponse)
async def get_user_sessions(
    user_id: str,
    limit: int = 10,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取用户的会话列表"""
    sessions = await crud.get_user_sessions(db, user_id, status=status, limit=limit)
    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s, from_attributes=True) for s in sessions],
        total=len(sessions)
    )
