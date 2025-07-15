# 用户会话管理器 - 替代全局游戏循环

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.database import get_db_session
from server.database.crud import CharacterCRUD
from server.database.models import Character
from server.core.systems.cultivation_system import CultivationSystem
from server.core.systems.alchemy_system import AlchemySystem
from server.core.systems.farm_system import FarmSystem

logger = logging.getLogger(__name__)


class UserSessionManager:
    """用户会话管理器 - 基于用户会话的个人计时器"""

    def __init__(self):
        # 存储用户会话：{user_id: session_info}
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        # 修炼间隔（秒）- 从配置文件读取
        from server.config import settings
        self.cultivation_interval = settings.CULTIVATION_TICK_INTERVAL
        logger.info(f"🔧 用户会话管理器初始化，修炼间隔: {self.cultivation_interval}秒")

    async def user_login(self, user_id: int, character_id: int) -> Dict[str, Any]:
        """
        用户登录处理

        Args:
            user_id: 用户ID
            character_id: 角色ID

        Returns:
            登录处理结果，包含离线收益
        """
        try:
            current_time = datetime.now()

            # 检查用户是否已经在线，如果是则先处理旧会话登出
            if user_id in self.user_sessions:
                logger.info(f"👤 用户 {user_id} 重复登录，先处理旧会话登出")
                await self.user_logout(user_id)

            # 获取角色信息
            async with get_db_session() as db:
                character = await CharacterCRUD.get_character_by_id(db, character_id)
                if not character:
                    return {"success": False, "message": "角色不存在"}

                # 计算离线收益
                offline_rewards = await self._calculate_offline_rewards(db, character, current_time)

                # 更新角色最后活跃时间
                character.last_active = current_time
                await db.commit()

            # 创建用户会话
            self.user_sessions[user_id] = {
                "character_id": character_id,
                "login_time": current_time,
                "last_cultivation_time": current_time,
                "last_activity_time": current_time,
                "is_online": True
            }

            logger.info(f"👤 用户 {user_id} (角色 {character_id}) 登录成功")

            return {
                "success": True,
                "message": "登录成功",
                "offline_rewards": offline_rewards,
                "session_info": self.user_sessions[user_id]
            }

        except Exception as e:
            logger.error(f"用户登录处理失败: {e}")
            return {"success": False, "message": f"登录处理失败: {str(e)}"}

    async def user_logout(self, user_id: int) -> Dict[str, Any]:
        """
        用户登出处理
        
        Args:
            user_id: 用户ID
            
        Returns:
            登出处理结果
        """
        try:
            if user_id not in self.user_sessions:
                return {"success": False, "message": "用户会话不存在"}

            session = self.user_sessions[user_id]
            character_id = session["character_id"]
            current_time = datetime.now()

            # 更新角色最后活跃时间
            async with get_db_session() as db:
                character = await CharacterCRUD.get_character_by_id(db, character_id)
                if character:
                    character.last_active = current_time
                    await db.commit()

            # 移除用户会话
            del self.user_sessions[user_id]

            logger.info(f"👤 用户 {user_id} (角色 {character_id}) 登出成功")
            
            return {"success": True, "message": "登出成功"}

        except Exception as e:
            logger.error(f"用户登出处理失败: {e}")
            return {"success": False, "message": f"登出处理失败: {str(e)}"}

    async def _calculate_offline_rewards(
        self, 
        db: AsyncSession, 
        character: Character, 
        current_time: datetime
    ) -> Dict[str, Any]:
        """
        计算离线收益
        
        Args:
            db: 数据库会话
            character: 角色对象
            current_time: 当前时间
            
        Returns:
            离线收益信息
        """
        try:
            if not character.last_active:
                # 首次登录，没有离线时间
                return {
                    "offline_duration": 0,
                    "cultivation_cycles": 0,
                    "cultivation_rewards": {},
                    "alchemy_rewards": {},
                    "farm_rewards": {}
                }

            # 计算离线时长
            offline_duration = (current_time - character.last_active).total_seconds()
            
            if offline_duration < self.cultivation_interval:
                # 离线时间不足一个修炼周期
                return {
                    "offline_duration": offline_duration,
                    "cultivation_cycles": 0,
                    "cultivation_rewards": {},
                    "alchemy_rewards": {},
                    "farm_rewards": {}
                }

            # 计算可以获得的修炼周期数
            cultivation_cycles = int(offline_duration // self.cultivation_interval)
            
            # 限制最大离线收益（比如最多24小时）
            max_cycles = int((24 * 3600) // self.cultivation_interval)  # 24小时
            cultivation_cycles = min(cultivation_cycles, max_cycles)

            logger.info(f"🕐 角色 {character.name} 离线 {offline_duration:.0f}秒，可获得 {cultivation_cycles} 个修炼周期收益")

            # 修炼收益不在离线时计算，只有用户在线时才能获得修炼收益
            cultivation_rewards = {}

            # 计算炼丹收益
            alchemy_rewards = await AlchemySystem.process_offline_alchemy(db, character, offline_duration)
            
            # 计算农场收益
            farm_rewards = await FarmSystem.process_offline_farming(db, character, offline_duration)

            return {
                "offline_duration": offline_duration,
                "cultivation_cycles": cultivation_cycles,
                "cultivation_rewards": cultivation_rewards,
                "alchemy_rewards": alchemy_rewards,
                "farm_rewards": farm_rewards
            }

        except Exception as e:
            logger.error(f"计算离线收益失败: {e}")
            return {
                "offline_duration": 0,
                "cultivation_cycles": 0,
                "cultivation_rewards": {},
                "alchemy_rewards": {},
                "farm_rewards": {},
                "error": str(e)
            }

    async def process_user_cultivation_cycle(self, user_id: int) -> Dict[str, Any]:
        """
        处理用户的修炼周期（手动触发或定时触发）
        
        Args:
            user_id: 用户ID
            
        Returns:
            修炼结果
        """
        try:
            if user_id not in self.user_sessions:
                return {"success": False, "message": "用户未在线"}

            session = self.user_sessions[user_id]
            character_id = session["character_id"]
            current_time = datetime.now()

            # 检查是否可以进行修炼周期
            last_cultivation = session["last_cultivation_time"]
            time_diff = (current_time - last_cultivation).total_seconds()

            if time_diff < self.cultivation_interval:
                remaining_time = self.cultivation_interval - time_diff
                return {
                    "success": False,
                    "message": f"修炼周期未到，还需等待 {remaining_time:.0f} 秒",
                    "remaining_time": remaining_time
                }

            # 执行修炼周期
            async with get_db_session() as db:
                character = await CharacterCRUD.get_character_by_id(db, character_id)
                if not character:
                    return {"success": False, "message": "角色不存在"}

                result = await CultivationSystem.process_cultivation_cycle(db, character)
                
                if result["success"]:
                    # 更新会话中的最后修炼时间
                    session["last_cultivation_time"] = current_time
                    session["last_activity_time"] = current_time

            return result

        except Exception as e:
            logger.error(f"处理用户修炼周期失败: {e}")
            return {"success": False, "message": f"修炼失败: {str(e)}"}

    def get_user_session_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户会话信息"""
        return self.user_sessions.get(user_id)

    def get_online_users(self) -> Dict[int, Dict[str, Any]]:
        """获取所有在线用户"""
        return self.user_sessions.copy()

    def get_online_count(self) -> int:
        """获取在线用户数量"""
        return len(self.user_sessions)

    def update_user_activity(self, user_id: int):
        """更新用户活跃时间"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["last_activity_time"] = datetime.now()


# 全局用户会话管理器实例
user_session_manager = UserSessionManager()
