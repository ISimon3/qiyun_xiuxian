# 灵田系统核心逻辑

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_

from server.database.models import Character, FarmPlot, Item, InventoryItem
from server.database.crud import GameLogCRUD, InventoryCRUD
from shared.constants import FARM_SYSTEM_CONFIG
from shared.schemas import FarmPlotInfo, FarmInfo


class FarmSystem:
    """灵田系统管理类"""

    @staticmethod
    async def get_farm_info(db: AsyncSession, character: Character) -> Dict[str, Any]:
        """获取灵田信息"""
        try:
            # 初始化灵田（如果不存在）
            await FarmSystem._initialize_farm_plots(db, character)

            # 获取所有地块
            result = await db.execute(
                select(FarmPlot)
                .where(FarmPlot.character_id == character.id)
                .order_by(FarmPlot.plot_index)
            )
            plots = result.scalars().all()

            # 更新地块状态
            plots_info = []
            for plot in plots:
                plot_info = await FarmSystem._get_plot_info(db, plot)
                plots_info.append(plot_info)

            # 获取可用种子
            available_seeds = await FarmSystem._get_available_seeds(db, character)

            return {
                "success": True,
                "total_plots": FARM_SYSTEM_CONFIG["TOTAL_PLOTS"],
                "unlocked_plots": len([p for p in plots if p.is_unlocked]),
                "plots": plots_info,
                "available_seeds": available_seeds
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"获取灵田信息失败: {str(e)}"
            }

    @staticmethod
    async def plant_seed(db: AsyncSession, character: Character, plot_index: int, seed_item_id: int) -> Dict[str, Any]:
        """种植种子"""
        try:
            # 获取地块
            result = await db.execute(
                select(FarmPlot)
                .where(and_(
                    FarmPlot.character_id == character.id,
                    FarmPlot.plot_index == plot_index
                ))
            )
            plot = result.scalar_one_or_none()

            if not plot:
                return {"success": False, "message": "地块不存在"}

            if not plot.is_unlocked:
                return {"success": False, "message": "地块未解锁"}

            if plot.seed_item_id is not None:
                return {"success": False, "message": "地块已有作物"}

            # 检查种子是否存在
            seed_item = await FarmSystem._get_seed_item(db, character, seed_item_id)
            if not seed_item:
                return {"success": False, "message": "种子不足"}

            # 获取种子物品信息
            seed_result = await db.execute(select(Item).where(Item.id == seed_item_id))
            seed_info = seed_result.scalar_one_or_none()
            if not seed_info:
                return {"success": False, "message": "种子信息不存在"}

            # 获取种子配置
            seed_config = FARM_SYSTEM_CONFIG["SEED_CONFIG"].get(seed_info.name)
            if not seed_config:
                return {"success": False, "message": "无效的种子类型"}

            # 计算成长时间（受地块类型和聚灵阵影响）
            plot_config = FARM_SYSTEM_CONFIG["PLOT_TYPES"][plot.plot_type]
            growth_hours = seed_config["growth_time_hours"]

            # 聚灵阵加速效果
            from server.core.systems.cave_system import CaveSystem
            spirit_bonus = CaveSystem.get_cultivation_speed_bonus(character.spirit_gathering_array_level)
            growth_hours = growth_hours / (plot_config["growth_speed_multiplier"] * spirit_bonus)

            # 种植
            now = datetime.now()
            harvest_time = now + timedelta(hours=growth_hours)

            plot.seed_item_id = seed_item_id
            plot.planted_at = now
            plot.harvest_at = harvest_time
            plot.growth_stage = 1  # 发芽阶段
            plot.is_ready = False
            plot.is_withered = False
            plot.has_pest = False
            plot.has_weed = False
            plot.mutation_chance = 0.0  # 移除变异系统

            # 消耗种子
            seed_item.quantity -= 1
            if seed_item.quantity <= 0:
                await db.delete(seed_item)

            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "FARM_PLANT",
                f"在{plot_config['name']}种植了{seed_info.name}",
                {
                    "plot_index": plot_index,
                    "seed_name": seed_info.name,
                    "harvest_time": harvest_time.isoformat()
                }
            )

            await db.commit()

            plot_info = await FarmSystem._get_plot_info(db, plot)

            return {
                "success": True,
                "message": f"成功种植{seed_info.name}",
                "plot_info": plot_info
            }

        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"种植失败: {str(e)}"
            }

    @staticmethod
    async def harvest_plot(db: AsyncSession, character: Character, plot_index: int) -> Dict[str, Any]:
        """收获地块"""
        try:
            # 获取地块
            result = await db.execute(
                select(FarmPlot)
                .where(and_(
                    FarmPlot.character_id == character.id,
                    FarmPlot.plot_index == plot_index
                ))
            )
            plot = result.scalar_one_or_none()

            if not plot:
                return {"success": False, "message": "地块不存在"}

            if plot.seed_item_id is None:
                return {"success": False, "message": "地块没有作物"}

            # 更新地块状态
            await FarmSystem._update_plot_status(db, plot)

            if not plot.is_ready:
                return {"success": False, "message": "作物尚未成熟"}

            # 获取种子信息
            seed_result = await db.execute(select(Item).where(Item.id == plot.seed_item_id))
            seed_item = seed_result.scalar_one_or_none()

            if not seed_item:
                return {"success": False, "message": "种子信息丢失"}

            seed_config = FARM_SYSTEM_CONFIG["SEED_CONFIG"].get(seed_item.name)
            if not seed_config:
                return {"success": False, "message": "无效的种子配置"}

            # 计算收获
            plot_config = FARM_SYSTEM_CONFIG["PLOT_TYPES"][plot.plot_type]
            base_yield = random.randint(seed_config["yield_min"], seed_config["yield_max"])
            final_yield = int(base_yield * plot_config["yield_multiplier"])

            # 普通收获（移除变异系统）
            harvested_items = [{
                "name": seed_config["result_item"],
                "quantity": final_yield,
                "is_mutation": False
            }]

            # 添加物品到背包
            for item_info in harvested_items:
                await FarmSystem._add_item_to_inventory(db, character, item_info["name"], item_info["quantity"])

            # 清理地块
            plot.seed_item_id = None
            plot.planted_at = None
            plot.harvest_at = None
            plot.growth_stage = 0
            plot.is_ready = False
            plot.is_withered = False
            plot.has_pest = False
            plot.has_weed = False
            plot.mutation_chance = 0.0

            # 记录日志
            item_descriptions = [f"{item['quantity']}个{item['name']}" for item in harvested_items]
            log_message = f"收获了{', '.join(item_descriptions)}"

            await GameLogCRUD.create_log(
                db,
                character.id,
                "FARM_HARVEST",
                log_message,
                {
                    "plot_index": plot_index,
                    "harvested_items": harvested_items
                }
            )

            await db.commit()

            plot_info = await FarmSystem._get_plot_info(db, plot)

            return {
                "success": True,
                "message": log_message,
                "harvested_items": harvested_items,
                "plot_info": plot_info
            }

        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"收获失败: {str(e)}"
            }

    @staticmethod
    async def unlock_plot(db: AsyncSession, character: Character, plot_index: int) -> Dict[str, Any]:
        """解锁地块"""
        try:
            # 检查地块索引
            if plot_index >= FARM_SYSTEM_CONFIG["TOTAL_PLOTS"]:
                return {"success": False, "message": "无效的地块编号"}

            # 获取地块
            result = await db.execute(
                select(FarmPlot)
                .where(and_(
                    FarmPlot.character_id == character.id,
                    FarmPlot.plot_index == plot_index
                ))
            )
            plot = result.scalar_one_or_none()

            if not plot:
                return {"success": False, "message": "地块不存在"}

            if plot.is_unlocked:
                return {"success": False, "message": "地块已解锁"}

            # 检查解锁条件
            unlock_req = FARM_SYSTEM_CONFIG["PLOT_UNLOCK_REQUIREMENTS"].get(plot_index)
            if unlock_req:
                if character.cave_level < unlock_req["cave_level"]:
                    return {
                        "success": False,
                        "message": f"需要{unlock_req['cave_level']}级洞府才能解锁此地块"
                    }

                if character.gold < unlock_req["cost"]:
                    return {
                        "success": False,
                        "message": f"金币不足，需要{unlock_req['cost']}金币"
                    }

                # 消耗金币
                character.gold -= unlock_req["cost"]
                cost = unlock_req["cost"]
            else:
                cost = 0

            # 解锁地块
            plot.is_unlocked = True

            # 记录日志
            await GameLogCRUD.create_log(
                db,
                character.id,
                "FARM_UNLOCK",
                f"解锁了第{plot_index + 1}块灵田",
                {
                    "plot_index": plot_index,
                    "cost": cost
                }
            )

            await db.commit()

            plot_info = await FarmSystem._get_plot_info(db, plot)

            return {
                "success": True,
                "message": f"成功解锁第{plot_index + 1}块灵田",
                "cost": cost,
                "plot_info": plot_info
            }

        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"解锁失败: {str(e)}"
            }

    @staticmethod
    async def _initialize_farm_plots(db: AsyncSession, character: Character):
        """初始化灵田地块"""
        # 检查是否已初始化
        result = await db.execute(
            select(FarmPlot)
            .where(FarmPlot.character_id == character.id)
        )
        existing_plots = result.scalars().all()

        if len(existing_plots) >= FARM_SYSTEM_CONFIG["TOTAL_PLOTS"]:
            return

        # 创建缺失的地块
        existing_indices = {plot.plot_index for plot in existing_plots}

        for i in range(FARM_SYSTEM_CONFIG["TOTAL_PLOTS"]):
            if i not in existing_indices:
                plot = FarmPlot(
                    character_id=character.id,
                    plot_index=i,
                    plot_type="normal",
                    is_unlocked=(i < FARM_SYSTEM_CONFIG["INITIAL_UNLOCKED_PLOTS"])
                )
                db.add(plot)

        await db.commit()

    @staticmethod
    async def _get_plot_info(db: AsyncSession, plot: FarmPlot) -> Dict[str, Any]:
        """获取地块详细信息"""
        # 更新地块状态
        await FarmSystem._update_plot_status(db, plot)

        plot_info = {
            "id": plot.id,
            "plot_index": plot.plot_index,
            "plot_type": plot.plot_type,
            "is_unlocked": plot.is_unlocked,
            "seed_item_id": plot.seed_item_id,
            "seed_name": None,
            "planted_at": plot.planted_at,
            "harvest_at": plot.harvest_at,
            "growth_stage": plot.growth_stage,
            "growth_stage_name": FARM_SYSTEM_CONFIG["GROWTH_STAGES"].get(plot.growth_stage, "未知"),
            "is_ready": plot.is_ready,
            "is_withered": plot.is_withered,
            "remaining_time_seconds": 0,
            "total_growth_time_seconds": 0,
            "growth_progress": 0.0
        }

        # 如果有种子，获取种子名称和时间信息
        if plot.seed_item_id:
            seed_result = await db.execute(select(Item).where(Item.id == plot.seed_item_id))
            seed_item = seed_result.scalar_one_or_none()
            if seed_item:
                plot_info["seed_name"] = seed_item.name

                if plot.planted_at and plot.harvest_at:
                    now = datetime.now()
                    total_time = (plot.harvest_at - plot.planted_at).total_seconds()
                    remaining_time = max(0, (plot.harvest_at - now).total_seconds())

                    plot_info["remaining_time_seconds"] = int(remaining_time)
                    plot_info["total_growth_time_seconds"] = int(total_time)
                    plot_info["growth_progress"] = min(1.0, (total_time - remaining_time) / total_time) if total_time > 0 else 0.0

        return plot_info

    @staticmethod
    async def _update_plot_status(db: AsyncSession, plot: FarmPlot):
        """更新地块状态"""
        if not plot.seed_item_id or not plot.harvest_at:
            return

        now = datetime.now()

        # 检查是否成熟
        if now >= plot.harvest_at:
            plot.is_ready = True
            plot.growth_stage = 4  # 成熟

            # 检查是否枯萎（成熟后每小时计算一次）
            if not plot.is_withered:
                overtime_hours = (now - plot.harvest_at).total_seconds() / 3600
                # 每完整小时计算一次枯萎概率
                hours_passed = int(overtime_hours)
                if hours_passed > 0:
                    wither_chance = FARM_SYSTEM_CONFIG["EVENT_CHANCES"]["wither_chance"]
                    # 每小时都有枯萎概率
                    for _ in range(hours_passed):
                        if random.random() < wither_chance:
                            plot.is_withered = True
                            break
        else:
            # 计算成长阶段
            if plot.planted_at:
                total_time = (plot.harvest_at - plot.planted_at).total_seconds()
                elapsed_time = (now - plot.planted_at).total_seconds()
                progress = elapsed_time / total_time

                if progress < 0.25:
                    plot.growth_stage = 1  # 发芽
                elif progress < 0.5:
                    plot.growth_stage = 2  # 幼苗
                elif progress < 0.75:
                    plot.growth_stage = 3  # 成长
                else:
                    plot.growth_stage = 4  # 接近成熟

        # 移除虫害和杂草的随机事件检查

    @staticmethod
    async def _get_available_seeds(db: AsyncSession, character: Character) -> List[Dict[str, Any]]:
        """获取可用种子列表"""
        # 获取背包中的种子
        result = await db.execute(
            select(InventoryItem, Item)
            .join(Item, InventoryItem.item_id == Item.id)
            .where(and_(
                InventoryItem.character_id == character.id,
                Item.item_type == "seed",
                InventoryItem.quantity > 0
            ))
        )

        seeds = []
        for inventory_item, item in result:
            seed_config = FARM_SYSTEM_CONFIG["SEED_CONFIG"].get(item.name, {})
            seeds.append({
                "item_id": item.id,
                "name": item.name,
                "quantity": inventory_item.quantity,
                "growth_time_hours": seed_config.get("growth_time_hours", 0),
                "result_item": seed_config.get("result_item", "未知"),
                "yield_range": f"{seed_config.get('yield_min', 1)}-{seed_config.get('yield_max', 1)}"
            })

        return seeds

    @staticmethod
    async def _get_seed_item(db: AsyncSession, character: Character, seed_item_id: int) -> Optional[InventoryItem]:
        """获取种子物品"""
        result = await db.execute(
            select(InventoryItem)
            .join(Item, InventoryItem.item_id == Item.id)
            .where(and_(
                InventoryItem.character_id == character.id,
                InventoryItem.item_id == seed_item_id,
                Item.item_type == "seed",
                InventoryItem.quantity > 0
            ))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _add_item_to_inventory(db: AsyncSession, character: Character, item_name: str, quantity: int):
        """添加物品到背包"""
        # 获取或创建物品
        result = await db.execute(select(Item).where(Item.name == item_name))
        item = result.scalar_one_or_none()

        if not item:
            # 创建新物品
            item = Item(
                name=item_name,
                type="material",  # 默认为材料类型
                description=f"从灵田收获的{item_name}",
                value=10  # 默认价值
            )
            db.add(item)
            await db.flush()  # 获取ID

        # 添加到背包
        await InventoryCRUD.add_item_to_inventory(db, character.id, item.id, quantity)

    @staticmethod
    async def update_all_plots(db: AsyncSession):
        """更新所有地块状态（定时任务用）"""
        try:
            result = await db.execute(
                select(FarmPlot)
                .where(FarmPlot.seed_item_id.isnot(None))
            )
            plots = result.scalars().all()

            for plot in plots:
                await FarmSystem._update_plot_status(db, plot)

            await db.commit()

        except Exception as e:
            await db.rollback()
            print(f"更新地块状态失败: {str(e)}")

    @staticmethod
    async def process_offline_farming(db: AsyncSession, character: Character, offline_duration: float) -> Dict[str, Any]:
        """
        处理离线农场收益

        Args:
            db: 数据库会话
            character: 角色对象
            offline_duration: 离线时长（秒）

        Returns:
            农场收益信息
        """
        try:
            # 获取角色的所有地块
            result = await db.execute(
                select(FarmPlot)
                .where(FarmPlot.character_id == character.id)
            )
            plots = result.scalars().all()

            matured_crops = 0
            items_gained = {}

            # 检查每个地块是否有作物成熟
            for plot in plots:
                if plot.seed_item_id and plot.harvest_at:
                    # 更新地块状态
                    await FarmSystem._update_plot_status(db, plot)

                    # 如果作物成熟且未枯萎，自动收获
                    if plot.is_ready and not plot.is_withered:
                        harvest_result = await FarmSystem.harvest_plot(db, character, plot.plot_index)
                        if harvest_result["success"]:
                            matured_crops += 1
                            # 统计收获的物品
                            for item_name, quantity in harvest_result.get("items_gained", {}).items():
                                items_gained[item_name] = items_gained.get(item_name, 0) + quantity

            return {
                "matured_crops": matured_crops,
                "items_gained": items_gained
            }

        except Exception as e:
            logger.error(f"处理离线农场失败: {e}")
            return {
                "matured_crops": 0,
                "items_gained": {},
                "error": str(e)
            }
