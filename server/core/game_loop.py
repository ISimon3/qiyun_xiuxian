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

logger = logging.getLogger(__name__)


class GameLoop:
    """游戏主循环管理器"""

    def __init__(self):
        self.is_running = False
        self.cultivation_interval = 300  # 5分钟 = 300秒
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
            async with get_db_session() as db:
                # 获取所有活跃的角色（最近24小时内登录过的）
                cutoff_time = datetime.now() - timedelta(hours=24)
                result = await db.execute(
                    select(Character).where(
                        Character.last_active >= cutoff_time
                    )
                )
                active_characters = result.scalars().all()

                logger.debug(f"处理 {len(active_characters)} 个活跃角色的修炼周期")

                for character in active_characters:
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

            # 如果是第一次处理这个角色，使用角色的最后活跃时间
            if last_cultivation is None:
                last_cultivation = character.last_active or current_time
                self.last_cultivation_time[character_id] = last_cultivation

            # 检查是否需要进行修炼周期
            time_diff = (current_time - last_cultivation).total_seconds()

            if time_diff >= self.cultivation_interval:
                # 计算需要处理的周期数
                cycles_to_process = int(time_diff // self.cultivation_interval)

                logger.debug(f"角色 {character.name} 需要处理 {cycles_to_process} 个修炼周期")

                # 处理每个修炼周期
                for cycle in range(cycles_to_process):
                    cultivation_result = await CultivationSystem.process_cultivation_cycle(db, character)

                    if cultivation_result["success"]:
                        logger.debug(f"角色 {character.name} 修炼周期 {cycle + 1} 完成")
                    else:
                        logger.warning(f"角色 {character.name} 修炼周期 {cycle + 1} 失败")

                # 更新最后修炼时间
                self.last_cultivation_time[character_id] = current_time

        except Exception as e:
            logger.error(f"处理角色 {character.name} 修炼失败: {e}")

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

    def get_character_next_cultivation_time(self, character_id: int) -> datetime:
        """
        获取角色下次修炼时间

        Args:
            character_id: 角色ID

        Returns:
            下次修炼时间
        """
        last_cultivation = self.last_cultivation_time.get(character_id)
        if last_cultivation is None:
            return datetime.now()

        return last_cultivation + timedelta(seconds=self.cultivation_interval)

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
