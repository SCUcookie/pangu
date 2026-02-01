"""
用户路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas.user import (
    UserProfileCreate, 
    UserProfileUpdate, 
    UserProfileResponse,
    UserStatisticsResponse
)
from db import crud

router = APIRouter()


@router.post("/user", response_model=UserProfileResponse)
async def create_user(
    request: UserProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新用户"""
    # 检查用户是否已存在
    existing = await crud.get_user_profile(db, request.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user = await crud.create_user_profile(
        db,
        user_id=request.user_id,
        name=request.name,
        education_level=request.education_level,
        grade=request.grade,
        subjects=request.subjects or [],
        preferred_language=request.preferred_language
    )
    
    return UserProfileResponse.model_validate(user, from_attributes=True)


@router.get("/user/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取用户画像"""
    user = await crud.get_user_profile(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse.model_validate(user, from_attributes=True)


@router.put("/user/{user_id}", response_model=UserProfileResponse)
async def update_user(
    user_id: str,
    request: UserProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新用户画像"""
    user = await crud.get_user_profile(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 只更新非None字段
    updates = request.model_dump(exclude_unset=True)
    if updates:
        user = await crud.update_user_profile(db, user_id, **updates)
    
    return UserProfileResponse.model_validate(user, from_attributes=True)


@router.get("/user/{user_id}/statistics", response_model=UserStatisticsResponse)
async def get_user_statistics(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取用户学习统计"""
    user = await crud.get_user_profile(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stats = await crud.get_user_statistics(db, user_id)
    return UserStatisticsResponse(**stats)
