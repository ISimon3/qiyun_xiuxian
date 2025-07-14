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
    user_data_updated = pyqtSignal(dict)  # 用户数据更新信号
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
        self._user_data: Optional[Dict[str, Any]] = None  # 用户游戏数据（原角色数据）
        self._cultivation_status: Optional[Dict[str, Any]] = None  # 修炼状态数据
        self._luck_info: Optional[Dict[str, Any]] = None  # 气运信息数据
        self._server_url: str = "http://localhost:8000"
        self._saved_credentials: Optional[Dict[str, str]] = None
        self._remember_login_state: bool = False  # 是否记住登录状态
        self._remember_password: bool = False     # 是否记住密码

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
    def user_data(self) -> Optional[Dict[str, Any]]:
        """获取用户游戏数据"""
        return self._user_data

    @property
    def cultivation_status(self) -> Optional[Dict[str, Any]]:
        """获取修炼状态数据"""
        return self._cultivation_status

    @property
    def luck_info(self) -> Optional[Dict[str, Any]]:
        """获取气运信息数据"""
        return self._luck_info

    @property
    def server_url(self) -> str:
        """获取服务器URL"""
        return self._server_url

    def set_server_url(self, url: str) -> None:
        """设置服务器URL"""
        self._server_url = url.rstrip('/')
        self.save_config()
        self.state_changed.emit('server_url', url)

    def login(self, user_info: Dict[str, Any], token_data: Dict[str, Any],
              remember_login_state: bool = False) -> None:
        """
        用户登录

        Args:
            user_info: 用户信息
            token_data: 令牌数据
            remember_login_state: 是否记住登录状态
        """
        print(f"📊 状态管理器: 开始登录处理 - {user_info.get('username')}")

        self._user_info = user_info
        self._access_token = token_data.get('access_token')
        self._remember_login_state = remember_login_state

        if not self._access_token:
            print("❌ 警告: 未获取到访问令牌")
            return

        # 计算token过期时间
        expires_in = token_data.get('expires_in', 3600)
        self._token_expires_at = datetime.now().timestamp() + expires_in

        print(f"✅ Token设置成功，有效期: {expires_in}秒")
        print(f"🔑 Token: {self._access_token[:20]}...")
        print(f"💾 记住登录状态: {remember_login_state}")

        # 保存配置
        self.save_config()
        print("💾 登录状态已保存")

        # 发送登录信号
        self.user_logged_in.emit(user_info)
        self.state_changed.emit('login', user_info)

    def logout(self, clear_all: bool = False) -> None:
        """
        用户登出

        Args:
            clear_all: 是否清除所有数据（包括保存的凭据）
        """
        self._user_info = None
        self._access_token = None
        self._token_expires_at = None
        self._user_data = None
        self._cultivation_status = None
        self._luck_info = None

        # 登出时总是清除记住登录状态标志，除非明确要求保留
        self._remember_login_state = False

        # 如果明确要求清除所有数据，则也清除凭据和记住密码设置
        if clear_all:
            self._saved_credentials = None
            self._remember_password = False

        # 保存配置
        self.save_config()

        # 发送登出信号
        self.user_logged_out.emit()
        self.state_changed.emit('logout', None)

    def save_credentials(self, username: str, encoded_password: str,
                        remember_password: bool = False) -> None:
        """
        保存用户凭据

        Args:
            username: 用户名
            encoded_password: 编码后的密码
            remember_password: 是否记住密码
        """
        self._remember_password = remember_password

        if remember_password:
            self._saved_credentials = {
                'username': username,
                'password': encoded_password
            }
            print(f"📝 状态管理器: 已保存用户 {username} 的凭据")
        else:
            # 只保存用户名，不保存密码
            self._saved_credentials = {
                'username': username,
                'password': ''
            }
            print(f"📝 状态管理器: 已保存用户名 {username}（未保存密码）")

        self.save_config()

    def get_saved_credentials(self) -> Optional[Dict[str, str]]:
        """
        获取保存的凭据

        Returns:
            保存的凭据字典，包含username和password字段
        """
        return self._saved_credentials

    def get_remember_settings(self) -> Dict[str, bool]:
        """
        获取记住设置

        Returns:
            包含remember_login_state和remember_password的字典
        """
        return {
            'remember_login_state': self._remember_login_state,
            'remember_password': self._remember_password
        }

    def clear_saved_password(self) -> None:
        """清除保存的密码，但保留用户名"""
        if self._saved_credentials:
            self._saved_credentials = {
                'username': self._saved_credentials.get('username', ''),
                'password': ''
            }
            self.save_config()
            print("🧹 状态管理器: 已清除保存的密码")

    def clear_all_credentials(self) -> None:
        """清除所有保存的凭据"""
        self._saved_credentials = None
        self.save_config()
        print("🧹 状态管理器: 已清除所有保存的凭据")

    def is_token_expired(self) -> bool:
        """检查token是否过期"""
        if not self._token_expires_at:
            return True
        # 提前5分钟认为token过期，避免边界情况
        buffer_time = 300  # 5分钟
        return datetime.now().timestamp() >= (self._token_expires_at - buffer_time)

    def update_user_data(self, user_data: Dict[str, Any]) -> None:
        """
        更新用户游戏数据

        Args:
            user_data: 用户游戏数据
        """
        self._user_data = user_data
        self.save_config()
        self.user_data_updated.emit(user_data)
        self.state_changed.emit('user_data', user_data)

    def update_cultivation_status(self, cultivation_status: Dict[str, Any]) -> None:
        """
        更新修炼状态数据

        Args:
            cultivation_status: 修炼状态数据
        """
        self._cultivation_status = cultivation_status
        # 修炼状态不需要持久化保存，只在内存中保持

    def update_luck_info(self, luck_info: Dict[str, Any]) -> None:
        """
        更新气运信息数据

        Args:
            luck_info: 气运信息数据
        """
        self._luck_info = luck_info
        # 气运信息不需要持久化保存，只在内存中保持

    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            config_data = {
                'server_url': self._server_url,
                'user_info': self._user_info if self._remember_login_state else None,
                'access_token': self._access_token if self._remember_login_state else None,
                'token_expires_at': self._token_expires_at if self._remember_login_state else None,
                'user_data': self._user_data if self._remember_login_state else None,
                'saved_credentials': self._saved_credentials,
                'remember_login_state': self._remember_login_state,
                'remember_password': self._remember_password,
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
                # 配置文件不存在时，重置所有状态为默认值
                print("配置文件不存在，重置为默认状态")
                self._server_url = 'http://localhost:8000'
                self._user_info = None
                self._access_token = None
                self._token_expires_at = None
                self._user_data = None
                self._saved_credentials = None
                self._remember_login_state = False
                self._remember_password = False
                return

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 恢复状态数据
            self._server_url = config_data.get('server_url', 'http://localhost:8000')
            self._user_info = config_data.get('user_info')
            self._access_token = config_data.get('access_token')
            self._token_expires_at = config_data.get('token_expires_at')
            self._user_data = config_data.get('user_data')
            self._saved_credentials = config_data.get('saved_credentials')
            self._remember_login_state = config_data.get('remember_login_state', False)
            self._remember_password = config_data.get('remember_password', False)

            # 检查token是否过期
            if self._access_token and self.is_token_expired():
                print("Token已过期，清除登录状态")
                self.logout()

        except Exception as e:
            print(f"加载配置失败: {e}")
            # 加载失败时也重置为默认状态
            self._server_url = 'http://localhost:8000'
            self._user_info = None
            self._access_token = None
            self._token_expires_at = None
            self._user_data = None
            self._saved_credentials = None
            self._remember_login_state = False
            self._remember_password = False

    def clear_config(self) -> None:
        """清除所有配置"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
        except Exception as e:
            print(f"清除配置失败: {e}")

        # 重置状态
        self.logout()

    def reload_config(self) -> None:
        """重新加载配置文件"""
        print("🔄 重新加载配置文件...")
        self.load_config()

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        return {
            'is_logged_in': self.is_logged_in,
            'username': self._user_info.get('username') if self._user_info else None,
            'has_game_data': self._user_data is not None,
            'user_name': self._user_data.get('name') if self._user_data else None,
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
