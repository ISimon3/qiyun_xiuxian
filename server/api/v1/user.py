# 用户信息接口

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db
from server.database.crud import UserCRUD, CharacterCRUD
from server.database.models import User
from server.core.dependencies import get_current_user, get_current_active_user
from server.core.character_service import CharacterService
from server.config import settings
from shared.schemas import (
    BaseResponse, UserInfo, CharacterCreate, CharacterInfo
)

router = APIRouter()


@router.get("/me", response_model=BaseResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的详细信息

    需要提供有效的JWT令牌
    """
    try:
        user_info = UserInfo.model_validate(current_user)

        return BaseResponse(
            success=True,
            message="获取用户信息成功",
            data=user_info.model_dump()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.get("/characters", response_model=BaseResponse, summary="获取用户角色列表")
async def get_user_characters(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有角色

    返回角色基本信息列表
    """
    try:
        characters = await CharacterCRUD.get_characters_by_user(db, current_user.id)

        character_list = []
        for char in characters:
            char_info = CharacterService.build_character_info(char)
            character_list.append(char_info.model_dump())

        return BaseResponse(
            success=True,
            message=f"获取角色列表成功，共{len(character_list)}个角色",
            data={
                "characters": character_list,
                "total": len(character_list),
                "max_characters": settings.MAX_CHARACTERS_PER_USER
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
        )


@router.post("/characters", response_model=BaseResponse, summary="创建新角色")
async def create_character(
    character_data: CharacterCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新角色

    - **name**: 角色名称 (2-20字符)
    - **spiritual_root**: 灵根类型

    每个用户最多可创建3个角色
    """
    try:
        # 检查角色数量限制
        existing_characters = await CharacterCRUD.get_characters_by_user(db, current_user.id)
        if len(existing_characters) >= settings.MAX_CHARACTERS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"每个用户最多只能创建{settings.MAX_CHARACTERS_PER_USER}个角色"
            )

        # 检查角色名是否重复（同一用户下）
        for char in existing_characters:
            if char.name == character_data.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色名已存在"
                )

        # 创建角色
        character = await CharacterCRUD.create_character(db, current_user.id, character_data)

        # 构造响应数据
        char_info = CharacterService.build_character_info(character)

        return BaseResponse(
            success=True,
            message="角色创建成功",
            data=char_info.model_dump()
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建角色失败: {str(e)}"
        )


@router.get("/characters/{character_id}", response_model=BaseResponse, summary="获取角色详细信息")
async def get_character_detail(
    character_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定角色的详细信息

    只能获取属于当前用户的角色信息
    """
    try:
        character = await CharacterCRUD.get_character_by_id(db, character_id)

        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 验证角色所有权
        if character.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该角色信息"
            )

        # 构造详细信息
        char_info = CharacterService.build_character_info(character)

        return BaseResponse(
            success=True,
            message="获取角色信息成功",
            data=char_info.model_dump()
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色信息失败: {str(e)}"
        )
