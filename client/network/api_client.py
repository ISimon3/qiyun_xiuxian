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

    def get_characters(self) -> Dict[str, Any]:
        """获取用户角色列表"""
        return self.client.get('/api/v1/user/characters')

    def create_character(self, name: str, spiritual_root: str) -> Dict[str, Any]:
        """
        创建角色

        Args:
            name: 角色名
            spiritual_root: 灵根类型

        Returns:
            创建结果
        """
        data = {
            "name": name,
            "spiritual_root": spiritual_root
        }
        return self.client.post('/api/v1/user/characters', data)


class GameAPIClient(APIClient):
    """游戏API客户端，整合所有API模块"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)

        # 初始化各个API模块
        self.auth = AuthAPI(self)
        self.user = UserAPI(self)

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
