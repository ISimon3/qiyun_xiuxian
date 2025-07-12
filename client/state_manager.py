# 客户端状态管理器 (保存玩家数据、token等)

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal

from shared.schemas import UserInfo, CharacterInfo


class StateManager(QObject):
    """客户端状态管理器"""

    # 信号定义
    user_logged_in = pyqtSignal(dict)  # 用户登录信号
    user_logged_out = pyqtSignal()     # 用户登出信号
    character_selected = pyqtSignal(dict)  # 角色选择信号
    state_changed = pyqtSignal(str, object)  # 通用状态变更信号

    def __init__(self, config_dir: str = None):
        super().__init__()

        # 配置目录
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".qiyun_xiuxian")
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "client_config.json")

        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)

        # 状态数据
        self._user_info: Optional[Dict[str, Any]] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._characters: List[Dict[str, Any]] = []
        self._current_character: Optional[Dict[str, Any]] = None
        self._server_url: str = "http://localhost:8000"

        # 加载保存的配置
        self.load_config()

    @property
    def is_logged_in(self) -> bool:
        """检查用户是否已登录"""
        return self._access_token is not None and self._user_info is not None

    @property
    def user_info(self) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        return self._user_info

    @property
    def access_token(self) -> Optional[str]:
        """获取访问令牌"""
        return self._access_token

    @property
    def characters(self) -> List[Dict[str, Any]]:
        """获取角色列表"""
        return self._characters.copy()

    @property
    def current_character(self) -> Optional[Dict[str, Any]]:
        """获取当前选中的角色"""
        return self._current_character

    @property
    def server_url(self) -> str:
        """获取服务器URL"""
        return self._server_url

    def set_server_url(self, url: str) -> None:
        """设置服务器URL"""
        self._server_url = url.rstrip('/')
        self.save_config()
        self.state_changed.emit('server_url', url)

    def login(self, user_info: Dict[str, Any], token_data: Dict[str, Any]) -> None:
        """
        用户登录

        Args:
            user_info: 用户信息
            token_data: 令牌数据
        """
        self._user_info = user_info
        self._access_token = token_data.get('access_token')

        # 计算token过期时间
        expires_in = token_data.get('expires_in', 3600)
        self._token_expires_at = datetime.now().timestamp() + expires_in

        # 保存配置
        self.save_config()

        # 发送登录信号
        self.user_logged_in.emit(user_info)
        self.state_changed.emit('login', user_info)

    def logout(self) -> None:
        """用户登出"""
        self._user_info = None
        self._access_token = None
        self._token_expires_at = None
        self._characters = []
        self._current_character = None

        # 保存配置
        self.save_config()

        # 发送登出信号
        self.user_logged_out.emit()
        self.state_changed.emit('logout', None)

    def is_token_expired(self) -> bool:
        """检查token是否过期"""
        if not self._token_expires_at:
            return True
        return datetime.now().timestamp() >= self._token_expires_at

    def update_characters(self, characters: List[Dict[str, Any]]) -> None:
        """
        更新角色列表

        Args:
            characters: 角色列表
        """
        self._characters = characters
        self.save_config()
        self.state_changed.emit('characters', characters)

    def select_character(self, character: Dict[str, Any]) -> None:
        """
        选择当前角色

        Args:
            character: 角色信息
        """
        self._current_character = character
        self.save_config()
        self.character_selected.emit(character)
        self.state_changed.emit('current_character', character)

    def add_character(self, character: Dict[str, Any]) -> None:
        """
        添加新角色到列表

        Args:
            character: 角色信息
        """
        self._characters.append(character)
        self.save_config()
        self.state_changed.emit('characters', self._characters)

    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            config_data = {
                'server_url': self._server_url,
                'user_info': self._user_info,
                'access_token': self._access_token,
                'token_expires_at': self._token_expires_at,
                'characters': self._characters,
                'current_character': self._current_character,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存配置失败: {e}")

    def load_config(self) -> None:
        """从文件加载配置"""
        try:
            if not os.path.exists(self.config_file):
                return

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 恢复状态数据
            self._server_url = config_data.get('server_url', 'http://localhost:8000')
            self._user_info = config_data.get('user_info')
            self._access_token = config_data.get('access_token')
            self._token_expires_at = config_data.get('token_expires_at')
            self._characters = config_data.get('characters', [])
            self._current_character = config_data.get('current_character')

            # 检查token是否过期
            if self._access_token and self.is_token_expired():
                print("Token已过期，清除登录状态")
                self.logout()

        except Exception as e:
            print(f"加载配置失败: {e}")

    def clear_config(self) -> None:
        """清除所有配置"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
        except Exception as e:
            print(f"清除配置失败: {e}")

        # 重置状态
        self.logout()

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        return {
            'is_logged_in': self.is_logged_in,
            'username': self._user_info.get('username') if self._user_info else None,
            'character_count': len(self._characters),
            'current_character_name': self._current_character.get('name') if self._current_character else None,
            'server_url': self._server_url,
            'token_expired': self.is_token_expired() if self._access_token else None
        }


# 全局状态管理器实例
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """获取全局状态管理器实例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def init_state_manager(config_dir: str = None) -> StateManager:
    """
    初始化全局状态管理器

    Args:
        config_dir: 配置目录路径

    Returns:
        状态管理器实例
    """
    global _state_manager
    _state_manager = StateManager(config_dir)
    return _state_manager
