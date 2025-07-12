# 气运系统核心逻辑

import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from server.database.models import Character, GameLog, InventoryItem, Item
from server.database.crud import CharacterCRUD, GameLogCRUD, InventoryCRUD
from shared.constants import (
    LUCK_LEVELS, DEFAULT_CONFIG, CULTIVATION_CONFIG,
    ITEM_TYPES, ITEM_QUALITY
)
from shared.utils import get_luck_level_name, generate_daily_luck


class LuckSystem:
    """气运系统核心类"""

    @staticmethod
    async def daily_sign_in(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """
        每日签到，随机获得气运值

        Args:
            db: 数据库会话
            character: 角色对象

        Returns:
            签到结果
        """
        try:
            # 检查今日是否已签到
            today = datetime.now().date()
            last_sign_date = character.last_active.date() if character.last_active else None

            if last_sign_date == today:
                luck_level = get_luck_level_name(character.luck_value)
                return {
                    "success": False,
                    "message": "今日已签到，请明日再来",
                    "new_luck": character.luck_value,
                    "luck_level": luck_level
                }

            # 生成今日气运值
            new_luck = generate_daily_luck()
            old_luck = character.luck_value

            # 更新角色气运值和最后活跃时间
            character.luck_value = new_luck
            character.last_active = datetime.now()

            # 记录日志
            luck_change = new_luck - old_luck
            luck_level = get_luck_level_name(new_luck)

            await GameLogCRUD.create_log(
                db,
                character.id,
                "DAILY_SIGN",
                f"每日签到完成，今日气运：{luck_level}({new_luck})",
                {
                    "old_luck": old_luck,
                    "new_luck": new_luck,
                    "luck_change": luck_change,
                    "luck_level": luck_level
                }
            )

            await db.commit()

            return {
                "success": True,
                "message": f"签到成功！今日气运：{luck_level}",
                "old_luck": old_luck,
                "new_luck": new_luck,
                "luck_change": luck_change,
                "luck_level": luck_level,
                "luck_color": LUCK_LEVELS[luck_level]["color"]
            }

        except Exception as e:
            await db.rollback()
            raise Exception(f"每日签到失败: {str(e)}")

    @staticmethod
    async def use_luck_item(
        db: AsyncSession,
        character: Character,
        item_id: int,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        使用气运道具（如转运丹）

        Args:
            db: 数据库会话
            character: 角色对象
            item_id: 道具ID
            quantity: 使用数量

        Returns:
            使用结果
        """
        try:
            # 获取道具信息
            item_result = await db.execute(select(Item).where(Item.id == item_id))
            item = item_result.scalar_one_or_none()

            if not item:
                return {"success": False, "message": "道具不存在"}

            # 检查是否为气运道具
            if (item.item_type not in ["CONSUMABLE", "PILL"]) or "转运" not in item.name:
                return {"success": False, "message": "该道具不是气运道具"}

            # 检查背包中是否有足够的道具
            inventory_result = await db.execute(
                select(InventoryItem).where(
                    InventoryItem.character_id == character.id,
                    InventoryItem.item_id == item_id
                )
            )
            inventory_item = inventory_result.scalar_one_or_none()

            if not inventory_item or inventory_item.quantity < quantity:
                return {"success": False, "message": "道具数量不足"}

            # 计算气运增加值
            luck_bonus = LuckSystem._calculate_item_luck_bonus(item, quantity)
            old_luck = character.luck_value
            new_luck = min(DEFAULT_CONFIG["MAX_LUCK_VALUE"], old_luck + luck_bonus)

            # 更新角色气运值
            character.luck_value = new_luck

            # 消耗道具
            if inventory_item.quantity == quantity:
                await db.delete(inventory_item)
            else:
                inventory_item.quantity -= quantity

            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "USE_LUCK_ITEM",
                f"使用{item.name}x{quantity}，气运+{luck_bonus}",
                {
                    "item_name": item.name,
                    "quantity": quantity,
                    "old_luck": old_luck,
                    "new_luck": new_luck,
                    "luck_bonus": luck_bonus
                }
            )

            await db.commit()

            return {
                "success": True,
                "message": f"使用{item.name}成功，气运+{luck_bonus}",
                "old_luck": old_luck,
                "new_luck": new_luck,
                "luck_bonus": luck_bonus,
                "luck_level": get_luck_level_name(new_luck)
            }

        except Exception as e:
            await db.rollback()
            raise Exception(f"使用气运道具失败: {str(e)}")

    @staticmethod
    def _calculate_item_luck_bonus(item: Item, quantity: int) -> int:
        """计算道具的气运加成"""
        # 根据道具品质和名称计算气运加成
        base_bonus = 10  # 基础加成

        # 品质加成
        quality_multiplier = {
            "COMMON": 1.0,
            "UNCOMMON": 1.5,
            "RARE": 2.0,
            "EPIC": 3.0,
            "LEGENDARY": 5.0
        }.get(item.quality, 1.0)

        # 道具类型加成
        if "小转运丹" in item.name:
            base_bonus = 5
        elif "转运丹" in item.name:
            base_bonus = 10
        elif "大转运丹" in item.name:
            base_bonus = 20
        elif "极品转运丹" in item.name:
            base_bonus = 50

        return int(base_bonus * quality_multiplier * quantity)

    @staticmethod
    def calculate_luck_effect_on_cultivation(luck_value: int) -> Dict[str, Any]:
        """
        计算气运对修炼的影响

        Args:
            luck_value: 当前气运值

        Returns:
            气运影响结果
        """
        luck_level = get_luck_level_name(luck_value)

        # 基础修炼倍率
        from shared.utils import calculate_luck_multiplier
        multiplier = calculate_luck_multiplier(luck_value)

        # 特殊事件概率
        special_event_chance = 0.0
        special_events = []

        if luck_value >= 80:  # 大吉
            special_event_chance = 0.15  # 15%概率触发特殊事件
            special_events = ["顿悟", "灵气共鸣", "功法突破"]
        elif luck_value >= 61:  # 小吉
            special_event_chance = 0.08  # 8%概率
            special_events = ["顿悟", "灵气共鸣"]
        elif luck_value >= 41:  # 平
            special_event_chance = 0.03  # 3%概率
            special_events = ["顿悟"]
        elif luck_value >= 26:  # 小凶
            special_event_chance = 0.05  # 5%概率负面事件
            special_events = ["修炼受阻"]
        elif luck_value >= 11:  # 凶
            special_event_chance = 0.10  # 10%概率负面事件
            special_events = ["修炼受阻", "走火入魔"]
        else:  # 大凶
            special_event_chance = 0.20  # 20%概率负面事件
            special_events = ["修炼受阻", "走火入魔"]

        return {
            "luck_level": luck_level,
            "multiplier": multiplier,
            "special_event_chance": special_event_chance,
            "possible_events": special_events,
            "is_positive": luck_value >= 50
        }

    @staticmethod
    def calculate_luck_effect_on_breakthrough(luck_value: int, base_success_rate: float) -> float:
        """
        计算气运对突破的影响

        Args:
            luck_value: 当前气运值
            base_success_rate: 基础成功率

        Returns:
            最终成功率
        """
        # 气运影响突破成功率
        luck_bonus = (luck_value - 50) * 0.01  # 每点气运影响1%成功率

        # 极端气运的额外影响
        if luck_value >= 90:  # 极好气运
            luck_bonus += 0.2  # 额外20%加成
        elif luck_value <= 10:  # 极差气运
            luck_bonus -= 0.3  # 额外30%减成

        final_rate = base_success_rate + luck_bonus
        return max(0.0, min(1.0, final_rate))  # 限制在0-1之间

    @staticmethod
    def calculate_luck_effect_on_drops(luck_value: int) -> Dict[str, Any]:
        """
        计算气运对掉落的影响

        Args:
            luck_value: 当前气运值

        Returns:
            掉落影响结果
        """
        luck_level = get_luck_level_name(luck_value)

        # 掉落数量倍率
        quantity_multiplier = 1.0
        if luck_value >= 80:
            quantity_multiplier = 1.5
        elif luck_value >= 61:
            quantity_multiplier = 1.2
        elif luck_value <= 25:
            quantity_multiplier = 0.8
        elif luck_value <= 10:
            quantity_multiplier = 0.5

        # 品质提升概率
        quality_upgrade_chance = 0.0
        if luck_value >= 80:
            quality_upgrade_chance = 0.3  # 30%概率品质提升
        elif luck_value >= 61:
            quality_upgrade_chance = 0.15  # 15%概率
        elif luck_value >= 41:
            quality_upgrade_chance = 0.05  # 5%概率

        # 稀有掉落概率
        rare_drop_chance = 0.0
        if luck_value >= 90:
            rare_drop_chance = 0.1  # 10%概率稀有掉落
        elif luck_value >= 75:
            rare_drop_chance = 0.05  # 5%概率

        return {
            "luck_level": luck_level,
            "quantity_multiplier": quantity_multiplier,
            "quality_upgrade_chance": quality_upgrade_chance,
            "rare_drop_chance": rare_drop_chance
        }

    @staticmethod
    async def trigger_special_cultivation_event(
        db: AsyncSession,
        character: Character,
        event_type: str
    ) -> Dict[str, Any]:
        """
        触发特殊修炼事件

        Args:
            db: 数据库会话
            character: 角色对象
            event_type: 事件类型

        Returns:
            事件结果
        """
        try:
            result = {"success": True, "message": "", "effects": {}}

            if event_type == "顿悟":
                # 顿悟：获得大量修为
                exp_bonus = random.randint(100, 500)
                character.cultivation_exp += exp_bonus
                result["message"] = f"修炼时突然顿悟，修为大增！(+{exp_bonus})"
                result["effects"]["cultivation_exp"] = exp_bonus

            elif event_type == "灵气共鸣":
                # 灵气共鸣：获得灵石
                spirit_stone_bonus = random.randint(10, 50)
                character.spirit_stone += spirit_stone_bonus
                result["message"] = f"与天地灵气产生共鸣，获得灵石！(+{spirit_stone_bonus})"
                result["effects"]["spirit_stone"] = spirit_stone_bonus

            elif event_type == "功法突破":
                # 功法突破：修炼速度临时提升
                result["message"] = "功法修炼有所突破，修炼效率提升！"
                result["effects"]["cultivation_speed_bonus"] = 0.5

            elif event_type == "修炼受阻":
                # 修炼受阻：修为减少
                exp_loss = random.randint(20, 100)
                character.cultivation_exp = max(0, character.cultivation_exp - exp_loss)
                result["message"] = f"修炼时心神不宁，修为有所损失(-{exp_loss})"
                result["effects"]["cultivation_exp"] = -exp_loss

            elif event_type == "走火入魔":
                # 走火入魔：修为大幅减少，气运降低
                exp_loss = random.randint(100, 300)
                luck_loss = random.randint(5, 15)
                character.cultivation_exp = max(0, character.cultivation_exp - exp_loss)
                character.luck_value = max(0, character.luck_value - luck_loss)
                result["message"] = f"修炼时走火入魔！修为和气运都有损失(-{exp_loss}修为, -{luck_loss}气运)"
                result["effects"]["cultivation_exp"] = -exp_loss
                result["effects"]["luck_value"] = -luck_loss



            # 记录事件日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "SPECIAL_EVENT",
                result["message"],
                {
                    "event_type": event_type,
                    "effects": result["effects"]
                }
            )

            await db.commit()
            return result

        except Exception as e:
            await db.rollback()
            raise Exception(f"触发特殊事件失败: {str(e)}")
