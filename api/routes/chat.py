"""
对话路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas.chat import ChatRequest, ChatResponse
from core.agent import get_agent_core

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息并获取Agent回复
    """
    try:
        agent = get_agent_core()
        response = await agent.process(request, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    流式对话接口 (TODO: 实现SSE)
    """
    # 暂时返回普通响应，后续实现SSE
    return await chat(request, db)
