# 核心挂机循环 (每分钟/五分钟计算收益)

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.database.database import get_db_session
from server.database.models import Character
from server.database.crud import CharacterCRUD
from server.core.systems.cultivation_system import CultivationSystem
from server.core.systems.alchemy_system import AlchemySystem
from server.core.systems.farm_system import FarmSystem

logger = logging.getLogger(__name__)


class GameLoop:
    """游戏主循环管理器"""

    def __init__(self):
        self.is_running = False
        # 从配置文件读取修炼间隔
        from server.config import settings
        self.cultivation_interval = settings.CULTIVATION_TICK_INTERVAL
        self.last_cultivation_time = {}  # 记录每个角色的最后修炼时间


    async def start(self):
        """启动游戏主循环"""
        if self.is_running:
            logger.warning("游戏主循环已在运行")
            return

        self.is_running = True
        logger.info("🎮 游戏主循环启动")

        try:
            while self.is_running:
                await self._process_cultivation_cycles()
                await self._process_alchemy_sessions()
                await self._process_farm_plots()
                await asyncio.sleep(60)  # 每分钟检查一次
        except Exception as e:
            logger.error(f"游戏主循环异常: {e}")
        finally:
            self.is_running = False
            logger.info("🎮 游戏主循环停止")

    async def stop(self):
        """停止游戏主循环"""
        self.is_running = False
        logger.info("正在停止游戏主循环...")

    async def _process_cultivation_cycles(self):
        """处理所有角色的修炼周期"""
        try:
            # 获取在线角色ID列表
            from server.api.v1.websocket import manager
            online_character_ids = list(manager.active_connections.keys())

            logger.info(f"🔍 在线角色检查: {online_character_ids}")

            if not online_character_ids:
                logger.info("📵 没有在线角色，跳过修炼周期处理")
                return

            async with get_db_session() as db:
                # 只获取在线的角色
                result = await db.execute(
                    select(Character).where(
                        Character.id.in_(online_character_ids)
                    )
                )
                online_characters = result.scalars().all()

                logger.info(f"⚡ 处理 {len(online_characters)} 个在线角色的修炼周期")

                for character in online_characters:
                    logger.info(f"🧘 处理角色 {character.name} (ID: {character.id}) 的修炼")
                    await self._process_character_cultivation(db, character)

        except Exception as e:
            logger.error(f"处理修炼周期失败: {e}")

    async def _process_character_cultivation(self, db: AsyncSession, character: Character):
        """处理单个角色的修炼"""
        try:
            character_id = character.id
            current_time = datetime.now()

            # 获取角色最后修炼时间
            last_cultivation = self.last_cultivation_time.get(character_id)

            # 如果是第一次处理这个角色，设置为当前时间（避免立即获得修炼收益）
            if last_cultivation is None:
                logger.info(f"🆕 角色 {character.name} 首次上线，设置修炼起始时间")
                self.last_cultivation_time[character_id] = current_time
                return  # 首次上线不处理修炼周期

            # 检查是否需要进行修炼周期
            time_diff = (current_time - last_cultivation).total_seconds()

            # 计算考虑聚灵阵加成的修炼间隔
            current_interval = self._get_character_cultivation_interval(character)

            logger.info(f"⏰ 角色 {character.name} 距离上次修炼: {time_diff:.1f}秒，需要间隔: {current_interval}秒")

            if time_diff >= current_interval:
                # 计算需要处理的周期数
                cycles_to_process = int(time_diff // self.cultivation_interval)

                logger.info(f"🔄 角色 {character.name} 需要处理 {cycles_to_process} 个修炼周期")

                # 处理每个修炼周期
                for cycle in range(cycles_to_process):
                    cultivation_result = await CultivationSystem.process_cultivation_cycle(db, character)

                    if cultivation_result["success"]:
                        logger.info(f"✅ 角色 {character.name} 修炼周期 {cycle + 1} 完成")
                    else:
                        logger.warning(f"❌ 角色 {character.name} 修炼周期 {cycle + 1} 失败")

                # 更新最后修炼时间
                self.last_cultivation_time[character_id] = current_time
            else:
                logger.info(f"⏳ 角色 {character.name} 修炼时间未到，还需等待 {self.cultivation_interval - time_diff:.1f}秒")

        except Exception as e:
            logger.error(f"处理角色 {character.name} 修炼失败: {e}")

    async def get_character_next_cultivation_time(self, character_id: int) -> datetime:
        """获取角色下次修炼时间（考虑聚灵阵加成）"""
        current_time = datetime.now()
        last_cultivation = self.last_cultivation_time.get(character_id)

        # 获取角色信息以计算聚灵阵加成
        async with get_db_session() as db:
            character = await CharacterCRUD.get_character_by_id(db, character_id)
            if not character:
                return current_time + timedelta(seconds=self.cultivation_interval)

        # 计算考虑聚灵阵加成的修炼间隔
        current_interval = self._get_character_cultivation_interval(character)

        if last_cultivation is None:
            # 如果没有记录，返回当前时间加上修炼间隔
            next_time = current_time + timedelta(seconds=current_interval)
            logger.info(f"🕐 角色 {character_id} 首次获取修炼时间: {next_time}")
            return next_time
        else:
            # 计算下次修炼时间
            next_time = last_cultivation + timedelta(seconds=current_interval)

            # 如果下次修炼时间已经过了，说明应该立即修炼
            if next_time <= current_time:
                next_time = current_time + timedelta(seconds=current_interval)
                logger.info(f"🕐 角色 {character_id} 修炼时间已到，设置新的修炼时间: {next_time}")

            return next_time

    def reset_character_cultivation_time(self, character_id: int):
        """重置角色修炼时间（用于切换修炼方向时）"""
        current_time = datetime.now()
        self.last_cultivation_time[character_id] = current_time
        logger.info(f"🔄 角色 {character_id} 修炼时间已重置: {current_time}")

    async def _process_alchemy_sessions(self):
        """处理炼丹会话状态更新"""
        try:
            async with get_db_session() as db:
                await AlchemySystem.update_alchemy_sessions(db)
        except Exception as e:
            logger.error(f"处理炼丹会话失败: {e}")

    async def _process_farm_plots(self):
        """处理农场地块状态更新"""
        try:
            async with get_db_session() as db:
                await FarmSystem.update_all_plots(db)
        except Exception as e:
            logger.error(f"处理农场地块失败: {e}")

    async def force_cultivation_cycle(self, character_id: int) -> Dict[str, Any]:
        """
        强制执行一次修炼周期（用于测试或手动触发）

        Args:
            character_id: 角色ID

        Returns:
            修炼结果
        """
        try:
            async with get_db_session() as db:
                character = await CharacterCRUD.get_character_by_id(db, character_id)
                if not character:
                    return {"success": False, "message": "角色不存在"}

                result = await CultivationSystem.process_cultivation_cycle(db, character)

                # 更新最后修炼时间
                self.last_cultivation_time[character_id] = datetime.now()

                return result

        except Exception as e:
            logger.error(f"强制修炼周期失败: {e}")
            return {"success": False, "message": f"修炼失败: {str(e)}"}



    def _get_character_cultivation_interval(self, character) -> float:
        """获取角色的实际修炼间隔（考虑聚灵阵加成）"""
        try:
            from shared.constants import CAVE_SYSTEM_CONFIG

            base_interval = self.cultivation_interval
            spirit_array_level = character.spirit_gathering_array_level

            # 获取聚灵阵的间隔减少效果
            if spirit_array_level > 0 and "SPIRIT_GATHERING_ARRAY" in CAVE_SYSTEM_CONFIG:
                array_benefits = CAVE_SYSTEM_CONFIG["SPIRIT_GATHERING_ARRAY"]["LEVEL_BENEFITS"]
                if spirit_array_level in array_benefits:
                    interval_reduction = array_benefits[spirit_array_level].get("cultivation_interval_reduction", 0)
                    # 减少修炼间隔
                    actual_interval = base_interval * (1 - interval_reduction)
                    return max(5.0, actual_interval)  # 最小间隔5秒

            return base_interval

        except Exception as e:
            print(f"❌ 计算修炼间隔失败: {e}")
            return self.cultivation_interval

    def get_status(self) -> Dict[str, Any]:
        """获取游戏循环状态"""
        return {
            "is_running": self.is_running,
            "cultivation_interval": self.cultivation_interval,
            "active_characters": len(self.last_cultivation_time),

            "last_cultivation_times": {
                char_id: time.isoformat()
                for char_id, time in self.last_cultivation_time.items()
            }
        }


# 全局游戏循环实例
game_loop = GameLoop()
