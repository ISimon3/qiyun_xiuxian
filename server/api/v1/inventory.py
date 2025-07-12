# 背包和装备管理接口

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db
from server.database.crud import CharacterCRUD, InventoryCRUD, EquipmentCRUD, ItemCRUD
from server.database.models import User
from server.core.dependencies import get_current_active_user
from server.core.character_service import CharacterService
from shared.schemas import (
    BaseResponse, InventoryItem, EquipItem, UnequipItem, ItemInfo
)

router = APIRouter()


@router.get("/inventory", response_model=BaseResponse, summary="获取角色背包")
async def get_character_inventory(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户角色的背包物品列表
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取背包物品
        inventory_items = await InventoryCRUD.get_character_inventory(db, character.id)
        
        # 构建响应数据
        items_data = []
        for inv_item in inventory_items:
            if inv_item.item:
                item_info = ItemInfo.model_validate(inv_item.item)
                inventory_item = InventoryItem(
                    item_id=inv_item.item_id,
                    item_info=item_info,
                    quantity=inv_item.quantity,
                    slot_position=inv_item.slot_position
                )
                items_data.append(inventory_item.model_dump())
        
        return BaseResponse(
            success=True,
            message=f"获取背包成功，共{len(items_data)}个物品",
            data={
                "items": items_data,
                "total_items": len(items_data),
                "character_id": character.id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取背包失败: {str(e)}"
        )


@router.get("/equipment", response_model=BaseResponse, summary="获取角色装备")
async def get_character_equipment(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户角色的装备信息

    返回详细的装备属性和加成信息
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 简化装备信息获取，暂时返回空装备
        return BaseResponse(
            success=True,
            message="获取装备信息成功",
            data={
                "character_id": character.id,
                "equipment": None,  # 暂时返回空装备
                "attributes": {
                    "hp": 100,
                    "physical_attack": 20,
                    "magic_attack": 20,
                    "physical_defense": 15,
                    "magic_defense": 15,
                    "critical_rate": 5.0,
                    "critical_damage": 150.0,
                    "cultivation_speed": 1.0,
                    "luck_bonus": 0
                },
                "training_attributes": {
                    "hp_training": character.hp_training,
                    "physical_attack_training": character.physical_attack_training,
                    "magic_attack_training": character.magic_attack_training,
                    "physical_defense_training": character.physical_defense_training,
                    "magic_defense_training": character.magic_defense_training
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取装备信息失败: {str(e)}"
        )


@router.post("/equip", response_model=BaseResponse, summary="装备物品")
async def equip_item(
    equip_data: EquipItem,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为当前用户角色装备物品

    - **item_id**: 要装备的物品ID
    - **slot**: 装备部位 (WEAPON, ARMOR, HELMET, BOOTS, BRACELET, MAGIC_WEAPON)
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)
        
        # 验证物品是否存在且为装备
        item = await ItemCRUD.get_item_by_id(db, equip_data.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物品不存在"
            )
        
        if item.item_type != "EQUIPMENT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该物品不是装备"
            )
        
        if item.equipment_slot != equip_data.slot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="装备部位不匹配"
            )
        
        # 检查境界需求
        if item.required_realm and item.required_realm > character.cultivation_realm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"境界不足，需要{item.required_realm}境界"
            )
        
        # TODO: 检查背包中是否有该物品
        # 这里简化处理，实际应该从背包中移除物品
        
        # 生成装备属性
        from shared.utils import generate_equipment_attributes
        attrs, variation = generate_equipment_attributes(
            equip_data.slot, 
            item.quality, 
            item.required_realm or 0
        )
        
        # 装备物品
        equipped_item = await EquipmentCRUD.equip_item(
            db=db,
            character_id=character.id,
            item_id=equip_data.item_id,
            slot=equip_data.slot,
            attribute_variation=variation,
            actual_attributes=attrs.model_dump()
        )

        # 返回更新后的角色信息
        updated_character = await CharacterCRUD.get_character_by_id(db, character.id)
        char_info = CharacterService.build_character_info(updated_character, include_equipment=True)
        
        return BaseResponse(
            success=True,
            message=f"成功装备 {item.name}",
            data={
                "character_info": char_info.model_dump(),
                "equipped_item": {
                    "id": equipped_item.id,
                    "item_name": item.name,
                    "slot": equip_data.slot,
                    "attributes": attrs.model_dump(),
                    "variation": variation
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"装备物品失败: {str(e)}"
        )


@router.post("/unequip", response_model=BaseResponse, summary="卸下装备")
async def unequip_item(
    unequip_data: UnequipItem,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    卸下当前用户角色装备

    - **slot**: 要卸下的装备部位
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 卸下装备
        success = await EquipmentCRUD.unequip_item(db, character.id, unequip_data.slot)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该部位没有装备"
            )
        
        # TODO: 将装备放回背包
        
        # 返回更新后的角色信息
        updated_character = await CharacterCRUD.get_character_by_id(db, character.id)
        char_info = CharacterService.build_character_info(updated_character, include_equipment=True)
        
        return BaseResponse(
            success=True,
            message=f"成功卸下{unequip_data.slot}装备",
            data={
                "character_info": char_info.model_dump()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"卸下装备失败: {str(e)}"
        )
