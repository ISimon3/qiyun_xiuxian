# 封装WebSocket实时通信

import json
import asyncio
import threading
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import websocket
from PyQt6.QtCore import QObject, pyqtSignal, QThread


class WebSocketClient(QObject):
    """WebSocket客户端"""

    # 信号定义
    connected = pyqtSignal()  # 连接成功
    disconnected = pyqtSignal()  # 连接断开
    message_received = pyqtSignal(dict)  # 收到消息
    error_occurred = pyqtSignal(str)  # 发生错误

    def __init__(self, server_url: str = "ws://localhost:8000"):
        super().__init__()
        self.server_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws: Optional[websocket.WebSocketApp] = None
        self.token: Optional[str] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # 秒

        # 消息回调
        self.message_callbacks: Dict[str, Callable] = {}

    def set_token(self, token: str):
        """设置认证token"""
        self.token = token

    def connect(self):
        """连接WebSocket服务器"""
        if not self.token:
            self.error_occurred.emit("未设置认证token")
            return

        if self.is_connected:
            print("⚠️ WebSocket已经连接")
            return

        try:
            # 构造WebSocket URL
            ws_url = f"{self.server_url}/api/v1/websocket/ws/{self.token}"
            print(f"🔗 正在连接WebSocket: {ws_url}")

            # 创建WebSocket连接
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # 在新线程中运行WebSocket
            def run_websocket():
                self.ws.run_forever()

            self.ws_thread = threading.Thread(target=run_websocket, daemon=True)
            self.ws_thread.start()

        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            self.error_occurred.emit(f"连接失败: {str(e)}")

    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws and self.is_connected:
            print("🔌 正在断开WebSocket连接...")
            self.ws.close()

    def send_message(self, message_data: Dict[str, Any]):
        """发送消息"""
        if not self.is_connected or not self.ws:
            print("⚠️ WebSocket未连接，无法发送消息")
            return False

        try:
            message_json = json.dumps(message_data)
            self.ws.send(message_json)
            return True
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            self.error_occurred.emit(f"发送消息失败: {str(e)}")
            return False

    def send_chat_message(self, content: str, channel: str = "WORLD"):
        """发送聊天消息"""
        message_data = {
            "type": "chat",
            "channel": channel,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        return self.send_message(message_data)

    def send_ping(self):
        """发送心跳消息"""
        message_data = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        return self.send_message(message_data)

    def request_history(self, channel: str = "WORLD", limit: int = 50):
        """请求历史消息"""
        message_data = {
            "type": "get_history",
            "channel": channel,
            "limit": limit
        }
        return self.send_message(message_data)

    def register_message_callback(self, message_type: str, callback: Callable):
        """注册消息回调"""
        self.message_callbacks[message_type] = callback

    def _on_open(self, ws):
        """WebSocket连接打开回调"""
        print("✅ WebSocket连接成功")
        self.is_connected = True
        self.reconnect_attempts = 0

        # 使用QTimer确保信号在主线程中发出
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.connected.emit())

        # 延迟请求历史消息，确保连接完全建立
        QTimer.singleShot(100, lambda: self.request_history())

    def _on_message(self, ws, message):
        """WebSocket消息接收回调"""
        try:
            message_data = json.loads(message)
            message_type = message_data.get("type", "unknown")

            print(f"📨 收到WebSocket消息: {message_type}")

            # 使用QTimer确保信号在主线程中发出
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._emit_message_signal(message_data))

        except Exception as e:
            print(f"❌ 处理WebSocket消息失败: {e}")
            QTimer.singleShot(0, lambda: self.error_occurred.emit(f"处理消息失败: {str(e)}"))

    def _emit_message_signal(self, message_data):
        """在主线程中发出消息信号"""
        try:
            message_type = message_data.get("type", "unknown")

            # 触发通用消息信号
            self.message_received.emit(message_data)

            # 调用特定类型的回调
            if message_type in self.message_callbacks:
                self.message_callbacks[message_type](message_data)

        except Exception as e:
            print(f"❌ 发出消息信号失败: {e}")
            self.error_occurred.emit(f"信号处理失败: {str(e)}")

    def _on_error(self, ws, error):
        """WebSocket错误回调"""
        print(f"❌ WebSocket错误: {error}")
        # 使用QTimer确保信号在主线程中发出
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.error_occurred.emit(f"WebSocket错误: {str(error)}"))

    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket连接关闭回调"""
        print(f"🔌 WebSocket连接已关闭: {close_status_code} - {close_msg}")
        self.is_connected = False

        # 使用QTimer确保信号在主线程中发出
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.disconnected.emit())

        # 尝试重连
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            print(f"🔄 尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")

            def delayed_reconnect():
                import time
                time.sleep(self.reconnect_delay)
                if not self.is_connected:  # 确保还没有连接
                    QTimer.singleShot(0, lambda: self.connect())

            reconnect_thread = threading.Thread(target=delayed_reconnect, daemon=True)
            reconnect_thread.start()
        else:
            print("❌ 达到最大重连次数，停止重连")


class WebSocketManager(QObject):
    """WebSocket管理器 - 单例模式"""

    _instance = None
    _client: Optional[WebSocketClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._initialized = True

    def get_client(self, server_url: str = "ws://localhost:8000") -> WebSocketClient:
        """获取WebSocket客户端实例"""
        if self._client is None:
            self._client = WebSocketClient(server_url)
        return self._client

    def cleanup(self):
        """清理资源"""
        if self._client:
            self._client.disconnect()
            self._client = None


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()
