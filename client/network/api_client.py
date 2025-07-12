# 封装HTTP请求 (登录、买东西等)

import json
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from shared.schemas import BaseResponse, UserRegister, UserLogin, UserInfo, Token


class APIClient:
    """API客户端，封装与服务端的HTTP通信"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API客户端

        Args:
            base_url: 服务端基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token: Optional[str] = None

        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def set_token(self, token: str) -> None:
        """设置访问令牌"""
        self.access_token = token
        self.session.headers['Authorization'] = f'Bearer {token}'

    def clear_token(self) -> None:
        """清除访问令牌"""
        self.access_token = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点
            data: 请求体数据
            params: URL参数
            timeout: 超时时间(秒)

        Returns:
            响应数据字典

        Raises:
            APIException: API请求异常
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))

        try:
            # 准备请求参数
            kwargs = {
                'timeout': timeout,
                'params': params
            }

            if data is not None:
                kwargs['json'] = data

            # 发送请求
            response = self.session.request(method, url, **kwargs)

            # 检查HTTP状态码
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text}'
                raise APIException(error_msg, response.status_code)

            # 解析响应
            try:
                return response.json()
            except json.JSONDecodeError:
                raise APIException("服务器响应格式错误", response.status_code)

        except requests.exceptions.Timeout:
            raise APIException("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise APIException("无法连接到服务器，请检查服务器状态")
        except requests.exceptions.RequestException as e:
            raise APIException(f"网络请求失败: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GET请求"""
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送POST请求"""
        return self._make_request('POST', endpoint, data=data)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送PUT请求"""
        return self._make_request('PUT', endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """发送DELETE请求"""
        return self._make_request('DELETE', endpoint)


class AuthAPI:
    """认证相关API"""

    def __init__(self, client: APIClient):
        self.client = client

    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        用户注册

        Args:
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            注册结果
        """
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        return self.client.post('/api/v1/auth/register', data)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            登录结果，包含token和用户信息
        """
        data = {
            "username": username,
            "password": password
        }
        response = self.client.post('/api/v1/auth/login', data)

        # 如果登录成功，自动设置token
        if response.get('success') and response.get('data'):
            token_data = response['data'].get('token')
            if token_data and token_data.get('access_token'):
                self.client.set_token(token_data['access_token'])

        return response

    def logout(self) -> Dict[str, Any]:
        """
        用户登出

        Returns:
            登出结果
        """
        try:
            response = self.client.post('/api/v1/auth/logout')
            return response
        finally:
            # 无论登出是否成功，都清除本地token
            self.client.clear_token()


class UserAPI:
    """用户信息相关API"""

    def __init__(self, client: APIClient):
        self.client = client

    def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        return self.client.get('/api/v1/user/me')

    def get_character(self) -> Dict[str, Any]:
        """获取用户角色信息（自动创建如果不存在）"""
        return self.client.get('/api/v1/user/character')

    def get_character_detail(self) -> Dict[str, Any]:
        """获取用户角色详细信息（包含装备）"""
        return self.client.get('/api/v1/user/character/detail')


class GameAPI:
    """游戏行为相关API"""

    def __init__(self, client: APIClient):
        self.client = client

    def daily_sign_in(self) -> Dict[str, Any]:
        """
        每日签到

        Returns:
            签到结果
        """
        return self.client.post('/api/v1/game/daily-sign')

    def use_luck_item(self, item_id: int, quantity: int = 1) -> Dict[str, Any]:
        """
        使用气运道具

        Args:
            item_id: 道具ID
            quantity: 使用数量

        Returns:
            使用结果
        """
        data = {
            "item_id": item_id,
            "quantity": quantity
        }
        return self.client.post('/api/v1/game/use-luck-item', data)

    def get_luck_info(self) -> Dict[str, Any]:
        """
        获取气运系统信息

        Returns:
            气运信息
        """
        return self.client.get('/api/v1/game/luck-info')

    def start_cultivation(self, cultivation_focus: str = "HP") -> Dict[str, Any]:
        """
        开始修炼

        Args:
            cultivation_focus: 修炼方向

        Returns:
            开始修炼结果
        """
        data = {"cultivation_focus": cultivation_focus}
        return self.client.post('/api/v1/game/start-cultivation', data)

    def change_cultivation_focus(self, cultivation_focus: str) -> Dict[str, Any]:
        """
        变更修炼方向

        Args:
            cultivation_focus: 新的修炼方向

        Returns:
            变更结果
        """
        data = {"cultivation_focus": cultivation_focus}
        return self.client.post('/api/v1/game/change-cultivation-focus', data)

    def manual_breakthrough(self) -> Dict[str, Any]:
        """
        手动突破境界

        Returns:
            突破结果
        """
        return self.client.post('/api/v1/game/manual-breakthrough')

    def get_cultivation_status(self) -> Dict[str, Any]:
        """
        获取修炼状态

        Returns:
            修炼状态信息
        """
        return self.client.get('/api/v1/game/cultivation-status')

    def force_cultivation_cycle(self) -> Dict[str, Any]:
        """
        强制执行修炼周期（测试用）

        Returns:
            修炼周期结果
        """
        return self.client.post('/api/v1/game/force-cultivation-cycle')


class InventoryAPI:
    """背包和装备相关API"""

    def __init__(self, client: APIClient):
        self.client = client

    def get_inventory(self) -> Dict[str, Any]:
        """
        获取角色背包

        Returns:
            背包物品列表
        """
        return self.client.get('/api/v1/inventory/inventory')

    def get_equipment(self) -> Dict[str, Any]:
        """
        获取角色装备

        Returns:
            装备信息
        """
        return self.client.get('/api/v1/inventory/equipment')

    def equip_item(self, item_id: int, slot: str) -> Dict[str, Any]:
        """
        装备物品

        Args:
            item_id: 物品ID
            slot: 装备部位

        Returns:
            装备结果
        """
        data = {
            "item_id": item_id,
            "slot": slot
        }
        return self.client.post('/api/v1/inventory/equip', data)

    def unequip_item(self, slot: str) -> Dict[str, Any]:
        """
        卸下装备

        Args:
            slot: 装备部位

        Returns:
            卸下结果
        """
        data = {"slot": slot}
        return self.client.post('/api/v1/inventory/unequip', data)

    def use_item(self, item_id: int, quantity: int = 1) -> Dict[str, Any]:
        """
        使用物品

        Args:
            item_id: 物品ID
            quantity: 使用数量

        Returns:
            使用结果
        """
        data = {
            "item_id": item_id,
            "quantity": quantity
        }
        return self.client.post('/api/v1/inventory/use-item', data)

    def delete_item(self, inventory_item_id: int, quantity: int = None) -> Dict[str, Any]:
        """
        删除物品

        Args:
            inventory_item_id: 背包物品ID
            quantity: 删除数量

        Returns:
            删除结果
        """
        data = {"inventory_item_id": inventory_item_id}
        if quantity is not None:
            data["quantity"] = quantity
        return self.client.post('/api/v1/inventory/delete-item', data)

    def sort_inventory(self, sort_type: str = "type") -> Dict[str, Any]:
        """
        整理背包

        Args:
            sort_type: 排序类型 (type, quality, name)

        Returns:
            整理结果
        """
        data = {"sort_type": sort_type}
        return self.client.post('/api/v1/inventory/sort', data)


class GameAPIClient(APIClient):
    """游戏API客户端，整合所有API模块"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)

        # 初始化各个API模块
        self.auth = AuthAPI(self)
        self.user = UserAPI(self)
        self.game = GameAPI(self)
        self.inventory = InventoryAPI(self)

    def test_connection(self) -> bool:
        """
        测试服务器连接

        Returns:
            连接是否成功
        """
        try:
            # 尝试访问根路径或健康检查端点
            response = self.get('/')
            return True
        except APIException:
            return False


class APIException(Exception):
    """API请求异常"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message
