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
    BaseResponse, InventoryItem, EquipItem, UnequipItem, ItemInfo,
    UseItem, DeleteItem, SortInventory
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

        # 获取角色装备
        equipped_items = await EquipmentCRUD.get_character_equipment(db, character.id)

        # 构建装备数据
        equipment_data = {}
        for equipped_item in equipped_items:
            if equipped_item.item:
                item_info = ItemInfo.model_validate(equipped_item.item)
                equipment_data[equipped_item.slot] = {
                    "item_info": item_info.model_dump(),
                    "actual_attributes": equipped_item.actual_attributes or {},
                    "attribute_variation": equipped_item.attribute_variation,
                    "equipped_at": equipped_item.equipped_at.isoformat() if equipped_item.equipped_at else None
                }

        return BaseResponse(
            success=True,
            message="获取装备信息成功",
            data={
                "character_id": character.id,
                "equipment": equipment_data,
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
        
        # 检查背包中是否有该物品并移除
        inventory_items = await InventoryCRUD.get_character_inventory(db, character.id)
        target_inventory_item = None
        for inv_item in inventory_items:
            if inv_item.item_id == equip_data.item_id:
                target_inventory_item = inv_item
                break

        if not target_inventory_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="背包中没有该物品"
            )

        # 从背包中移除物品（装备类物品数量通常为1）
        if target_inventory_item.quantity > 1:
            target_inventory_item.quantity -= 1
            await db.commit()
        else:
            await db.delete(target_inventory_item)
            await db.commit()
        
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

        # 先获取要卸下的装备信息
        equipped_items = await EquipmentCRUD.get_character_equipment(db, character.id)
        target_equipped_item = None
        for equipped_item in equipped_items:
            if equipped_item.slot == unequip_data.slot:
                target_equipped_item = equipped_item
                break

        if not target_equipped_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该部位没有装备"
            )

        # 卸下装备
        success = await EquipmentCRUD.unequip_item(db, character.id, unequip_data.slot)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="卸下装备失败"
            )

        # 将装备放回背包
        from server.database.models import InventoryItem
        inventory_item = InventoryItem(
            character_id=character.id,
            item_id=target_equipped_item.item_id,
            quantity=1,
            attribute_variation=target_equipped_item.attribute_variation,
            actual_attributes=target_equipped_item.actual_attributes
        )
        db.add(inventory_item)
        await db.commit()
        
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


@router.post("/use-item", response_model=BaseResponse, summary="使用物品")
async def use_item(
    use_data: UseItem,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    使用背包中的物品（消耗品、丹药等）

    - **item_id**: 物品ID
    - **quantity**: 使用数量
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取物品信息
        item = await ItemCRUD.get_item_by_id(db, use_data.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物品不存在"
            )

        # 检查是否为可使用物品
        if item.item_type not in ["CONSUMABLE", "PILL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该物品不能使用"
            )

        # 检查背包中是否有足够的物品
        inventory_items = await InventoryCRUD.get_character_inventory(db, character.id)
        target_item = None
        for inv_item in inventory_items:
            if inv_item.item_id == use_data.item_id:
                target_item = inv_item
                break

        if not target_item or target_item.quantity < use_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="物品数量不足"
            )

        # 使用物品效果（简化处理）
        effect_message = f"使用了{item.name}x{use_data.quantity}"

        # 特殊物品效果处理
        if "转运" in item.name:
            # 气运道具，调用气运系统
            from server.core.systems.luck_system import LuckSystem
            result = await LuckSystem.use_luck_item(db, character, use_data.item_id, use_data.quantity)
            if not result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
            effect_message = result["message"]
        else:
            # 其他消耗品，减少数量
            await InventoryCRUD.remove_item_from_inventory(db, target_item.id, use_data.quantity)

        return BaseResponse(
            success=True,
            message=effect_message,
            data={
                "item_name": item.name,
                "quantity_used": use_data.quantity,
                "remaining_quantity": max(0, target_item.quantity - use_data.quantity)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"使用物品失败: {str(e)}"
        )


@router.post("/delete-item", response_model=BaseResponse, summary="删除物品")
async def delete_item(
    delete_data: DeleteItem,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除背包中的物品

    - **inventory_item_id**: 背包物品ID
    - **quantity**: 删除数量（None表示删除全部）
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 删除物品
        success = await InventoryCRUD.remove_item_from_inventory(
            db, delete_data.inventory_item_id, delete_data.quantity
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物品不存在"
            )

        return BaseResponse(
            success=True,
            message="物品删除成功",
            data={
                "inventory_item_id": delete_data.inventory_item_id,
                "quantity_deleted": delete_data.quantity
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除物品失败: {str(e)}"
        )


@router.post("/sort", response_model=BaseResponse, summary="整理背包")
async def sort_inventory(
    sort_data: SortInventory,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    整理背包物品

    - **sort_type**: 排序类型 (type, quality, name)
    """
    try:
        # 获取或创建角色
        character = await CharacterCRUD.get_or_create_character(db, current_user.id, current_user.username)

        # 获取背包物品
        inventory_items = await InventoryCRUD.get_character_inventory(db, character.id)

        # 根据排序类型进行排序
        if sort_data.sort_type == "type":
            # 按物品类型排序
            sorted_items = sorted(inventory_items, key=lambda x: (x.item.item_type if x.item else "", x.item.name if x.item else ""))
        elif sort_data.sort_type == "quality":
            # 按品质排序
            quality_order = {"COMMON": 1, "UNCOMMON": 2, "RARE": 3, "EPIC": 4, "LEGENDARY": 5}
            sorted_items = sorted(inventory_items, key=lambda x: (
                quality_order.get(x.item.quality if x.item else "COMMON", 0),
                x.item.name if x.item else ""
            ))
        else:  # name
            # 按名称排序
            sorted_items = sorted(inventory_items, key=lambda x: x.item.name if x.item else "")

        # 更新背包位置
        for i, item in enumerate(sorted_items):
            item.slot_position = i + 1

        await db.commit()

        return BaseResponse(
            success=True,
            message=f"背包整理完成（按{sort_data.sort_type}排序）",
            data={
                "sort_type": sort_data.sort_type,
                "total_items": len(sorted_items)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"整理背包失败: {str(e)}"
        )
