# 用户游戏数据初始化服务

import random
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.database.models import Character, Item, InventoryItem, EquippedItem
from server.database.crud import InventoryCRUD, EquipmentCRUD
from shared.constants import EQUIPMENT_SLOTS, ITEM_QUALITY
from shared.utils import generate_equipment_attributes


class CharacterInitService:
    """用户游戏数据初始化服务"""
    
    @staticmethod
    async def initialize_new_character(db: AsyncSession, character: Character) -> None:
        """
        为新创建的角色初始化装备和物品

        Args:
            db: 数据库会话
            character: 新创建的角色
        """
        # 1. 给予初始装备
        await CharacterInitService._give_starter_equipment(db, character)

        # 2. 给予初始物品
        await CharacterInitService._give_starter_items(db, character)
    
    @staticmethod
    async def _give_starter_equipment(db: AsyncSession, character: Character) -> None:
        """给予初始装备"""
        # 为每个装备部位分配一件普通品质的装备
        for slot_key, slot_name in EQUIPMENT_SLOTS.items():
            # 查找适合新手的普通装备（境界需求为0）
            result = await db.execute(
                select(Item).where(
                    and_(
                        Item.item_type == "EQUIPMENT",
                        Item.equipment_slot == slot_key,
                        Item.quality == "COMMON",
                        Item.required_realm == 0
                    )
                ).limit(1)
            )

            equipment_item = result.scalar_one_or_none()
            if not equipment_item:
                continue

            # 生成装备属性（带随机波动）
            base_attrs = equipment_item.base_attributes or {}
            attrs, variation = generate_equipment_attributes(slot_key, "COMMON", 0)

            # 装备该物品
            try:
                await EquipmentCRUD.equip_item(
                    db=db,
                    character_id=character.id,
                    item_id=equipment_item.id,
                    slot=slot_key,
                    attribute_variation=variation,
                    actual_attributes=attrs.model_dump()
                )
            except Exception as e:
                # 静默处理装备失败，不影响角色创建
                pass
    
    @staticmethod
    async def _give_starter_items(db: AsyncSession, character: Character) -> None:
        """给予初始物品"""
        # 初始物品列表
        starter_items = [
            {"name": "回血丹", "quantity": 10},
            {"name": "回灵丹", "quantity": 5},
            {"name": "灵草", "quantity": 20},
            {"name": "灵石碎片", "quantity": 10},
            {"name": "灵草种子", "quantity": 5}
        ]

        for item_info in starter_items:
            # 查找物品
            result = await db.execute(
                select(Item).where(Item.name == item_info["name"]).limit(1)
            )

            item = result.scalar_one_or_none()
            if not item:
                continue

            # 添加到背包
            try:
                await InventoryCRUD.add_item_to_inventory(
                    db=db,
                    character_id=character.id,
                    item_id=item.id,
                    quantity=item_info["quantity"]
                )
            except Exception as e:
                # 静默处理物品添加失败，不影响角色创建
                pass
    
    @staticmethod
    def get_random_spiritual_root() -> str:
        """根据权重随机生成灵根类型"""
        from shared.constants import SPIRITUAL_ROOTS

        # 使用新的权重系统进行随机分配
        spiritual_roots = []
        weights = []

        for root_name, root_info in SPIRITUAL_ROOTS.items():
            spiritual_roots.append(root_name)
            weights.append(root_info["weight"])

        return random.choices(spiritual_roots, weights=weights)[0]
    
    @staticmethod
    async def validate_character_creation(
        db: AsyncSession, 
        user_id: int, 
        character_name: str
    ) -> tuple[bool, str]:
        """
        验证角色创建的有效性
        
        Returns:
            (is_valid, error_message)
        """
        # 检查角色名长度
        if len(character_name) < 2 or len(character_name) > 20:
            return False, "角色名长度必须在2-20个字符之间"
        
        # 检查角色名是否包含特殊字符
        import re
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$', character_name):
            return False, "角色名只能包含中文、英文、数字和下划线"
        
        # 检查是否有敏感词（这里简单检查几个）
        forbidden_words = ["管理员", "GM", "系统", "客服", "admin"]
        for word in forbidden_words:
            if word.lower() in character_name.lower():
                return False, "角色名包含禁用词汇"
        
        return True, ""
    
    @staticmethod
    def get_spiritual_root_info() -> dict:
        """获取灵根信息（用于参考）"""
        from shared.constants import SPIRITUAL_ROOTS

        # 灵根类型信息（按修炼速度排序）
        root_info = []
        for root_name, root_data in SPIRITUAL_ROOTS.items():
            root_info.append({
                "name": root_name,
                "multiplier": root_data["multiplier"],
                "rarity": root_data["rarity"],
                "description": f"修炼速度: {root_data['multiplier']}x"
            })

        # 按修炼速度倍率排序
        root_info.sort(key=lambda x: x["multiplier"], reverse=True)

        return {
            "spiritual_roots": root_info,
            "info": [
                "系统会为新用户注册时自动随机分配灵根",
                "天灵根：2.0倍修炼速度，+15%突破成功率（传说级，权重1）",
                "变异灵根：1.5倍修炼速度，+10%突破成功率（史诗级，权重3）",
                "单灵根：1.2倍修炼速度，+5%突破成功率（优秀级，权重20）",
                "双灵根：1.1倍修炼速度（普通级，权重40）",
                "三灵根：1.0倍修炼速度，基准（普通级，权重40）",
                "四灵根：0.9倍修炼速度（普通级，权重40）",
                "五灵根：0.8倍修炼速度（普通级，权重40）",
                "废灵根：0.7倍修炼速度（普通级，权重40）"
            ]
        }
