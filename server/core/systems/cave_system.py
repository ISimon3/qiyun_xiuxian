# 洞府系统核心逻辑

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Character
from server.database.crud import GameLogCRUD
from shared.constants import CAVE_SYSTEM_CONFIG
from shared.utils import get_realm_name


class CaveSystem:
    """洞府系统管理类"""

    @staticmethod
    async def get_cave_info(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """获取洞府信息"""
        try:
            cave_level = character.cave_level
            spirit_array_level = character.spirit_gathering_array_level
            
            # 获取可用功能
            available_features = []
            for level in range(1, cave_level + 1):
                features = CAVE_SYSTEM_CONFIG["CAVE_LEVEL_FEATURES"].get(level, [])
                available_features.extend(features)
            
            # 聚灵阵通过减少修炼间隔来提升修炼频率，不影响单次修炼效率
            cultivation_interval_reduction = CaveSystem.get_cultivation_interval_reduction(spirit_array_level)
            
            return {
                "success": True,
                "cave_level": cave_level,
                "spirit_gathering_array_level": spirit_array_level,
                "max_cave_level": CAVE_SYSTEM_CONFIG["MAX_CAVE_LEVEL"],
                "max_spirit_array_level": CAVE_SYSTEM_CONFIG["MAX_SPIRIT_ARRAY_LEVEL"],
                "available_features": available_features,
                "cultivation_interval_reduction": cultivation_interval_reduction,
                "cave_upgrade_cost": CaveSystem._get_upgrade_cost("cave", cave_level + 1),
                "spirit_array_upgrade_cost": CaveSystem._get_upgrade_cost("spirit_array", spirit_array_level + 1),
                # 添加角色信息
                "cultivation_realm": character.cultivation_realm,
                "spiritual_root": character.spiritual_root,
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取洞府信息失败: {str(e)}"
            }

    @staticmethod
    async def upgrade_cave(db: AsyncSession, character: Character, upgrade_type: str) -> Dict[str, Any]:
        """升级洞府或聚灵阵"""
        try:
            if upgrade_type == "cave":
                return await CaveSystem._upgrade_cave_level(db, character)
            elif upgrade_type == "spirit_array":
                return await CaveSystem._upgrade_spirit_array(db, character)
            else:
                return {
                    "success": False,
                    "message": "无效的升级类型"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"升级失败: {str(e)}"
            }

    @staticmethod
    async def _upgrade_cave_level(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """升级洞府等级"""
        current_level = character.cave_level
        target_level = current_level + 1
        
        # 检查是否已达到最高等级
        if current_level >= CAVE_SYSTEM_CONFIG["MAX_CAVE_LEVEL"]:
            return {
                "success": False,
                "message": "洞府已达到最高等级"
            }
        
        # 获取升级成本
        upgrade_cost = CaveSystem._get_upgrade_cost("cave", target_level)
        if not upgrade_cost:
            return {
                "success": False,
                "message": "无法获取升级成本信息"
            }
        
        # 检查资源是否足够
        required_spirit_stone = upgrade_cost.get("spirit_stone", 0)
        if character.spirit_stone < required_spirit_stone:
            return {
                "success": False,
                "message": f"灵石不足，需要{required_spirit_stone}灵石"
            }
        
        # 执行升级
        character.spirit_stone -= required_spirit_stone
        character.cave_level = target_level
        
        # 记录日志
        await GameLogCRUD.create_log(
            db,
            character.id,
            "CAVE_UPGRADE",
            f"洞府升级成功！等级提升至{target_level}级",
            {
                "old_level": current_level,
                "new_level": target_level,
                "cost_spirit_stone": required_spirit_stone,
                "remaining_spirit_stone": character.spirit_stone
            }
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"洞府升级成功！等级提升至{target_level}级",
            "old_level": current_level,
            "new_level": target_level,
            "cost_spirit_stone": required_spirit_stone,
            "cost_materials": {}
        }

    @staticmethod
    async def _upgrade_spirit_array(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """升级聚灵阵"""
        current_level = character.spirit_gathering_array_level
        target_level = current_level + 1
        
        # 检查洞府等级是否足够（需要2级洞府才能建造聚灵阵）
        if character.cave_level < 2:
            return {
                "success": False,
                "message": "洞府等级不足，需要2级洞府才能建造聚灵阵"
            }
        
        # 检查是否已达到最高等级
        if current_level >= CAVE_SYSTEM_CONFIG["MAX_SPIRIT_ARRAY_LEVEL"]:
            return {
                "success": False,
                "message": "聚灵阵已达到最高等级"
            }
        
        # 获取升级成本
        upgrade_cost = CaveSystem._get_upgrade_cost("spirit_array", target_level)
        if not upgrade_cost:
            return {
                "success": False,
                "message": "无法获取升级成本信息"
            }
        
        # 检查资源是否足够
        required_spirit_stone = upgrade_cost.get("spirit_stone", 0)
        if character.spirit_stone < required_spirit_stone:
            return {
                "success": False,
                "message": f"灵石不足，需要{required_spirit_stone}灵石"
            }
        
        # 执行升级
        character.spirit_stone -= required_spirit_stone
        character.spirit_gathering_array_level = target_level
        
        # 记录日志
        await GameLogCRUD.create_log(
            db,
            character.id,
            "SPIRIT_ARRAY_UPGRADE",
            f"聚灵阵升级成功！等级提升至{target_level}级",
            {
                "old_level": current_level,
                "new_level": target_level,
                "cost_spirit_stone": required_spirit_stone,
                "remaining_spirit_stone": character.spirit_stone,
                "new_interval_reduction": CAVE_SYSTEM_CONFIG["SPIRIT_GATHERING_ARRAY"]["LEVEL_BENEFITS"].get(
                    target_level, {}
                ).get("cultivation_interval_reduction", 0.0)
            }
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"聚灵阵升级成功！等级提升至{target_level}级",
            "old_level": current_level,
            "new_level": target_level,
            "cost_spirit_stone": required_spirit_stone,
            "cost_materials": {}
        }

    @staticmethod
    def _get_upgrade_cost(upgrade_type: str, target_level: int) -> Dict[str, Any]:
        """获取升级成本"""
        if upgrade_type == "cave":
            return CAVE_SYSTEM_CONFIG["CAVE_UPGRADE_COSTS"].get(target_level)
        elif upgrade_type == "spirit_array":
            return CAVE_SYSTEM_CONFIG["SPIRIT_ARRAY_UPGRADE_COSTS"].get(target_level)
        return None

    @staticmethod
    def get_cultivation_interval_reduction(spirit_array_level: int) -> float:
        """获取聚灵阵修炼间隔减少率"""
        if "SPIRIT_GATHERING_ARRAY" in CAVE_SYSTEM_CONFIG:
            array_benefits = CAVE_SYSTEM_CONFIG["SPIRIT_GATHERING_ARRAY"]["LEVEL_BENEFITS"]
            return array_benefits.get(spirit_array_level, {}).get("cultivation_interval_reduction", 0.0)
        return 0.0

    @staticmethod
    async def apply_cycle_rewards(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """应用洞府系统的周期性奖励"""
        try:
            rewards = {
                "gold_gained": 0,
                "spirit_stone_gained": 0,
                "sources": []
            }

            # 洞府等级奖励 - 每周期获得金币
            cave_level = character.cave_level
            if cave_level > 0 and "CAVE_UPGRADE" in CAVE_SYSTEM_CONFIG:
                cave_benefits = CAVE_SYSTEM_CONFIG["CAVE_UPGRADE"]["LEVEL_BENEFITS"]
                if cave_level in cave_benefits:
                    gold_range = cave_benefits[cave_level].get("gold_per_cycle", (0, 0))
                    if gold_range[1] > 0:
                        import random
                        gold_gained = random.randint(gold_range[0], gold_range[1])
                        character.gold += gold_gained
                        rewards["gold_gained"] += gold_gained
                        rewards["sources"].append(f"洞府{cave_level}级")

            # 聚灵阵奖励 - 每周期获得灵石
            spirit_array_level = character.spirit_gathering_array_level
            if spirit_array_level > 0 and "SPIRIT_GATHERING_ARRAY" in CAVE_SYSTEM_CONFIG:
                array_benefits = CAVE_SYSTEM_CONFIG["SPIRIT_GATHERING_ARRAY"]["LEVEL_BENEFITS"]
                if spirit_array_level in array_benefits:
                    stone_range = array_benefits[spirit_array_level].get("spirit_stone_per_cycle", (0, 0))
                    if stone_range[1] > 0:
                        import random
                        stone_gained = random.randint(stone_range[0], stone_range[1])
                        character.spirit_stone += stone_gained
                        rewards["spirit_stone_gained"] += stone_gained
                        rewards["sources"].append(f"聚灵阵{spirit_array_level}级")

            # 如果有奖励，记录日志
            if rewards["gold_gained"] > 0 or rewards["spirit_stone_gained"] > 0:
                log_message = "洞府周期奖励："
                reward_parts = []
                if rewards["gold_gained"] > 0:
                    reward_parts.append(f"金币+{rewards['gold_gained']}")
                if rewards["spirit_stone_gained"] > 0:
                    reward_parts.append(f"灵石+{rewards['spirit_stone_gained']}")

                log_message += "，".join(reward_parts)
                log_message += f"（来源：{', '.join(rewards['sources'])}）"

                await GameLogCRUD.create_log(
                    db,
                    character.id,
                    "CAVE_CYCLE_REWARD",
                    log_message,
                    rewards
                )

            return rewards

        except Exception as e:
            print(f"❌ 应用洞府周期奖励失败: {e}")
            return {
                "gold_gained": 0,
                "spirit_stone_gained": 0,
                "sources": []
            }
