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
    ITEM_TYPES, ITEM_QUALITY, LUCK_SPECIAL_EVENTS
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
            # 检查今日是否已签到（基于服务器时间的每天凌晨12:00重置）
            from server.config import get_server_now, get_server_today, convert_to_server_time

            now = get_server_now()
            today = get_server_today()

            # 检查最后签到日期
            last_sign_date = None
            if character.last_sign_date:
                last_sign_datetime = convert_to_server_time(character.last_sign_date)
                last_sign_date = last_sign_datetime.date()

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

            # 更新角色气运值、最后活跃时间和签到日期（使用服务器时区）
            character.luck_value = new_luck
            character.last_active = now
            character.last_sign_date = now

            # 记录日志
            luck_change = new_luck - old_luck
            luck_level = get_luck_level_name(new_luck)

            await GameLogCRUD.create_log(
                db,
                character.id,
                "DAILY_SIGN",
                f"每日签到完成，今日气运：{luck_level}",
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

        # 计算特殊事件概率
        luck_level = get_luck_level_name(luck_value)
        base_chance = CULTIVATION_CONFIG["BASE_SPECIAL_EVENT_CHANCE"]

        # 获取气运等级对应的概率倍率
        luck_multipliers = LUCK_SPECIAL_EVENTS["LUCK_LEVEL_MULTIPLIERS"].get(luck_level, {"positive": 1.0, "negative": 1.0})

        # 计算正面和负面事件概率
        positive_chance = base_chance * luck_multipliers["positive"]
        negative_chance = base_chance * luck_multipliers["negative"]
        total_special_event_chance = positive_chance + negative_chance

        # 获取可能的事件列表
        possible_positive_events = list(LUCK_SPECIAL_EVENTS["POSITIVE_EVENTS"].keys())
        possible_negative_events = list(LUCK_SPECIAL_EVENTS["NEGATIVE_EVENTS"].keys())

        special_events = {
            "positive": possible_positive_events,
            "negative": possible_negative_events,
            "positive_chance": positive_chance,
            "negative_chance": negative_chance
        }

        return {
            "luck_level": luck_level,
            "multiplier": multiplier,
            "special_event_chance": total_special_event_chance,
            "special_events": special_events,
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
        event_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        触发特殊修炼事件

        Args:
            db: 数据库会话
            character: 角色对象
            event_info: 事件信息，包含事件类型和是否为正面事件

        Returns:
            事件结果
        """
        try:
            event_type = event_info.get("event_type")
            is_positive = event_info.get("is_positive", True)

            result = {"success": True, "message": "", "effects": {}, "event_type": event_type, "is_positive": is_positive}

            if is_positive:
                # 处理正面事件
                event_config = LUCK_SPECIAL_EVENTS["POSITIVE_EVENTS"].get(event_type, {})

                if event_type == "顿悟":
                    exp_bonus = random.randint(
                        event_config.get("exp_bonus_min", 100),
                        event_config.get("exp_bonus_max", 200)
                    )
                    character.cultivation_exp += exp_bonus
                    result["message"] = f"修炼时突然顿悟，修为大增！(+{exp_bonus})"
                    result["effects"]["cultivation_exp"] = exp_bonus

                elif event_type == "灵气共鸣":
                    spirit_stone_bonus = random.randint(
                        event_config.get("spirit_stone_bonus_min", 10),
                        event_config.get("spirit_stone_bonus_max", 50)
                    )
                    character.spirit_stone += spirit_stone_bonus
                    result["message"] = f"与天地灵气产生共鸣，获得灵石！(+{spirit_stone_bonus})"
                    result["effects"]["spirit_stone"] = spirit_stone_bonus



                elif event_type == "天材地宝":
                    # 随机提升一个属性
                    attributes = {
                        "hp": "生命值",
                        "physical_attack": "物理攻击",
                        "magic_attack": "魔法攻击",
                        "physical_defense": "物理防御",
                        "magic_defense": "魔法防御"
                    }
                    chosen_attr = random.choice(list(attributes.keys()))
                    attr_name = attributes[chosen_attr]
                    bonus = event_config.get("attribute_bonus", 5)

                    # 更新角色属性
                    current_value = getattr(character, chosen_attr, 0)
                    setattr(character, chosen_attr, current_value + bonus)

                    result["message"] = f"偶遇天材地宝，{attr_name}永久提升！(+{bonus})"
                    result["effects"][chosen_attr] = bonus

            else:
                # 处理负面事件
                event_config = LUCK_SPECIAL_EVENTS["NEGATIVE_EVENTS"].get(event_type, {})

                if event_type == "走火入魔":
                    exp_penalty = random.randint(
                        event_config.get("exp_penalty_min", 50),
                        event_config.get("exp_penalty_max", 100)
                    )
                    character.cultivation_exp = max(0, character.cultivation_exp - exp_penalty)
                    result["message"] = f"修炼时走火入魔，损失修为！(-{exp_penalty})"
                    result["effects"]["cultivation_exp"] = -exp_penalty

                elif event_type == "灵气紊乱":
                    spirit_stone_penalty = random.randint(
                        event_config.get("spirit_stone_penalty_min", 5),
                        event_config.get("spirit_stone_penalty_max", 20)
                    )
                    character.spirit_stone = max(0, character.spirit_stone - spirit_stone_penalty)
                    result["message"] = f"周围灵气紊乱，消耗额外灵石！(-{spirit_stone_penalty})"
                    result["effects"]["spirit_stone"] = -spirit_stone_penalty

                elif event_type == "财物散失":
                    gold_penalty = random.randint(
                        event_config.get("gold_penalty_min", 100),
                        event_config.get("gold_penalty_max", 500)
                    )
                    character.gold = max(0, character.gold - gold_penalty)
                    result["message"] = f"修炼时心神不宁，财物散失！(-{gold_penalty})"
                    result["effects"]["gold"] = -gold_penalty

                elif event_type == "气运受损":
                    luck_penalty = event_config.get("luck_penalty", 1)
                    old_luck = character.luck_value
                    character.luck_value = max(0, character.luck_value - luck_penalty)
                    actual_penalty = old_luck - character.luck_value
                    result["message"] = f"修炼时触犯禁忌，气运受损！(-{actual_penalty})"
                    result["effects"]["luck_value"] = -actual_penalty

            return result

        except Exception as e:
            await db.rollback()
            raise Exception(f"触发特殊事件失败: {str(e)}")
