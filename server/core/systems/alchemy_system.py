# 炼丹系统核心逻辑

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_

from server.database.models import Character, AlchemyRecipe, AlchemySession, Item, InventoryItem
from server.database.crud import GameLogCRUD, InventoryCRUD
from shared.constants import ALCHEMY_SYSTEM_CONFIG, ALCHEMY_RECIPES, ALCHEMY_MATERIALS
from shared.schemas import AlchemyRecipeInfo, AlchemySessionInfo, AlchemyInfo


class AlchemySystem:
    """炼丹系统管理类"""

    @staticmethod
    async def get_alchemy_info(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """获取炼丹系统信息"""
        try:
            # 初始化丹方数据（如果不存在）
            await AlchemySystem._initialize_recipes(db)

            # 获取活跃的炼丹会话
            active_sessions = await AlchemySystem._get_active_sessions(db, character)

            # 获取可用丹方
            available_recipes = await AlchemySystem._get_available_recipes(db, character)

            # 获取材料库存
            materials_inventory = await AlchemySystem._get_materials_inventory(db, character)

            return {
                "success": True,
                "alchemy_level": character.alchemy_level,
                "alchemy_exp": character.alchemy_exp,
                "max_concurrent_sessions": ALCHEMY_SYSTEM_CONFIG["MAX_CONCURRENT_SESSIONS"],
                "active_sessions": active_sessions,
                "available_recipes": available_recipes,
                "materials_inventory": materials_inventory
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"获取炼丹信息失败: {str(e)}"
            }

    @staticmethod
    async def start_alchemy(db: AsyncSession, character: Character, recipe_id: str) -> Dict[str, Any]:
        """开始炼丹"""
        try:
            # 检查是否达到最大并发数
            active_count = await AlchemySystem._get_active_session_count(db, character)
            if active_count >= ALCHEMY_SYSTEM_CONFIG["MAX_CONCURRENT_SESSIONS"]:
                return {
                    "success": False,
                    "message": f"同时炼制数量已达上限({ALCHEMY_SYSTEM_CONFIG['MAX_CONCURRENT_SESSIONS']})"
                }

            # 获取丹方信息
            recipe = await AlchemySystem._get_recipe(db, recipe_id)
            if not recipe:
                return {"success": False, "message": "丹方不存在"}

            # 检查境界要求
            if character.cultivation_realm < recipe.required_realm:
                return {
                    "success": False,
                    "message": f"境界不足，需要{recipe.required_realm}级境界"
                }

            # 检查炼丹等级要求
            if character.alchemy_level < recipe.required_alchemy_level:
                return {
                    "success": False,
                    "message": f"炼丹等级不足，需要{recipe.required_alchemy_level}级"
                }

            # 检查材料是否充足
            materials_check = await AlchemySystem._check_materials(db, character, recipe.materials)
            if not materials_check["sufficient"]:
                return {
                    "success": False,
                    "message": "材料不足",
                    "missing_materials": materials_check["missing"]
                }

            # 消耗材料
            await AlchemySystem._consume_materials(db, character, recipe.materials)

            # 计算炼制时间和成功率
            alchemy_time = AlchemySystem._calculate_alchemy_time(character, recipe)
            success_rate = AlchemySystem._calculate_success_rate(character, recipe)

            # 创建炼丹会话
            now = datetime.now()
            finish_time = now + timedelta(minutes=alchemy_time)

            session = AlchemySession(
                character_id=character.id,
                recipe_id=recipe_id,
                quality=recipe.quality,
                started_at=now,
                finish_at=finish_time,
                success_rate=success_rate,
                result_item_name=recipe.result_item_name
            )

            db.add(session)
            await db.commit()

            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "ALCHEMY_START",
                f"开始炼制{recipe.name}",
                {
                    "recipe_id": recipe_id,
                    "recipe_name": recipe.name,
                    "finish_time": finish_time.isoformat(),
                    "success_rate": success_rate
                }
            )

            # 返回会话信息
            session_info = await AlchemySystem._get_session_info(db, session)

            return {
                "success": True,
                "message": f"开始炼制{recipe.name}",
                "session_info": session_info
            }

        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"开始炼丹失败: {str(e)}"
            }

    @staticmethod
    async def collect_alchemy_result(db: AsyncSession, character: Character, session_id: int) -> Dict[str, Any]:
        """收取炼丹结果"""
        try:
            # 获取炼丹会话
            result = await db.execute(
                select(AlchemySession)
                .where(and_(
                    AlchemySession.id == session_id,
                    AlchemySession.character_id == character.id
                ))
            )
            session = result.scalar_one_or_none()

            if not session:
                return {"success": False, "message": "炼丹会话不存在"}

            if session.status == "COMPLETED":
                return {"success": False, "message": "已经收取过了"}

            # 检查是否完成
            now = datetime.now()
            if now < session.finish_at:
                remaining_seconds = int((session.finish_at - now).total_seconds())
                return {
                    "success": False,
                    "message": f"炼制尚未完成，还需{remaining_seconds}秒"
                }

            # 判断炼制结果
            is_success = random.random() < session.success_rate
            exp_gained = 10 + (session.quality == "RARE") * 5 + (session.quality == "EPIC") * 10

            if is_success:
                # 炼制成功，判断品质提升
                final_quality = AlchemySystem._determine_final_quality(session.quality)

                # 添加物品到背包
                await InventoryCRUD.add_item_to_inventory(
                    db, character.id, session.result_item_name, 1, final_quality
                )

                session.status = "COMPLETED"
                session.completed_at = now
                session.result_quality = final_quality
                session.exp_gained = exp_gained

                # 增加炼丹经验
                character.alchemy_exp += exp_gained

                # 检查是否升级
                level_up_message = ""
                if AlchemySystem._check_level_up(character):
                    character.alchemy_level += 1
                    level_up_message = f"，炼丹等级提升至{character.alchemy_level}级！"

                message = f"炼制成功！获得{final_quality}品质的{session.result_item_name}{level_up_message}"

                # 记录日志
                await GameLogCRUD.create_log(
                    db,
                    character.id,
                    "ALCHEMY_SUCCESS",
                    message,
                    {
                        "session_id": session_id,
                        "result_item": session.result_item_name,
                        "result_quality": final_quality,
                        "exp_gained": exp_gained
                    }
                )

            else:
                # 炼制失败
                session.status = "FAILED"
                session.completed_at = now
                session.exp_gained = exp_gained // 2  # 失败也给一半经验

                character.alchemy_exp += session.exp_gained

                message = f"炼制失败，获得{session.exp_gained}点炼丹经验"

                # 记录日志
                await GameLogCRUD.create_log(
                    db,
                    character.id,
                    "ALCHEMY_FAILED",
                    message,
                    {
                        "session_id": session_id,
                        "exp_gained": session.exp_gained
                    }
                )

            await db.commit()

            return {
                "success": True,
                "message": message,
                "result_item": session.result_item_name if is_success else None,
                "result_quality": session.result_quality if is_success else None,
                "exp_gained": session.exp_gained
            }

        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"收取炼丹结果失败: {str(e)}"
            }

    @staticmethod
    async def _initialize_recipes(db: AsyncSession):
        """初始化丹方数据"""
        # 检查是否已初始化
        result = await db.execute(select(AlchemyRecipe))
        existing_recipes = result.scalars().all()

        if len(existing_recipes) > 0:
            return

        # 添加基础丹方
        for recipe_id, recipe_data in ALCHEMY_RECIPES.items():
            recipe = AlchemyRecipe(
                recipe_id=recipe_id,
                name=recipe_data["name"],
                description=recipe_data["description"],
                quality=recipe_data["quality"],
                required_realm=recipe_data["required_realm"],
                required_alchemy_level=recipe_data.get("required_alchemy_level", 1),
                materials=recipe_data["materials"],
                result_item_name=recipe_data["result_item"],
                base_time_minutes=recipe_data["base_time_minutes"],
                base_success_rate=ALCHEMY_SYSTEM_CONFIG["BASE_SUCCESS_RATE"],
                effects=recipe_data.get("effects", {})
            )
            db.add(recipe)

        await db.commit()

    @staticmethod
    async def _get_active_sessions(db: AsyncSession, character: Character) -> List[Dict[str, Any]]:
        """获取活跃的炼丹会话"""
        result = await db.execute(
            select(AlchemySession)
            .where(and_(
                AlchemySession.character_id == character.id,
                AlchemySession.status == "IN_PROGRESS"
            ))
            .order_by(AlchemySession.started_at)
        )
        sessions = result.scalars().all()

        sessions_info = []
        for session in sessions:
            session_info = await AlchemySystem._get_session_info(db, session)
            sessions_info.append(session_info)

        return sessions_info

    @staticmethod
    async def _get_session_info(db: AsyncSession, session: AlchemySession) -> Dict[str, Any]:
        """获取会话详细信息"""
        # 获取丹方信息
        recipe = await AlchemySystem._get_recipe(db, session.recipe_id)
        recipe_name = recipe.name if recipe else session.recipe_id

        # 计算剩余时间和进度
        now = datetime.now()
        if session.status == "IN_PROGRESS":
            if now >= session.finish_at:
                remaining_time = 0
                progress = 1.0
            else:
                remaining_time = int((session.finish_at - session.started_at).total_seconds())
                elapsed_time = int((now - session.started_at).total_seconds())
                total_time = int((session.finish_at - session.started_at).total_seconds())
                progress = elapsed_time / total_time if total_time > 0 else 0.0
        else:
            remaining_time = 0
            progress = 1.0

        return {
            "id": session.id,
            "recipe_id": session.recipe_id,
            "recipe_name": recipe_name,
            "status": session.status,
            "quality": session.quality,
            "started_at": session.started_at,
            "finish_at": session.finish_at,
            "completed_at": session.completed_at,
            "success_rate": session.success_rate,
            "result_item_name": session.result_item_name,
            "result_quality": session.result_quality,
            "exp_gained": session.exp_gained,
            "remaining_time_seconds": remaining_time,
            "progress": progress
        }

    @staticmethod
    async def _get_available_recipes(db: AsyncSession, character: Character) -> List[Dict[str, Any]]:
        """获取可用丹方"""
        result = await db.execute(
            select(AlchemyRecipe)
            .where(and_(
                AlchemyRecipe.required_realm <= character.cultivation_realm,
                AlchemyRecipe.required_alchemy_level <= character.alchemy_level
            ))
            .order_by(AlchemyRecipe.required_realm, AlchemyRecipe.required_alchemy_level)
        )
        recipes = result.scalars().all()

        recipes_info = []
        for recipe in recipes:
            # 检查材料是否充足
            materials_check = await AlchemySystem._check_materials(db, character, recipe.materials)

            recipe_info = {
                "id": recipe.recipe_id,
                "name": recipe.name,
                "description": recipe.description,
                "quality": recipe.quality,
                "required_realm": recipe.required_realm,
                "required_alchemy_level": recipe.required_alchemy_level,
                "materials": recipe.materials,
                "result_item_name": recipe.result_item_name,
                "base_time_minutes": recipe.base_time_minutes,
                "base_success_rate": recipe.base_success_rate,
                "effects": recipe.effects,
                "can_craft": materials_check["sufficient"],
                "missing_materials": materials_check["missing"] if not materials_check["sufficient"] else None
            }
            recipes_info.append(recipe_info)

        return recipes_info

    @staticmethod
    async def _get_materials_inventory(db: AsyncSession, character: Character) -> Dict[str, int]:
        """获取材料库存"""
        # 获取所有材料类型的物品
        result = await db.execute(
            select(InventoryItem, Item)
            .join(Item, InventoryItem.item_id == Item.id)
            .where(and_(
                InventoryItem.character_id == character.id,
                Item.item_type == "MATERIAL"
            ))
        )

        materials = {}
        for inventory_item, item in result:
            materials[item.name] = inventory_item.quantity

        return materials

    @staticmethod
    async def _get_recipe(db: AsyncSession, recipe_id: str) -> Optional[AlchemyRecipe]:
        """获取丹方"""
        result = await db.execute(
            select(AlchemyRecipe)
            .where(AlchemyRecipe.recipe_id == recipe_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_active_session_count(db: AsyncSession, character: Character) -> int:
        """获取活跃会话数量"""
        result = await db.execute(
            select(AlchemySession)
            .where(and_(
                AlchemySession.character_id == character.id,
                AlchemySession.status == "IN_PROGRESS"
            ))
        )
        return len(result.scalars().all())

    @staticmethod
    async def _check_materials(db: AsyncSession, character: Character, required_materials: Dict[str, int]) -> Dict[str, Any]:
        """检查材料是否充足"""
        materials_inventory = await AlchemySystem._get_materials_inventory(db, character)

        missing = {}
        for material_name, required_amount in required_materials.items():
            current_amount = materials_inventory.get(material_name, 0)
            if current_amount < required_amount:
                missing[material_name] = required_amount - current_amount

        return {
            "sufficient": len(missing) == 0,
            "missing": missing
        }

    @staticmethod
    async def _consume_materials(db: AsyncSession, character: Character, required_materials: Dict[str, int]):
        """消耗材料"""
        for material_name, required_amount in required_materials.items():
            # 查找材料物品
            result = await db.execute(
                select(InventoryItem, Item)
                .join(Item, InventoryItem.item_id == Item.id)
                .where(and_(
                    InventoryItem.character_id == character.id,
                    Item.name == material_name,
                    Item.item_type == "MATERIAL"
                ))
            )

            inventory_item, item = result.first()
            if inventory_item:
                inventory_item.quantity -= required_amount
                if inventory_item.quantity <= 0:
                    await db.delete(inventory_item)

    @staticmethod
    def _calculate_alchemy_time(character: Character, recipe: AlchemyRecipe) -> int:
        """计算炼制时间"""
        base_time = recipe.base_time_minutes

        # 洞府丹房加速（如果洞府等级>=3）
        if character.cave_level >= 3:
            # 每级洞府减少5%时间
            time_reduction = (character.cave_level - 2) * 0.05
            base_time = base_time * (1 - min(time_reduction, 0.5))  # 最多减少50%

        # 炼丹等级加速
        level_bonus = (character.alchemy_level - 1) * 0.02  # 每级减少2%时间
        base_time = base_time * (1 - min(level_bonus, 0.3))  # 最多减少30%

        return max(int(base_time), 5)  # 最少5分钟

    @staticmethod
    def _calculate_success_rate(character: Character, recipe: AlchemyRecipe) -> float:
        """计算成功率"""
        base_rate = recipe.base_success_rate

        # 境界加成
        realm_bonus = character.cultivation_realm * ALCHEMY_SYSTEM_CONFIG["SUCCESS_RATE_MODIFIERS"]["realm_bonus"]

        # 气运加成
        luck_bonus = (character.luck_value - 50) * ALCHEMY_SYSTEM_CONFIG["SUCCESS_RATE_MODIFIERS"]["luck_bonus"]

        # 洞府丹房加成
        cave_bonus = 0
        if character.cave_level >= 3:
            cave_bonus = (character.cave_level - 2) * ALCHEMY_SYSTEM_CONFIG["SUCCESS_RATE_MODIFIERS"]["cave_bonus"]

        # 炼丹等级加成
        alchemy_level_bonus = (character.alchemy_level - 1) * 0.01  # 每级+1%成功率

        final_rate = base_rate + realm_bonus + luck_bonus + cave_bonus + alchemy_level_bonus
        return min(max(final_rate, 0.1), 0.95)  # 限制在10%-95%之间

    @staticmethod
    def _determine_final_quality(base_quality: str) -> str:
        """确定最终品质（可能提升）"""
        quality_levels = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"]

        if base_quality not in quality_levels:
            return base_quality

        current_index = quality_levels.index(base_quality)

        # 检查是否品质提升
        for i in range(len(quality_levels) - 1, current_index, -1):
            upgrade_key = f"{quality_levels[i-1]}_TO_{quality_levels[i]}"
            upgrade_chance = ALCHEMY_SYSTEM_CONFIG["QUALITY_UPGRADE_CHANCE"].get(upgrade_key, 0)

            if random.random() < upgrade_chance:
                return quality_levels[i]

        return base_quality

    @staticmethod
    def _check_level_up(character: Character) -> bool:
        """检查是否可以升级"""
        # 简单的升级公式：每级需要 level * 100 经验
        required_exp = character.alchemy_level * 100
        return character.alchemy_exp >= required_exp

    @staticmethod
    async def update_alchemy_sessions(db: AsyncSession):
        """更新所有炼丹会话状态（由游戏循环调用）"""
        try:
            now = datetime.now()

            # 查找所有已完成但未处理的会话
            result = await db.execute(
                select(AlchemySession)
                .where(and_(
                    AlchemySession.status == "IN_PROGRESS",
                    AlchemySession.finish_at <= now
                ))
            )

            completed_sessions = result.scalars().all()

            for session in completed_sessions:
                # 这里只更新状态，实际收取由玩家手动触发
                # 可以发送通知给玩家
                pass

        except Exception as e:
            print(f"更新炼丹会话状态失败: {e}")

    @staticmethod
    async def use_pill(db: AsyncSession, character: Character, pill_name: str, effects: Dict[str, Any]) -> Dict[str, Any]:
        """使用丹药"""
        try:
            # 检查背包中是否有该丹药
            result = await db.execute(
                select(InventoryItem, Item)
                .join(Item, InventoryItem.item_id == Item.id)
                .where(and_(
                    InventoryItem.character_id == character.id,
                    Item.name == pill_name,
                    Item.item_type == "PILL"
                ))
            )

            inventory_item, item = result.first()
            if not inventory_item or inventory_item.quantity <= 0:
                return {"success": False, "message": f"没有{pill_name}"}

            # 应用丹药效果
            effect_messages = []

            for effect_type, value in effects.items():
                if effect_type == "HP_RESTORE":
                    # 恢复生命值（这里只是示例，实际需要战斗系统支持）
                    effect_messages.append(f"恢复{value}点生命值")

                elif effect_type == "CULTIVATION_EXP":
                    character.cultivation_exp += value
                    effect_messages.append(f"获得{value}点修炼经验")

                elif effect_type == "PHYSICAL_ATTACK_PERMANENT":
                    character.physical_attack_training += value
                    effect_messages.append(f"物理攻击永久+{value}")

                elif effect_type == "MAGIC_ATTACK_PERMANENT":
                    character.magic_attack_training += value
                    effect_messages.append(f"法术攻击永久+{value}")

                elif effect_type == "PHYSICAL_DEFENSE_PERMANENT":
                    character.physical_defense_training += value
                    effect_messages.append(f"物理防御永久+{value}")

                elif effect_type == "MAGIC_DEFENSE_PERMANENT":
                    character.magic_defense_training += value
                    effect_messages.append(f"法术防御永久+{value}")

                elif effect_type == "LUCK_VALUE":
                    character.luck_value = min(character.luck_value + value, 100)
                    effect_messages.append(f"气运值+{value}")

            # 消耗丹药
            inventory_item.quantity -= 1
            if inventory_item.quantity <= 0:
                await db.delete(inventory_item)

            await db.commit()

            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "USE_PILL",
                f"使用{pill_name}，{', '.join(effect_messages)}",
                {"pill_name": pill_name, "effects": effects}
            )

            return {
                "success": True,
                "message": f"使用{pill_name}成功，{', '.join(effect_messages)}"
            }

        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"使用丹药失败: {str(e)}"
            }
