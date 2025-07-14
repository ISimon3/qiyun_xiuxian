# 后台任务管理器 - 只处理炼丹和农场等离线收益

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db_session
from server.core.systems.alchemy_system import AlchemySystem
from server.core.systems.farm_system import FarmSystem

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    后台任务管理器

    根据用户的设计思路：
    - 服务端全局运行，处理用户不在线时的"炼丹"、"灵田"收益
    - 不再处理修炼收益（修炼收益只有用户在线时才能获得）
    """

    def __init__(self):
        self.is_running = False
        self.task_interval = 60  # 每分钟检查一次

    async def start(self):
        """启动后台任务循环"""
        if self.is_running:
            logger.warning("后台任务管理器已在运行")
            return

        self.is_running = True
        logger.info("🔄 后台任务管理器启动（处理炼丹和农场收益）")

        try:
            while self.is_running:
                await self._process_background_tasks()
                await asyncio.sleep(self.task_interval)
        except Exception as e:
            logger.error(f"后台任务循环异常: {e}")
        finally:
            self.is_running = False
            logger.info("🔄 后台任务管理器停止")

    async def stop(self):
        """停止后台任务循环"""
        self.is_running = False
        logger.info("正在停止后台任务管理器...")

    async def _process_background_tasks(self):
        """处理后台任务"""
        try:
            current_time = datetime.now()
            logger.info(f"🔍 执行后台任务检查 - {current_time.strftime('%H:%M:%S')}")

            # 处理炼丹会话状态更新
            await self._process_alchemy_sessions()

            # 处理农场地块状态更新
            await self._process_farm_plots()

            logger.info("✅ 后台任务检查完成")

        except Exception as e:
            logger.error(f"处理后台任务失败: {e}")

    async def _process_alchemy_sessions(self):
        """处理炼丹会话状态更新"""
        try:
            async with get_db_session() as db:
                await AlchemySystem.update_alchemy_sessions(db)
                logger.debug("🧪 炼丹会话状态已更新")
        except Exception as e:
            logger.error(f"处理炼丹会话失败: {e}")

    async def _process_farm_plots(self):
        """处理农场地块状态更新"""
        try:
            async with get_db_session() as db:
                await FarmSystem.update_all_plots(db)
                logger.debug("🌱 农场地块状态已更新")
        except Exception as e:
            logger.error(f"处理农场地块失败: {e}")

    def get_status(self) -> dict:
        """获取后台任务管理器状态"""
        return {
            "is_running": self.is_running,
            "task_interval": self.task_interval,
            "current_time": datetime.now().isoformat()
        }


# 全局后台任务管理器实例
background_task_manager = BackgroundTaskManager()
