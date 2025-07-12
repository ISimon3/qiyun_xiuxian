# 修为、境界、突破逻辑

import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from server.database.models import Character, GameLog
from server.database.crud import CharacterCRUD, GameLogCRUD
from server.core.systems.luck_system import LuckSystem
from shared.constants import (
    CULTIVATION_REALMS, CULTIVATION_EXP_REQUIREMENTS,
    CULTIVATION_FOCUS_TYPES, CULTIVATION_CONFIG, DEFAULT_CONFIG
)
from shared.utils import (
    simulate_cultivation_session, get_realm_name,
    get_luck_level_name, calculate_base_attributes
)


class CultivationSystem:
    """修炼系统核心类"""

    @staticmethod
    async def start_cultivation(
        db: AsyncSession,
        character: Character,
        cultivation_focus: str = "HP"
    ) -> Dict[str, Any]:
        """
        开始挂机修炼

        Args:
            db: 数据库会话
            character: 角色对象
            cultivation_focus: 修炼方向 (HP, PHYSICAL_ATTACK, MAGIC_ATTACK, PHYSICAL_DEFENSE, MAGIC_DEFENSE)

        Returns:
            开始修炼结果
        """
        try:
            # 验证修炼方向
            if cultivation_focus not in CULTIVATION_FOCUS_TYPES:
                return {
                    "success": False,
                    "message": f"无效的修炼方向: {cultivation_focus}"
                }

            # 更新角色的修炼方向
            character.cultivation_focus = cultivation_focus
            character.last_active = datetime.now()

            # 记录日志
            focus_name = CULTIVATION_FOCUS_TYPES[cultivation_focus]["name"]
            await GameLogCRUD.create_log(
                db,
                character.id,
                "CULTIVATION_START",
                f"开始修炼，专注方向：{focus_name}",
                {
                    "cultivation_focus": cultivation_focus,
                    "focus_name": focus_name
                }
            )

            await db.commit()

            return {
                "success": True,
                "message": f"开始修炼，专注方向：{focus_name}",
                "cultivation_focus": cultivation_focus,
                "focus_name": focus_name
            }

        except Exception as e:
            await db.rollback()
            raise Exception(f"开始修炼失败: {str(e)}")

    @staticmethod
    async def change_cultivation_focus(
        db: AsyncSession,
        character: Character,
        cultivation_focus: str
    ) -> Dict[str, Any]:
        """
        变更修炼方向

        Args:
            db: 数据库会话
            character: 角色对象
            cultivation_focus: 新的修炼方向

        Returns:
            变更结果
        """
        try:
            # 验证修炼方向
            if cultivation_focus not in CULTIVATION_FOCUS_TYPES:
                return {
                    "success": False,
                    "message": f"无效的修炼方向: {cultivation_focus}"
                }

            # 获取旧的修炼方向
            old_focus = character.cultivation_focus or "HP"
            old_focus_name = CULTIVATION_FOCUS_TYPES.get(old_focus, {}).get("name", "未知")

            # 更新角色的修炼方向
            character.cultivation_focus = cultivation_focus
            character.last_active = datetime.now()

            # 记录日志
            focus_name = CULTIVATION_FOCUS_TYPES[cultivation_focus]["name"]
            await GameLogCRUD.create_log(
                db,
                character.id,
                "CULTIVATION_FOCUS_CHANGE",
                f"修炼方向变更：{old_focus_name} → {focus_name}",
                {
                    "old_cultivation_focus": old_focus,
                    "new_cultivation_focus": cultivation_focus,
                    "old_focus_name": old_focus_name,
                    "new_focus_name": focus_name
                }
            )

            await db.commit()

            return {
                "success": True,
                "message": f"修炼方向已变更为：{focus_name}",
                "old_cultivation_focus": old_focus,
                "new_cultivation_focus": cultivation_focus,
                "old_focus_name": old_focus_name,
                "new_focus_name": focus_name
            }

        except Exception as e:
            await db.rollback()
            raise Exception(f"变更修炼方向失败: {str(e)}")

    @staticmethod
    async def process_cultivation_cycle(
        db: AsyncSession,
        character: Character
    ) -> Dict[str, Any]:
        """
        处理一次修炼周期（5分钟）

        Args:
            db: 数据库会话
            character: 角色对象

        Returns:
            修炼结果
        """
        try:
            # 检查是否在修炼状态
            if not character.cultivation_focus:
                character.cultivation_focus = "HP"  # 默认体修

            # 计算修炼收益 (5分钟 = 5次1分钟修炼)
            cultivation_result = simulate_cultivation_session(
                character.luck_value,
                character.cultivation_focus,
                1.0  # 基础修炼速度
            )

            # 5分钟的收益是1分钟的5倍
            cultivation_result["exp_gained"] *= 5
            cultivation_result["attribute_gained"] *= 5

            # 应用修炼收益
            old_exp = character.cultivation_exp
            old_realm = character.cultivation_realm

            # 修为变化
            character.cultivation_exp += cultivation_result["exp_gained"]

            # 基础属性变化
            attribute_type = cultivation_result["attribute_type"]
            attribute_gained = cultivation_result["attribute_gained"]

            if attribute_type == "HP":
                character.hp_training += attribute_gained
            elif attribute_type == "PHYSICAL_ATTACK":
                character.physical_attack_training += attribute_gained
            elif attribute_type == "MAGIC_ATTACK":
                character.magic_attack_training += attribute_gained
            elif attribute_type == "PHYSICAL_DEFENSE":
                character.physical_defense_training += attribute_gained
            elif attribute_type == "MAGIC_DEFENSE":
                character.magic_defense_training += attribute_gained

            # 不进行自动突破，只有手动突破
            realm_changed = False

            # 处理特殊事件
            special_event_result = None
            if cultivation_result.get("special_event"):
                special_event_result = await LuckSystem.trigger_special_cultivation_event(
                    db, character, cultivation_result["special_event"]
                )

            # 更新最后活跃时间
            character.last_active = datetime.now()

            # 记录修炼日志
            log_message = f"修炼收益：修为+{cultivation_result['exp_gained']}"
            if attribute_gained > 0:
                focus_name = CULTIVATION_FOCUS_TYPES[attribute_type]["name"]
                log_message += f"，{focus_name}+{attribute_gained}"

            if cultivation_result.get("luck_effect"):
                log_message += f"（{cultivation_result['luck_effect']}）"

            log_data = {
                "exp_gained": cultivation_result["exp_gained"],
                "attribute_type": attribute_type,
                "attribute_gained": attribute_gained,
                "luck_multiplier": cultivation_result["luck_multiplier"],
                "luck_effect": cultivation_result.get("luck_effect"),
                "special_event": cultivation_result.get("special_event")
            }

            # 移除自动突破相关的日志记录

            await GameLogCRUD.create_log(
                db,
                character.id,
                "CULTIVATION_CYCLE",
                log_message,
                log_data
            )

            # 如果有特殊事件，记录特殊事件日志
            if special_event_result:
                await GameLogCRUD.create_log(
                    db,
                    character.id,
                    "SPECIAL_EVENT",
                    special_event_result["message"],
                    special_event_result["effects"]
                )

            await db.commit()

            return {
                "success": True,
                "exp_gained": cultivation_result["exp_gained"],
                "attribute_gained": attribute_gained,
                "attribute_type": attribute_type,
                "focus_name": cultivation_result["focus_name"],
                "luck_multiplier": cultivation_result["luck_multiplier"],
                "luck_effect": cultivation_result.get("luck_effect"),
                "special_event": cultivation_result.get("special_event"),
                "special_event_result": special_event_result,
                "current_exp": character.cultivation_exp
            }

        except Exception as e:
            await db.rollback()
            raise Exception(f"修炼周期处理失败: {str(e)}")



    @staticmethod
    async def manual_breakthrough(
        db: AsyncSession,
        character: Character,
        use_items: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        手动突破境界

        Args:
            db: 数据库会话
            character: 角色对象
            use_items: 使用的辅助物品ID列表

        Returns:
            突破结果
        """
        try:
            current_realm = character.cultivation_realm
            target_realm = current_realm + 1

            # 检查是否已达到最高境界
            if current_realm >= len(CULTIVATION_REALMS) - 1:
                return {
                    "success": False,
                    "message": "已达到最高境界，无法继续突破"
                }

            # 检查修为是否足够
            required_exp = CULTIVATION_EXP_REQUIREMENTS.get(target_realm, float('inf'))
            if character.cultivation_exp < required_exp:
                return {
                    "success": False,
                    "message": f"修为不足，需要{required_exp}修为才能突破到{get_realm_name(target_realm)}"
                }

            # 计算突破成功率
            from server.core.character_service import CharacterService
            success_rate = CharacterService.calculate_breakthrough_success_rate(
                character, target_realm, use_items
            )

            # 进行突破判定
            success = random.random() < success_rate

            if success:
                # 突破成功
                old_realm = character.cultivation_realm
                character.cultivation_realm = target_realm

                # 消耗修为
                character.cultivation_exp -= required_exp

                # 记录日志
                await GameLogCRUD.create_log(
                    db,
                    character.id,
                    "BREAKTHROUGH_SUCCESS",
                    f"手动突破成功！从{get_realm_name(old_realm)}突破至{get_realm_name(target_realm)}",
                    {
                        "old_realm": old_realm,
                        "new_realm": target_realm,
                        "success_rate": success_rate,
                        "exp_consumed": required_exp,
                        "use_items": use_items or []
                    }
                )

                await db.commit()

                return {
                    "success": True,
                    "message": f"突破成功！境界提升至{get_realm_name(target_realm)}",
                    "old_realm": old_realm,
                    "new_realm": target_realm,
                    "success_rate": success_rate,
                    "exp_consumed": required_exp
                }
            else:
                # 突破失败
                exp_loss = int(required_exp * 0.2)  # 手动突破失败损失20%所需修为
                character.cultivation_exp = max(0, character.cultivation_exp - exp_loss)

                # 记录日志
                await GameLogCRUD.create_log(
                    db,
                    character.id,
                    "BREAKTHROUGH_FAILED",
                    f"手动突破失败，修为损失{exp_loss}",
                    {
                        "target_realm": target_realm,
                        "success_rate": success_rate,
                        "exp_loss": exp_loss,
                        "use_items": use_items or []
                    }
                )

                await db.commit()

                return {
                    "success": False,
                    "message": f"突破失败，修为损失{exp_loss}",
                    "success_rate": success_rate,
                    "exp_loss": exp_loss
                }

        except Exception as e:
            await db.rollback()
            raise Exception(f"手动突破失败: {str(e)}")

    @staticmethod
    async def get_cultivation_status(
        db: AsyncSession,
        character: Character
    ) -> Dict[str, Any]:
        """
        获取修炼状态信息

        Args:
            db: 数据库会话
            character: 角色对象

        Returns:
            修炼状态信息
        """
        try:
            current_realm = character.cultivation_realm
            current_exp = character.cultivation_exp

            # 当前境界信息
            current_realm_name = get_realm_name(current_realm)

            # 下一境界信息
            next_realm = current_realm + 1
            next_realm_name = get_realm_name(next_realm) if next_realm < len(CULTIVATION_REALMS) else "已达巅峰"

            # 突破所需修为
            required_exp = CULTIVATION_EXP_REQUIREMENTS.get(next_realm, 0)
            exp_progress = min(current_exp / required_exp, 1.0) if required_exp > 0 else 1.0

            # 修炼方向信息
            cultivation_focus = character.cultivation_focus or "HP"
            focus_info = CULTIVATION_FOCUS_TYPES.get(cultivation_focus, CULTIVATION_FOCUS_TYPES["HP"])

            # 气运影响
            luck_effect = LuckSystem.calculate_luck_effect_on_cultivation(character.luck_value)

            # 突破成功率
            breakthrough_rate = 0.0
            can_breakthrough = False
            if current_realm < len(CULTIVATION_REALMS) - 1 and current_exp >= required_exp:
                from server.core.character_service import CharacterService
                breakthrough_rate = CharacterService.calculate_breakthrough_success_rate(character, next_realm)
                can_breakthrough = True

            return {
                "success": True,
                "current_realm": current_realm,
                "current_realm_name": current_realm_name,
                "current_exp": current_exp,
                "next_realm": next_realm,
                "next_realm_name": next_realm_name,
                "required_exp": required_exp,
                "exp_progress": exp_progress,
                "can_breakthrough": can_breakthrough,
                "breakthrough_rate": breakthrough_rate,
                "cultivation_focus": cultivation_focus,
                "focus_name": focus_info["name"],
                "luck_effect": luck_effect,
                "is_cultivating": character.cultivation_focus is not None
            }

        except Exception as e:
            raise Exception(f"获取修炼状态失败: {str(e)}")
