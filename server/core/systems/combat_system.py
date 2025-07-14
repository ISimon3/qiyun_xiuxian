# 副本、战斗逻辑

import random
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from server.database.models import Character, DungeonInstance, CombatLog, Monster
from server.database.crud import GameLogCRUD
from shared.constants import (
    COMBAT_SYSTEM_CONFIG, DUNGEON_SYSTEM_CONFIG, MONSTER_CONFIGS,
    REALM_BASE_ATTRIBUTES
)
from shared.utils import calculate_base_attributes, calculate_final_attributes
from shared.schemas import CharacterTrainingAttributes, EquipmentAttributes
from server.core.character_service import CharacterService


class CombatSystem:
    """战斗系统核心类"""

    @staticmethod
    def calculate_damage(
        attacker_stats: Dict[str, Any],
        defender_stats: Dict[str, Any],
        skill_type: str = "NORMAL_ATTACK",
        is_player_attacker: bool = True
    ) -> Tuple[int, bool]:
        """
        计算伤害值

        Args:
            attacker_stats: 攻击者属性
            defender_stats: 防御者属性
            skill_type: 技能类型
            is_player_attacker: 是否为玩家攻击

        Returns:
            (伤害值, 是否暴击)
        """
        try:
            # 获取技能配置
            skill_config = COMBAT_SYSTEM_CONFIG["SKILL_EFFECTS"].get(
                skill_type, COMBAT_SYSTEM_CONFIG["SKILL_EFFECTS"]["NORMAL_ATTACK"]
            )

            # 确定攻击类型和基础伤害
            if skill_config["type"] == "MAGIC":
                base_attack = attacker_stats.get("magic_attack", 0)
                defense = defender_stats.get("magic_defense", 0)
            else:  # PHYSICAL
                base_attack = attacker_stats.get("physical_attack", 0)
                defense = defender_stats.get("physical_defense", 0)

            # 应用技能倍率
            damage_multiplier = skill_config.get("damage_multiplier", 1.0)
            base_damage = base_attack * damage_multiplier

            # 计算防御减伤
            defense_reduction = defense * COMBAT_SYSTEM_CONFIG["DEFENSE_REDUCTION_FACTOR"]
            damage = max(base_damage - defense_reduction, COMBAT_SYSTEM_CONFIG["MIN_DAMAGE"])

            # 计算暴击
            critical_rate = attacker_stats.get("critical_rate", COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_RATE"])
            critical_rate += skill_config.get("critical_rate_bonus", 0)

            is_critical = random.random() < critical_rate
            if is_critical:
                critical_damage = attacker_stats.get("critical_damage", COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_DAMAGE"])
                damage *= critical_damage

            # 添加伤害浮动
            variance = COMBAT_SYSTEM_CONFIG["DAMAGE_VARIANCE"]
            damage_variance = random.uniform(1 - variance, 1 + variance)
            damage = int(damage * damage_variance)

            return max(damage, COMBAT_SYSTEM_CONFIG["MIN_DAMAGE"]), is_critical

        except Exception as e:
            # 发生错误时返回最小伤害
            return COMBAT_SYSTEM_CONFIG["MIN_DAMAGE"], False

    @staticmethod
    def calculate_heal(healer_stats: Dict[str, Any], skill_type: str = "HEAL") -> int:
        """
        计算治疗量

        Args:
            healer_stats: 治疗者属性
            skill_type: 技能类型

        Returns:
            治疗量
        """
        try:
            skill_config = COMBAT_SYSTEM_CONFIG["SKILL_EFFECTS"].get(skill_type)
            if not skill_config or skill_config["type"] != "HEAL":
                return 0

            max_hp = healer_stats.get("max_hp", 100)
            heal_multiplier = skill_config.get("heal_multiplier", 0.3)
            heal_amount = int(max_hp * heal_multiplier)

            # 添加一些随机性
            variance = COMBAT_SYSTEM_CONFIG["DAMAGE_VARIANCE"]
            heal_variance = random.uniform(1 - variance, 1 + variance)
            heal_amount = int(heal_amount * heal_variance)

            return max(heal_amount, 1)

        except Exception as e:
            return 0

    @staticmethod
    def get_player_combat_stats(character: Character) -> Dict[str, Any]:
        """
        获取玩家战斗属性

        Args:
            character: 角色对象

        Returns:
            战斗属性字典
        """
        try:
            # 使用CharacterService获取完整的角色信息，包含最终属性
            character_info = CharacterService.build_character_info(character, include_equipment=True)
            final_attributes = character_info.attributes

            # 构建战斗属性
            combat_stats = {
                "max_hp": final_attributes.hp,
                "current_hp": character.current_hp,
                "physical_attack": final_attributes.physical_attack,
                "magic_attack": final_attributes.magic_attack,
                "physical_defense": final_attributes.physical_defense,
                "magic_defense": final_attributes.magic_defense,
                "critical_rate": final_attributes.critical_rate / 100.0,  # 转换为小数
                "critical_damage": final_attributes.critical_damage / 100.0  # 转换为小数
            }

            return combat_stats

        except Exception as e:
            # 返回默认属性
            return {
                "max_hp": 100,
                "current_hp": 100,
                "physical_attack": 20,
                "magic_attack": 20,
                "physical_defense": 15,
                "magic_defense": 15,
                "critical_rate": COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_RATE"],
                "critical_damage": COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_DAMAGE"]
            }

    @staticmethod
    def get_monster_combat_stats(monster_config: Dict[str, Any], difficulty: str = "NORMAL") -> Dict[str, Any]:
        """
        获取怪物战斗属性

        Args:
            monster_config: 怪物配置
            difficulty: 副本难度

        Returns:
            战斗属性字典
        """
        try:
            # 获取难度倍率
            difficulty_multiplier = DUNGEON_SYSTEM_CONFIG["DIFFICULTY_MULTIPLIERS"].get(
                difficulty, DUNGEON_SYSTEM_CONFIG["DIFFICULTY_MULTIPLIERS"]["NORMAL"]
            )

            # 获取怪物类型倍率
            monster_type = monster_config.get("monster_type", "NORMAL")
            type_multiplier = DUNGEON_SYSTEM_CONFIG["MONSTER_TYPE_MULTIPLIERS"].get(
                monster_type, DUNGEON_SYSTEM_CONFIG["MONSTER_TYPE_MULTIPLIERS"]["NORMAL"]
            )

            # 计算最终属性
            base_hp = monster_config["base_hp"]
            hp_multiplier = difficulty_multiplier["monster_hp_multiplier"] * type_multiplier["hp_multiplier"]
            max_hp = int(base_hp * hp_multiplier)

            attack_multiplier = difficulty_multiplier["monster_attack_multiplier"] * type_multiplier["attack_multiplier"]
            defense_multiplier = type_multiplier["defense_multiplier"]

            combat_stats = {
                "max_hp": max_hp,
                "current_hp": max_hp,
                "physical_attack": int(monster_config["base_physical_attack"] * attack_multiplier),
                "magic_attack": int(monster_config["base_magic_attack"] * attack_multiplier),
                "physical_defense": int(monster_config["base_physical_defense"] * defense_multiplier),
                "magic_defense": int(monster_config["base_magic_defense"] * defense_multiplier),
                "critical_rate": monster_config.get("critical_rate", COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_RATE"]),
                "critical_damage": monster_config.get("critical_damage", COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_DAMAGE"])
            }

            return combat_stats

        except Exception as e:
            # 返回默认怪物属性
            return {
                "max_hp": 100,
                "current_hp": 100,
                "physical_attack": 30,
                "magic_attack": 20,
                "physical_defense": 15,
                "magic_defense": 10,
                "critical_rate": COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_RATE"],
                "critical_damage": COMBAT_SYSTEM_CONFIG["BASE_CRITICAL_DAMAGE"]
            }

    @staticmethod
    def choose_monster_action(
        monster_config: Dict[str, Any],
        monster_stats: Dict[str, Any],
        player_stats: Dict[str, Any],
        turn_count: int
    ) -> str:
        """
        选择怪物行动

        Args:
            monster_config: 怪物配置
            monster_stats: 怪物当前属性
            player_stats: 玩家属性
            turn_count: 回合数

        Returns:
            选择的技能
        """
        try:
            available_skills = monster_config.get("skills", ["NORMAL_ATTACK"])
            ai_pattern = monster_config.get("ai_pattern", {"aggressive": 0.7, "defensive": 0.3})

            # 如果怪物血量低于30%，更倾向于防御或治疗
            hp_ratio = monster_stats["current_hp"] / monster_stats["max_hp"]
            if hp_ratio < 0.3:
                if "HEAL" in available_skills and random.random() < 0.6:
                    return "HEAL"
                elif "DEFEND" in available_skills and random.random() < 0.4:
                    return "DEFEND"

            # 根据AI模式选择行动
            if random.random() < ai_pattern.get("aggressive", 0.7):
                # 攻击性行动
                attack_skills = [skill for skill in available_skills
                               if skill in ["NORMAL_ATTACK", "HEAVY_ATTACK", "MAGIC_ATTACK", "POISON_BITE", "SWIFT_STRIKE"]]
                if attack_skills:
                    return random.choice(attack_skills)
            else:
                # 防御性行动
                defensive_skills = [skill for skill in available_skills
                                  if skill in ["DEFEND", "HEAL", "STONE_SHIELD", "NATURE_BLESSING"]]
                if defensive_skills:
                    return random.choice(defensive_skills)

            # 默认普通攻击
            return "NORMAL_ATTACK"

        except Exception as e:
            return "NORMAL_ATTACK"

    @staticmethod
    async def execute_combat_action(
        db: AsyncSession,
        dungeon_instance: DungeonInstance,
        action_type: str,
        actor: str,
        player_stats: Dict[str, Any],
        monster_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行战斗行动

        Args:
            db: 数据库会话
            dungeon_instance: 副本实例
            action_type: 行动类型
            actor: 行动者 (PLAYER/MONSTER)
            player_stats: 玩家属性
            monster_stats: 怪物属性

        Returns:
            行动结果
        """
        try:
            result = {
                "success": True,
                "action_type": action_type,
                "actor": actor,
                "damage": 0,
                "heal": 0,
                "is_critical": False,
                "description": "",
                "player_hp_before": player_stats["current_hp"],
                "monster_hp_before": monster_stats["current_hp"],
                "player_hp_after": player_stats["current_hp"],
                "monster_hp_after": monster_stats["current_hp"]
            }

            if actor == "PLAYER":
                attacker_stats = player_stats
                defender_stats = monster_stats
                target = "MONSTER"
            else:
                attacker_stats = monster_stats
                defender_stats = player_stats
                target = "PLAYER"

            # 执行不同类型的行动
            if action_type in ["NORMAL_ATTACK", "HEAVY_ATTACK", "MAGIC_ATTACK", "POISON_BITE", "SWIFT_STRIKE"]:
                # 攻击行动
                damage, is_critical = CombatSystem.calculate_damage(
                    attacker_stats, defender_stats, action_type, actor == "PLAYER"
                )

                result["damage"] = damage
                result["is_critical"] = is_critical

                # 应用伤害
                if target == "PLAYER":
                    player_stats["current_hp"] = max(0, player_stats["current_hp"] - damage)
                    result["player_hp_after"] = player_stats["current_hp"]
                else:
                    monster_stats["current_hp"] = max(0, monster_stats["current_hp"] - damage)
                    result["monster_hp_after"] = monster_stats["current_hp"]

                # 生成描述
                actor_name = "你" if actor == "PLAYER" else dungeon_instance.monster_data.get("name", "怪物")
                target_name = "怪物" if target == "MONSTER" else "你"
                critical_text = "暴击！" if is_critical else ""
                result["description"] = f"{actor_name}对{target_name}造成了{damage}点伤害！{critical_text}"

            elif action_type == "HEAL":
                # 治疗行动
                heal_amount = CombatSystem.calculate_heal(attacker_stats, action_type)

                if actor == "PLAYER":
                    max_heal = player_stats["max_hp"] - player_stats["current_hp"]
                    actual_heal = min(heal_amount, max_heal)
                    player_stats["current_hp"] += actual_heal
                    result["player_hp_after"] = player_stats["current_hp"]
                else:
                    max_heal = monster_stats["max_hp"] - monster_stats["current_hp"]
                    actual_heal = min(heal_amount, max_heal)
                    monster_stats["current_hp"] += actual_heal
                    result["monster_hp_after"] = monster_stats["current_hp"]

                result["heal"] = actual_heal
                actor_name = "你" if actor == "PLAYER" else dungeon_instance.monster_data.get("name", "怪物")
                result["description"] = f"{actor_name}恢复了{actual_heal}点生命值！"

            elif action_type == "DEFEND":
                # 防御行动
                actor_name = "你" if actor == "PLAYER" else dungeon_instance.monster_data.get("name", "怪物")
                result["description"] = f"{actor_name}进入了防御状态！"

            else:
                # 其他特殊技能
                actor_name = "你" if actor == "PLAYER" else dungeon_instance.monster_data.get("name", "怪物")
                result["description"] = f"{actor_name}使用了{action_type}！"

            # 记录战斗日志
            await CombatSystem._log_combat_action(db, dungeon_instance, result)

            return result

        except Exception as e:
            return {
                "success": False,
                "message": f"执行战斗行动失败: {str(e)}"
            }

    @staticmethod
    async def _log_combat_action(
        db: AsyncSession,
        dungeon_instance: DungeonInstance,
        action_result: Dict[str, Any]
    ):
        """记录战斗日志"""
        try:
            combat_log = CombatLog(
                dungeon_instance_id=dungeon_instance.id,
                character_id=dungeon_instance.character_id,
                action_type=action_result["action_type"],
                actor=action_result["actor"],
                target="MONSTER" if action_result["actor"] == "PLAYER" else "PLAYER",
                damage=action_result.get("damage", 0),
                is_critical=action_result.get("is_critical", False),
                damage_type="PHYSICAL",  # TODO: 根据技能类型确定
                player_hp_before=action_result["player_hp_before"],
                player_hp_after=action_result["player_hp_after"],
                monster_hp_before=action_result["monster_hp_before"],
                monster_hp_after=action_result["monster_hp_after"],
                description=action_result["description"],
                details=action_result
            )

            db.add(combat_log)
            await db.commit()

        except Exception as e:
            await db.rollback()
            # 日志记录失败不影响战斗继续
