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
    BaseResponse, UserInfo, CharacterInfo
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


@router.get("/character", response_model=BaseResponse, summary="获取用户角色")
async def get_user_character(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的角色信息

    如果角色不存在，会自动创建一个新角色
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 简化角色信息构建，避免复杂的装备处理
        from shared.utils import calculate_base_attributes
        base_attributes = calculate_base_attributes(character.cultivation_realm)

        # 构建简单的角色信息
        char_data = {
            "id": character.id,
            "name": character.name,
            "cultivation_exp": character.cultivation_exp,
            "cultivation_realm": character.cultivation_realm,
            "spiritual_root": character.spiritual_root,
            "luck_value": character.luck_value,
            "gold": character.gold,
            "spirit_stone": character.spirit_stone,
            "created_at": character.created_at.isoformat(),
            "last_active": character.last_active.isoformat() if character.last_active else None,
            "cultivation_focus": character.cultivation_focus,
            "attributes": {
                "hp": base_attributes.hp + character.hp_training,
                "physical_attack": base_attributes.physical_attack + character.physical_attack_training,
                "magic_attack": base_attributes.magic_attack + character.magic_attack_training,
                "physical_defense": base_attributes.physical_defense + character.physical_defense_training,
                "magic_defense": base_attributes.magic_defense + character.magic_defense_training,
                "critical_rate": base_attributes.critical_rate,
                "critical_damage": base_attributes.critical_damage,
                "cultivation_speed": base_attributes.cultivation_speed,
                "luck_bonus": base_attributes.luck_bonus
            },
            "training_attributes": {
                "hp_training": character.hp_training,
                "physical_attack_training": character.physical_attack_training,
                "magic_attack_training": character.magic_attack_training,
                "physical_defense_training": character.physical_defense_training,
                "magic_defense_training": character.magic_defense_training
            },
            "equipment": None
        }

        return BaseResponse(
            success=True,
            message="获取角色信息成功",
            data=char_data
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色信息失败: {str(e)}"
        )


# 移除角色创建接口 - 每个用户只有一个角色，自动创建


@router.get("/character/detail", response_model=BaseResponse, summary="获取角色详细信息")
async def get_character_detail(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户角色的详细信息（包含装备加成）
    """
    try:
        # 获取或创建角色（包含装备信息）
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取角色装备
        from server.database.crud import EquipmentCRUD
        equipped_items = await EquipmentCRUD.get_character_equipment(db, character.id)

        # 计算完整属性（包含装备加成）
        from shared.utils import calculate_base_attributes, calculate_final_attributes
        from shared.schemas import CharacterTrainingAttributes, EquipmentAttributes

        base_attributes = calculate_base_attributes(character.cultivation_realm)

        training_attributes = CharacterTrainingAttributes(
            hp_training=character.hp_training,
            physical_attack_training=character.physical_attack_training,
            magic_attack_training=character.magic_attack_training,
            physical_defense_training=character.physical_defense_training,
            magic_defense_training=character.magic_defense_training
        )

        # 收集装备属性加成
        equipment_bonuses = []
        for equipped_item in equipped_items:
            if equipped_item.actual_attributes:
                # 将装备的实际属性转换为EquipmentAttributes对象
                equipment_attrs = EquipmentAttributes(**equipped_item.actual_attributes)
                equipment_bonuses.append(equipment_attrs)

        # 计算最终属性
        final_attributes = calculate_final_attributes(base_attributes, training_attributes, equipment_bonuses)

        char_data = {
            "id": character.id,
            "name": character.name,
            "cultivation_exp": character.cultivation_exp,
            "cultivation_realm": character.cultivation_realm,
            "spiritual_root": character.spiritual_root,
            "luck_value": character.luck_value,
            "gold": character.gold,
            "spirit_stone": character.spirit_stone,
            "created_at": character.created_at.isoformat(),
            "last_active": character.last_active.isoformat() if character.last_active else None,
            "cultivation_focus": character.cultivation_focus,
            "attributes": {
                "hp": final_attributes.hp,
                "physical_attack": final_attributes.physical_attack,
                "magic_attack": final_attributes.magic_attack,
                "physical_defense": final_attributes.physical_defense,
                "magic_defense": final_attributes.magic_defense,
                "critical_rate": final_attributes.critical_rate,
                "critical_damage": final_attributes.critical_damage,
                "cultivation_speed": final_attributes.cultivation_speed,
                "luck_bonus": final_attributes.luck_bonus
            },
            "training_attributes": {
                "hp_training": character.hp_training,
                "physical_attack_training": character.physical_attack_training,
                "magic_attack_training": character.magic_attack_training,
                "physical_defense_training": character.physical_defense_training,
                "magic_defense_training": character.magic_defense_training
            },
            "equipment_count": len(equipped_items)  # 装备数量
        }

        return BaseResponse(
            success=True,
            message="获取角色详细信息成功",
            data=char_data
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详细信息失败: {str(e)}"
        )
