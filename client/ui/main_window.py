# 主界面 (QQ风格)

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QPushButton, QMessageBox,
    QApplication, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QAction

from client.network.api_client import GameAPIClient, APIException
from client.network.websocket_client import websocket_manager
from client.state_manager import get_state_manager
from client.ui.widgets.character_info_widget import CharacterInfoWidget
from client.ui.widgets.cultivation_log_widget import CultivationLogWidget
from shared.constants import CULTIVATION_FOCUS_TYPES


class DataUpdateWorker(QThread):
    """数据更新工作线程"""

    # 信号定义
    character_updated = pyqtSignal(dict)  # 角色数据更新信号
    cultivation_status_updated = pyqtSignal(dict)  # 修炼状态更新信号
    luck_info_updated = pyqtSignal(dict)  # 气运信息更新信号
    update_failed = pyqtSignal(str)  # 更新失败信号

    def __init__(self, api_client: GameAPIClient):
        super().__init__()
        self.api_client = api_client
        self.running = False

    def start_updates(self):
        """开始数据更新"""
        self.running = True
        self.start()

    def stop_updates(self):
        """停止数据更新"""
        print("🛑 请求停止数据更新线程...")
        self.running = False

        # 如果线程正在运行，请求中断
        if self.isRunning():
            self.requestInterruption()
            print("📤 已发送线程中断请求")

    def run(self):
        """执行数据更新循环"""
        print("🚀 数据更新线程启动")

        while self.running and not self.isInterruptionRequested():
            try:
                # 检查API客户端是否有token
                if not self.api_client.access_token:
                    self.update_failed.emit("未设置访问令牌，请重新登录")
                    break

                # 获取角色信息
                character_response = self.api_client.user.get_character_detail()
                if character_response.get('success'):
                    self.character_updated.emit(character_response['data'])
                else:
                    error_msg = character_response.get('message', '获取角色信息失败')
                    self.update_failed.emit(f"角色信息: {error_msg}")

                # 获取修炼状态
                cultivation_response = self.api_client.game.get_cultivation_status()
                if cultivation_response.get('success'):
                    self.cultivation_status_updated.emit(cultivation_response['data'])
                else:
                    error_msg = cultivation_response.get('message', '获取修炼状态失败')
                    self.update_failed.emit(f"修炼状态: {error_msg}")

                # 获取气运信息
                luck_response = self.api_client.game.get_luck_info()
                if luck_response.get('success'):
                    self.luck_info_updated.emit(luck_response['data'])
                else:
                    error_msg = luck_response.get('message', '获取气运信息失败')
                    self.update_failed.emit(f"气运信息: {error_msg}")

            except APIException as e:
                if "401" in str(e):
                    self.update_failed.emit("认证失败，请重新登录")
                    break  # 停止更新循环
                else:
                    self.update_failed.emit(f"API错误: {str(e)}")
            except Exception as e:
                self.update_failed.emit(f"未知错误: {str(e)}")

            # 等待30秒后再次更新，每秒检查一次中断请求
            for i in range(30):
                if self.isInterruptionRequested() or not self.running:
                    break
                self.msleep(1000)  # 每秒检查一次

        print("🛑 数据更新线程已停止")


class FunctionMenuWidget(QWidget):
    """功能菜单组件"""

    # 信号定义
    function_selected = pyqtSignal(str)  # 功能选择信号

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)

        # 功能按钮列表（简化为图标，添加悬浮提示）
        functions = [
            ("背包", "backpack", "🎒", "查看背包物品"),
            ("洞府", "cave", "🏠", "进入洞府，可进行突破"),
            ("农场", "farm", "🌱", "管理农场种植"),
            ("炼丹", "alchemy", "⚗️", "炼制丹药"),
            ("副本", "dungeon", "⚔️", "挑战副本"),
            ("世界boss", "worldboss", "👹", "挑战世界boss"),
            ("商城", "shop", "🏪", "购买物品"),
            ("频道", "channel", "💬", "聊天频道")
        ]

        self.buttons = {}
        for name, key, icon, tooltip in functions:
            btn = QPushButton(f"{icon}")
            btn.setMinimumHeight(35)
            btn.setMaximumWidth(50)
            btn.setToolTip(tooltip)  # 添加悬浮提示
            btn.clicked.connect(lambda checked, k=key: self.function_selected.emit(k))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-size: 16px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border: 2px solid #007acc;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            self.buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()  # 右侧留白
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """主界面窗口"""

    def __init__(self, server_url: str = "http://localhost:8000"):
        super().__init__()

        # 初始化组件
        self.api_client = GameAPIClient(server_url)
        self.state_manager = get_state_manager()

        # 设置API客户端的token
        if self.state_manager.access_token:
            self.api_client.set_token(self.state_manager.access_token)

        # 初始化WebSocket客户端
        self.websocket_client = websocket_manager.get_client(server_url)
        if self.state_manager.access_token:
            self.websocket_client.set_token(self.state_manager.access_token)
        self.setup_websocket_connections()

        # 消息去重：存储最近发送的消息内容和时间戳
        self.recent_sent_messages = []  # 存储最近发送的消息，用于去重

        # 数据更新线程
        self.update_worker = DataUpdateWorker(self.api_client)
        self.setup_worker_connections()

        # 界面组件
        self.character_info_widget = None
        self.cultivation_log_widget = None
        self.chat_widget = None
        self.function_menu_widget = None

        # 界面状态
        self.current_lower_view = "log"  # "log" 或 "chat"

        self.init_ui()
        self.setup_connections()

        # 检查登录状态
        if not self.state_manager.is_logged_in or self.state_manager.is_token_expired():
            print("⚠️ 用户未登录或token已过期，触发登出")
            # 延迟触发登出，确保窗口已完全初始化
            QTimer.singleShot(100, self.state_manager.logout)
            return

        # 启动数据更新
        self.update_worker.start_updates()

        # 延迟加载初始数据，确保界面已完全初始化
        QTimer.singleShot(1000, self.load_initial_data)

        # 延迟启动自动修炼
        QTimer.singleShot(2000, self.start_auto_cultivation)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("气运修仙 - 主界面")

        # 设置窗口大小 (4:9比例)
        window_width = 400
        window_height = 900
        self.setFixedSize(window_width, window_height)

        # 居中显示
        self.center_window()

        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 垂直分割
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 上区域 (30%) - 角色信息和功能菜单
        upper_widget = QWidget()
        upper_widget.setMinimumHeight(int(window_height * 0.3))
        upper_widget.setMaximumHeight(int(window_height * 0.3))
        upper_widget.setStyleSheet("background-color: #f8f8f8; border-bottom: 2px solid #ddd;")

        upper_layout = QVBoxLayout()
        upper_layout.setSpacing(5)
        upper_layout.setContentsMargins(5, 5, 5, 5)

        # 角色信息组件
        self.character_info_widget = CharacterInfoWidget()
        upper_layout.addWidget(self.character_info_widget)

        # 功能菜单组件
        self.function_menu_widget = FunctionMenuWidget()
        upper_layout.addWidget(self.function_menu_widget)

        upper_widget.setLayout(upper_layout)
        splitter.addWidget(upper_widget)

        # 下区域 (70%) - 修炼日志和聊天切换
        lower_widget = QWidget()
        lower_widget.setMinimumHeight(int(window_height * 0.7))
        lower_widget.setStyleSheet("background-color: #ffffff;")

        self.lower_layout = QVBoxLayout()
        self.lower_layout.setSpacing(0)
        self.lower_layout.setContentsMargins(5, 5, 5, 5)

        # 创建修炼日志组件
        self.cultivation_log_widget = CultivationLogWidget()
        self.lower_layout.addWidget(self.cultivation_log_widget)

        # 创建聊天组件（初始隐藏）
        self.chat_widget = self.create_chat_widget()
        self.chat_widget.setVisible(False)
        self.lower_layout.addWidget(self.chat_widget)

        lower_widget.setLayout(self.lower_layout)
        splitter.addWidget(lower_widget)

        # 设置分割器比例
        splitter.setSizes([int(window_height * 0.3), int(window_height * 0.7)])
        splitter.setChildrenCollapsible(False)  # 禁止折叠

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

    def center_window(self):
        """窗口居中显示"""
        screen = self.screen().availableGeometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())

    def setup_connections(self):
        """设置信号连接"""
        # 状态管理器信号
        self.state_manager.user_logged_out.connect(self.on_user_logged_out)
        self.state_manager.state_changed.connect(self.on_state_changed)

        # 功能菜单信号
        if self.function_menu_widget:
            self.function_menu_widget.function_selected.connect(self.on_function_selected)

        # 角色信息组件信号
        if self.character_info_widget:
            self.character_info_widget.daily_sign_requested.connect(self.on_daily_sign_requested)
            self.character_info_widget.cultivation_focus_changed.connect(self.on_cultivation_focus_changed)

    def on_daily_sign_requested(self):
        """处理每日签到请求"""
        try:
            response = self.api_client.game.daily_sign_in()
            if response.get('success'):
                data = response['data']
                message = data.get('message', '签到成功')
                QMessageBox.information(self, "签到成功", message)
                # 刷新数据
                self.load_initial_data()
            else:
                error_msg = response.get('message', '签到失败')
                QMessageBox.warning(self, "签到失败", error_msg)
        except APIException as e:
            if "401" in str(e):
                QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
                self.state_manager.logout()  # 触发登出，会自动关闭窗口
            else:
                QMessageBox.warning(self, "签到失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"签到时发生错误: {str(e)}")

    def on_cultivation_focus_changed(self, focus_type: str):
        """处理修炼方向变更"""
        try:
            response = self.api_client.game.change_cultivation_focus(focus_type)
            if response.get('success'):
                focus_info = CULTIVATION_FOCUS_TYPES.get(focus_type, {})
                focus_name = focus_info.get('name', '未知')
                focus_icon = focus_info.get('icon', '❓')

                # 添加日志
                if self.cultivation_log_widget:
                    self.cultivation_log_widget.add_system_log(f"修炼方向已切换为: {focus_name}{focus_icon}")

                print(f"✅ 修炼方向已切换为: {focus_name}")
            else:
                error_msg = response.get('message', '修炼方向切换失败')
                QMessageBox.warning(self, "切换失败", error_msg)
                # 恢复原来的选择
                self.load_initial_data()
        except APIException as e:
            if "401" in str(e):
                QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
                self.state_manager.logout()  # 触发登出，会自动关闭窗口
            else:
                QMessageBox.warning(self, "切换失败", str(e))
                self.load_initial_data()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修炼方向切换时发生错误: {str(e)}")
            self.load_initial_data()

    def setup_worker_connections(self):
        """设置工作线程信号连接"""
        self.update_worker.character_updated.connect(self.on_character_updated)
        self.update_worker.cultivation_status_updated.connect(self.on_cultivation_status_updated)
        self.update_worker.luck_info_updated.connect(self.on_luck_info_updated)
        self.update_worker.update_failed.connect(self.on_update_failed)

    def setup_websocket_connections(self):
        """设置WebSocket连接"""
        # 连接WebSocket信号
        self.websocket_client.connected.connect(self.on_websocket_connected)
        self.websocket_client.disconnected.connect(self.on_websocket_disconnected)
        self.websocket_client.message_received.connect(self.on_websocket_message)
        self.websocket_client.error_occurred.connect(self.on_websocket_error)

        # 注册消息回调
        self.websocket_client.register_message_callback("chat", self.on_chat_message)
        self.websocket_client.register_message_callback("system", self.on_system_message)
        self.websocket_client.register_message_callback("history", self.on_history_message)

        # 启动WebSocket连接 - 延迟更长时间确保界面完全初始化
        QTimer.singleShot(5000, self.safe_connect_websocket)  # 延迟5秒连接

    def safe_connect_websocket(self):
        """安全地连接WebSocket"""
        try:
            if hasattr(self, 'websocket_client') and self.websocket_client:
                print("🔗 开始连接WebSocket...")
                self.websocket_client.connect()
            else:
                print("❌ WebSocket客户端未初始化")
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            import traceback
            traceback.print_exc()

    def load_initial_data(self):
        """加载初始数据"""
        try:
            # 检查登录状态
            if not self.state_manager.is_logged_in or self.state_manager.is_token_expired():
                QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
                self.state_manager.logout()  # 触发登出，会自动关闭窗口
                return

            # 确保API客户端有token
            if not self.api_client.access_token:
                if self.state_manager.access_token:
                    self.api_client.set_token(self.state_manager.access_token)
                else:
                    QMessageBox.warning(self, "认证失败", "未找到访问令牌，请重新登录")
                    self.state_manager.logout()  # 触发登出，会自动关闭窗口
                    return

            # 获取角色信息
            character_response = self.api_client.user.get_character_detail()
            if character_response.get('success'):
                self.on_character_updated(character_response['data'])
            else:
                error_msg = character_response.get('message', '获取角色信息失败')
                print(f"⚠️ 角色信息加载失败: {error_msg}")

            # 获取修炼状态
            cultivation_response = self.api_client.game.get_cultivation_status()
            if cultivation_response.get('success'):
                self.on_cultivation_status_updated(cultivation_response['data'])
            else:
                error_msg = cultivation_response.get('message', '获取修炼状态失败')
                print(f"⚠️ 修炼状态加载失败: {error_msg}")

            # 获取气运信息
            luck_response = self.api_client.game.get_luck_info()
            if luck_response.get('success'):
                self.on_luck_info_updated(luck_response['data'])
            else:
                error_msg = luck_response.get('message', '获取气运信息失败')
                print(f"⚠️ 气运信息加载失败: {error_msg}")

        except APIException as e:
            if "401" in str(e):
                QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
                self.state_manager.logout()  # 触发登出，会自动关闭窗口
            else:
                QMessageBox.warning(self, "数据加载失败", f"无法加载游戏数据: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def on_character_updated(self, character_data: Dict[str, Any]):
        """角色数据更新处理"""
        if self.character_info_widget:
            self.character_info_widget.update_character_info(character_data)

    def on_cultivation_status_updated(self, cultivation_data: Dict[str, Any]):
        """修炼状态更新处理"""
        if self.character_info_widget:
            self.character_info_widget.update_cultivation_status(cultivation_data)

        if self.cultivation_log_widget:
            self.cultivation_log_widget.update_cultivation_status(cultivation_data)

    def on_luck_info_updated(self, luck_data: Dict[str, Any]):
        """气运信息更新处理"""
        if self.character_info_widget:
            self.character_info_widget.update_luck_info(luck_data)

    def on_update_failed(self, error_message: str):
        """数据更新失败处理"""
        print(f"数据更新失败: {error_message}")

        # 检查是否为认证失败
        if "认证失败" in error_message or "401" in error_message:
            print("🔐 检测到认证失败，触发用户登出...")
            # 触发状态管理器登出，这会自动关闭主窗口并显示登录界面
            self.state_manager.logout()
        # 可以在状态栏显示错误信息，但不弹窗打扰用户

    def on_function_selected(self, function_key: str):
        """功能选择处理"""
        if function_key == "backpack":
            self.show_backpack_window()
        elif function_key == "cave":
            self.show_cave_window()
        elif function_key == "farm":
            self.show_farm_window()
        elif function_key == "alchemy":
            self.show_alchemy_window()
        elif function_key == "dungeon":
            self.show_dungeon_window()
        elif function_key == "worldboss":
            self.show_worldboss_window()
        elif function_key == "shop":
            self.show_shop_window()
        elif function_key == "channel":
            self.toggle_chat_view()
        else:
            QMessageBox.information(self, "提示", f"功能 '{function_key}' 正在开发中...")

    def show_backpack_window(self):
        """显示背包窗口"""
        try:
            from client.ui.windows.backpack_window import BackpackWindow

            # 检查是否已经打开了背包窗口
            if hasattr(self, 'backpack_window') and self.backpack_window and not self.backpack_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.backpack_window.raise_()
                self.backpack_window.activateWindow()
                return

            # 创建新的背包窗口
            self.backpack_window = BackpackWindow(self)
            self.backpack_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开背包窗口失败: {str(e)}")

    def show_cave_window(self):
        """显示洞府窗口"""
        try:
            from client.ui.windows.cave_window import CaveWindow

            # 检查是否已经打开了洞府窗口
            if hasattr(self, 'cave_window') and self.cave_window and not self.cave_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.cave_window.raise_()
                self.cave_window.activateWindow()
                return

            # 创建新的洞府窗口
            self.cave_window = CaveWindow(self)
            self.cave_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开洞府窗口失败: {str(e)}")

    def show_farm_window(self):
        """显示灵田窗口"""
        try:
            from client.ui.windows.farm_window import FarmWindow

            # 检查是否已经打开了灵田窗口
            if hasattr(self, 'farm_window') and self.farm_window and not self.farm_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.farm_window.raise_()
                self.farm_window.activateWindow()
                return

            # 创建新的灵田窗口
            self.farm_window = FarmWindow(self)
            self.farm_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开灵田窗口失败: {str(e)}")

    def show_alchemy_window(self):
        """显示炼丹窗口"""
        try:
            from client.ui.windows.alchemy_window import AlchemyWindow

            # 检查是否已经打开了炼丹窗口
            if hasattr(self, 'alchemy_window') and self.alchemy_window and not self.alchemy_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.alchemy_window.raise_()
                self.alchemy_window.activateWindow()
                return

            # 创建新的炼丹窗口
            self.alchemy_window = AlchemyWindow(self.api_client, self.state_manager)
            self.alchemy_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开炼丹窗口失败: {str(e)}")

    def show_dungeon_window(self):
        """显示副本窗口"""
        try:
            from client.ui.windows.dungeon_window import DungeonWindow

            # 检查是否已经打开了副本窗口
            if hasattr(self, 'dungeon_window') and self.dungeon_window and not self.dungeon_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.dungeon_window.raise_()
                self.dungeon_window.activateWindow()
                return

            # 创建新的副本窗口
            self.dungeon_window = DungeonWindow(self)
            self.dungeon_window.dungeon_completed.connect(self.on_dungeon_completed)
            self.dungeon_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开副本窗口失败: {str(e)}")

    def on_dungeon_completed(self, result_data):
        """处理副本完成事件"""
        try:
            # 刷新角色信息
            if self.character_info_widget:
                self.character_info_widget.refresh_character_info()

            # 添加日志
            if self.cultivation_log_widget:
                self.cultivation_log_widget.add_special_event_log("完成副本探索，获得丰厚奖励！")

        except Exception as e:
            print(f"处理副本完成事件失败: {str(e)}")

    def show_worldboss_window(self):
        """显示世界boss窗口"""
        self.show_worldboss_dialog()

    def show_shop_window(self):
        """显示商城窗口"""
        try:
            from client.ui.windows.shop_window import ShopWindow

            # 检查是否已经打开了商城窗口
            if hasattr(self, 'shop_window') and self.shop_window and not self.shop_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.shop_window.raise_()
                self.shop_window.activateWindow()
                return

            # 创建新的商城窗口
            self.shop_window = ShopWindow(self)
            self.shop_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开商城窗口失败: {str(e)}")

    def show_breakthrough_dialog(self):
        """显示突破对话框"""
        try:
            # 获取当前修炼状态
            response = self.api_client.game.get_cultivation_status()
            if not response.get('success'):
                QMessageBox.warning(self, "错误", "无法获取修炼状态")
                return

            cultivation_data = response['data']
            can_breakthrough = cultivation_data.get('can_breakthrough', False)
            breakthrough_rate = cultivation_data.get('breakthrough_rate', 0)
            current_realm = cultivation_data.get('current_realm_name', '未知')

            if not can_breakthrough:
                QMessageBox.information(
                    self, "无法突破",
                    f"当前境界: {current_realm}\n修为不足，无法进行突破。\n请继续修炼积累修为。"
                )
                return

            # 确认突破
            reply = QMessageBox.question(
                self, "境界突破",
                f"当前境界: {current_realm}\n"
                f"突破成功率: {breakthrough_rate:.1f}%\n\n"
                f"是否尝试突破到下一境界？\n"
                f"注意：突破失败可能会损失部分修为。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 执行突破
                breakthrough_response = self.api_client.game.manual_breakthrough()
                if breakthrough_response.get('success'):
                    result_data = breakthrough_response['data']
                    success = result_data.get('success', False)
                    message = result_data.get('message', '')

                    if success:
                        QMessageBox.information(self, "突破成功！", f"🎉 {message}")
                        # 添加突破日志
                        if self.cultivation_log_widget:
                            self.cultivation_log_widget.add_breakthrough_log(
                                cultivation_data.get('current_realm', 0),
                                cultivation_data.get('current_realm', 0) + 1,
                                True
                            )
                    else:
                        QMessageBox.warning(self, "突破失败", f"💥 {message}")
                        # 添加失败日志
                        if self.cultivation_log_widget:
                            self.cultivation_log_widget.add_breakthrough_log(
                                cultivation_data.get('current_realm', 0),
                                cultivation_data.get('current_realm', 0),
                                False
                            )

                    # 刷新数据
                    self.load_initial_data()
                else:
                    error_msg = breakthrough_response.get('message', '突破失败')
                    QMessageBox.warning(self, "突破失败", error_msg)

        except APIException as e:
            if "401" in str(e):
                QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
                self.state_manager.logout()  # 触发登出，会自动关闭窗口
            else:
                QMessageBox.warning(self, "突破失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"突破时发生错误: {str(e)}")

    def start_auto_cultivation(self):
        """启动自动修炼"""
        try:
            # 检查登录状态
            if not self.state_manager.is_logged_in or self.state_manager.is_token_expired():
                return

            # 获取当前修炼状态
            response = self.api_client.game.get_cultivation_status()
            if not response.get('success'):
                print("⚠️ 无法获取修炼状态，跳过自动修炼")
                return

            cultivation_data = response['data']
            is_cultivating = cultivation_data.get('is_cultivating', False)

            if not is_cultivating:
                # 获取当前修炼方向，如果没有则使用默认的体修
                current_focus = cultivation_data.get('cultivation_focus', 'HP')

                # 开始修炼
                start_response = self.api_client.game.start_cultivation(current_focus)
                if start_response.get('success'):
                    focus_info = CULTIVATION_FOCUS_TYPES.get(current_focus, {})
                    focus_name = focus_info.get('name', '体修')
                    focus_icon = focus_info.get('icon', '🛡️')

                    print(f"✅ 自动开始修炼: {focus_name}{focus_icon}")

                    # 添加系统日志
                    if self.cultivation_log_widget:
                        self.cultivation_log_widget.add_system_log(f"自动开始修炼: {focus_name}{focus_icon}")
                else:
                    error_msg = start_response.get('message', '自动修炼启动失败')
                    print(f"⚠️ 自动修炼启动失败: {error_msg}")
            else:
                print("✅ 角色已在修炼中")

        except APIException as e:
            print(f"⚠️ 自动修炼启动失败: {e}")
            # 检查是否为认证失败
            if "401" in str(e):
                print("🔐 自动修炼启动时检测到认证失败，触发用户登出...")
                self.state_manager.logout()
        except Exception as e:
            print(f"⚠️ 自动修炼启动异常: {e}")

    def create_chat_widget(self):
        """创建聊天组件"""
        # 直接创建简单的聊天组件
        return self.create_simple_chat_widget()

    def create_simple_chat_widget(self):
        """创建聊天组件（自动选择HTML或QTextEdit）"""
        # 检查WebEngine是否可用
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            return self.create_html_chat_widget()
        except ImportError:
            print("⚠️ WebEngine不可用，使用QTextEdit聊天界面")
            return self.create_textedit_chat_widget()

    def create_html_chat_widget(self):
        """创建基于HTML的聊天组件"""
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWidgets import QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton

        chat_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("💬 聊天频道")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        layout.addLayout(title_layout)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(line)

        # 聊天显示区域 - 使用HTML渲染
        self.chat_display = QWebEngineView()
        self.chat_display.setMinimumHeight(350)

        # 初始化聊天消息列表
        self.chat_messages = []

        # 设置初始HTML内容
        self.init_chat_html()

        # 延迟添加欢迎消息，等待HTML加载完成
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.add_welcome_message)

        layout.addWidget(self.chat_display)

        # 输入区域
        input_layout = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("💬 输入聊天内容...")
        self.chat_input.setMinimumHeight(36)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e1e5e9;
                border-radius: 18px;
                padding: 8px 16px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background: white;
            }
            QLineEdit:hover {
                border: 2px solid #adb5bd;
            }
        """)
        input_layout.addWidget(self.chat_input)

        send_button = QPushButton("📤 发送")
        send_button.setMinimumHeight(36)
        send_button.setMaximumWidth(80)
        send_button.clicked.connect(self.send_chat_message)
        send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 600;
                font-family: "Microsoft YaHei";
                padding: 0 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
            QPushButton:pressed {
                background: #004085;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
        """)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

        chat_widget.setLayout(layout)
        return chat_widget

    def init_chat_html(self):
        """初始化聊天HTML页面"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>聊天频道</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    font-size: 14px;
                    background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
                    color: #333;
                    line-height: 1.0;
                    overflow-x: hidden;
                }

                .chat-container {
                    padding: 1px;
                    margin: 0;
                    width: 100%;
                    height: 100vh;
                    overflow-y: auto;
                }

                .welcome-message {
                    text-align: center;
                    margin: 0;
                    padding: 2px 4px;
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                    border-radius: 6px;
                    border: 1px solid #90caf9;
                    font-size: 10px;
                    color: #1565c0;
                    font-weight: normal;
                    display: none;
                }

                .message {
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    word-wrap: break-word;
                    clear: both;
                    line-height: 1.0;
                }

                .message-left {
                    text-align: left;
                    float: left;
                    clear: both;
                    margin: 0;
                }

                .message-right {
                    text-align: right;
                    float: right;
                    clear: both;
                    margin: 0;
                }

                .message-center {
                    text-align: center;
                    clear: both;
                    margin: 0;
                }

                .message-header {
                    font-size: 14px;
                    font-weight: 600;
                    margin: 0;
                    padding: 0;
                    line-height: 1.0;
                }

                .message-content {
                    font-size: 14px;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    line-height: 1.0;
                }

                .system-message {
                    color: #e65100;
                    font-weight: 600;
                    background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
                    padding: 2px 6px;
                    border-radius: 6px;
                    border: 1px solid #ffcc02;
                    display: inline-block;
                    margin: 0;
                    font-size: 12px;
                    line-height: 1.0;
                }

                .world-channel {
                    color: #007bff;
                }

                .clearfix::after {
                    content: "";
                    display: table;
                    clear: both;
                }
            </style>
        </head>
        <body>
            <div class="chat-container" id="chatContainer">
                <!-- 动态添加消息，不要硬编码 -->
            </div>

            <script>
                function addMessage(html) {
                    const container = document.getElementById('chatContainer');
                    container.insertAdjacentHTML('beforeend', html);
                    container.scrollTop = container.scrollHeight;
                }

                function clearMessages() {
                    const container = document.getElementById('chatContainer');
                    container.innerHTML = '';
                }
            </script>
        </body>
        </html>
        """

        self.chat_display.setHtml(html_template)

    def add_welcome_message(self):
        """添加带当前时间的欢迎消息"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
            welcome_msg = self.create_system_message_html("欢迎进入聊天频道，祝您修炼愉快！", current_time)
            self.add_message_to_chat_display(welcome_msg)
        except Exception as e:
            print(f"❌ 添加欢迎消息失败: {e}")

    def switch_to_chat_view(self):
        """切换到聊天界面"""
        if self.current_lower_view == "chat":
            return

        self.current_lower_view = "chat"

        # 隐藏修炼日志，显示聊天
        self.cultivation_log_widget.setVisible(False)
        self.chat_widget.setVisible(True)

        # 更新频道按钮图标和提示
        if "channel" in self.function_menu_widget.buttons:
            channel_btn = self.function_menu_widget.buttons["channel"]
            channel_btn.setText("📋")
            channel_btn.setToolTip("切换到修炼日志")

        # 清除新消息提示
        self.clear_new_message_indicator()

        print("🔄 已切换到聊天界面")

    def switch_to_log_view(self):
        """切换到修炼日志界面"""
        if self.current_lower_view == "log":
            return

        self.current_lower_view = "log"

        # 隐藏聊天，显示修炼日志
        self.chat_widget.setVisible(False)
        self.cultivation_log_widget.setVisible(True)

        # 更新频道按钮图标和提示
        if "channel" in self.function_menu_widget.buttons:
            channel_btn = self.function_menu_widget.buttons["channel"]
            channel_btn.setText("💬")
            channel_btn.setToolTip("聊天频道")

        # 清除新消息提示（如果有的话）
        self.clear_new_message_indicator()

        print("🔄 已切换到修炼日志界面")

    def send_chat_message(self):
        """发送聊天消息"""
        if not hasattr(self, 'chat_input'):
            return

        message = self.chat_input.text().strip()
        if not message:
            return

        # 清空输入框
        self.chat_input.clear()

        # 立即显示自己的消息（乐观更新）
        self.add_local_chat_message(message)

        # 通过WebSocket发送消息
        if hasattr(self, 'websocket_client') and self.websocket_client.is_connected:
            success = self.websocket_client.send_chat_message(message, "WORLD")
            if success:
                print(f"💬 通过WebSocket发送聊天消息: {message}")
            else:
                print("❌ WebSocket发送消息失败")
        else:
            print("⚠️ WebSocket未连接，消息仅本地显示")

    def add_local_chat_message(self, message: str):
        """添加本地聊天消息（用于WebSocket未连接时的回退）"""
        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")

        # 获取用户名
        username = "我"
        if self.state_manager.user_info:
            username = self.state_manager.user_info.get('username', '我')

        # 转义HTML特殊字符
        import html
        safe_message = html.escape(str(message))
        safe_username = html.escape(str(username))

        # 记录发送的消息用于去重
        message_key = f"{safe_message}_{current_time}"
        self.recent_sent_messages.append(message_key)

        # 只保留最近10条消息记录
        if len(self.recent_sent_messages) > 10:
            self.recent_sent_messages.pop(0)

        # 创建自己的消息（右对齐）
        new_message = self.create_chat_message_html(
            "WORLD", safe_username, safe_message, current_time, is_own_message=True
        )

        self.add_message_to_chat_display(new_message)

    def toggle_chat_view(self):
        """切换聊天/日志界面"""
        if self.current_lower_view == "log":
            self.switch_to_chat_view()
        else:
            self.switch_to_log_view()

    def show_worldboss_dialog(self):
        """显示世界boss对话框"""
        try:
            # 创建世界boss信息对话框
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTextEdit

            dialog = QDialog(self)
            dialog.setWindowTitle("👹 世界boss")
            dialog.setFixedSize(500, 600)
            dialog.setModal(True)

            layout = QVBoxLayout()
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            # 标题
            title_label = QLabel("👹 世界boss - 魔龙王")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("color: #8b0000; margin-bottom: 10px;")
            layout.addWidget(title_label)

            # Boss信息
            boss_info_layout = QVBoxLayout()

            # Boss血量
            hp_layout = QHBoxLayout()
            hp_label = QLabel("血量:")
            hp_label.setStyleSheet("font-weight: bold; color: #333;")
            hp_layout.addWidget(hp_label)

            hp_progress = QProgressBar()
            hp_progress.setMinimum(0)
            hp_progress.setMaximum(1000000)
            hp_progress.setValue(750000)  # 75%血量
            hp_progress.setMinimumHeight(25)
            hp_progress.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #8b0000;
                    border-radius: 12px;
                    text-align: center;
                    background-color: #f0f0f0;
                    color: white;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff4444, stop:1 #cc0000);
                    border-radius: 10px;
                }
            """)
            hp_progress.setFormat("750,000 / 1,000,000 (75%)")
            hp_layout.addWidget(hp_progress)

            boss_info_layout.addLayout(hp_layout)

            # Boss属性
            attrs_layout = QHBoxLayout()

            left_attrs = QVBoxLayout()
            left_attrs.addWidget(QLabel("等级: 50"))
            left_attrs.addWidget(QLabel("物理攻击: 8,500"))
            left_attrs.addWidget(QLabel("法术攻击: 9,200"))

            right_attrs = QVBoxLayout()
            right_attrs.addWidget(QLabel("物理防御: 6,800"))
            right_attrs.addWidget(QLabel("法术防御: 7,100"))
            right_attrs.addWidget(QLabel("暴击率: 25%"))

            attrs_layout.addLayout(left_attrs)
            attrs_layout.addLayout(right_attrs)
            boss_info_layout.addLayout(attrs_layout)

            layout.addLayout(boss_info_layout)

            # 分割线
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("color: #ccc; margin: 10px 0;")
            layout.addWidget(line)

            # 战斗记录
            battle_label = QLabel("⚔️ 最近战斗记录:")
            battle_label.setStyleSheet("font-weight: bold; color: #333; margin-bottom: 5px;")
            layout.addWidget(battle_label)

            battle_log = QTextEdit()
            battle_log.setMaximumHeight(150)
            battle_log.setReadOnly(True)
            battle_log.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: 'Consolas', monospace;
                    font-size: 11px;
                }
            """)

            battle_log.setHtml("""
            <div style="color: #28a745;">[15:30] 玩家"剑仙"对魔龙王造成了12,500点伤害！</div>
            <div style="color: #dc3545;">[15:31] 魔龙王使用"龙息"，对玩家"剑仙"造成了8,200点伤害！</div>
            <div style="color: #28a745;">[15:32] 玩家"法神"对魔龙王造成了15,800点法术伤害！</div>
            <div style="color: #ffc107;">[15:33] 玩家"盾卫"使用"护盾术"，为团队提供了防护！</div>
            <div style="color: #dc3545;">[15:34] 魔龙王进入狂暴状态，攻击力提升50%！</div>
            <div style="color: #28a745;">[15:35] 玩家"治愈者"为团队恢复了20,000点生命值！</div>
            """)

            layout.addWidget(battle_log)

            # 奖励信息
            reward_label = QLabel("🎁 击败奖励:")
            reward_label.setStyleSheet("font-weight: bold; color: #333; margin-top: 10px;")
            layout.addWidget(reward_label)

            reward_text = QLabel("• 经验值: 50,000\n• 金币: 10,000\n• 灵石: 500\n• 龙鳞护甲 (传说级)\n• 龙血丹 x3")
            reward_text.setStyleSheet("color: #666; margin-left: 10px; line-height: 1.4;")
            layout.addWidget(reward_text)

            # 按钮区域
            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)

            # 挑战按钮
            challenge_button = QPushButton("⚔️ 挑战Boss")
            challenge_button.setMinimumHeight(40)
            challenge_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #a71e2a;
                }
            """)
            challenge_button.clicked.connect(lambda: self.challenge_worldboss(dialog))
            button_layout.addWidget(challenge_button)

            # 组队按钮
            team_button = QPushButton("👥 组队挑战")
            team_button.setMinimumHeight(40)
            team_button.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)
            team_button.clicked.connect(lambda: QMessageBox.information(dialog, "提示", "组队功能正在开发中..."))
            button_layout.addWidget(team_button)

            # 关闭按钮
            close_button = QPushButton("关闭")
            close_button.setMinimumHeight(40)
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
                QPushButton:pressed {
                    background-color: #545b62;
                }
            """)
            close_button.clicked.connect(dialog.close)
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)

            dialog.setLayout(layout)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示世界boss界面时发生错误: {str(e)}")

    def challenge_worldboss(self, dialog):
        """挑战世界boss"""
        try:
            # 确认挑战
            reply = QMessageBox.question(
                dialog, "确认挑战",
                "确定要挑战魔龙王吗？\n\n"
                "⚠️ 注意：\n"
                "• 挑战需要消耗100点体力\n"
                "• 失败可能会损失部分修为\n"
                "• 建议组队挑战以提高成功率",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 模拟战斗结果
                import random
                success = random.random() < 0.3  # 30%成功率

                if success:
                    QMessageBox.information(
                        dialog, "挑战成功！",
                        "🎉 恭喜！您成功击败了魔龙王！\n\n"
                        "获得奖励：\n"
                        "• 经验值: +50,000\n"
                        "• 金币: +10,000\n"
                        "• 灵石: +500\n"
                        "• 龙鳞护甲 (传说级)\n"
                        "• 龙血丹 x3"
                    )

                    # 添加战斗日志
                    if self.cultivation_log_widget:
                        self.cultivation_log_widget.add_special_event_log("成功击败世界boss魔龙王，获得丰厚奖励！")
                else:
                    QMessageBox.warning(
                        dialog, "挑战失败",
                        "💥 很遗憾，您被魔龙王击败了！\n\n"
                        "损失：\n"
                        "• 体力: -100\n"
                        "• 修为: -5,000\n\n"
                        "建议提升实力后再来挑战，或寻找队友组队！"
                    )

                    # 添加战斗日志
                    if self.cultivation_log_widget:
                        self.cultivation_log_widget.add_special_event_log("挑战世界boss魔龙王失败，损失了一些修为")

                dialog.close()

        except Exception as e:
            QMessageBox.critical(dialog, "错误", f"挑战世界boss时发生错误: {str(e)}")

    def on_user_logged_out(self):
        """用户登出处理"""
        self.close()

    def on_state_changed(self, state_key: str, state_value: Any):
        """状态变更处理"""
        if state_key == "server_url":
            # 服务器URL变更，重新初始化API客户端
            self.api_client = GameAPIClient(state_value)
            if self.state_manager.access_token:
                self.api_client.set_token(self.state_manager.access_token)

    # WebSocket事件处理方法
    def on_websocket_connected(self):
        """WebSocket连接成功"""
        print("✅ WebSocket连接成功")

    def on_websocket_disconnected(self):
        """WebSocket连接断开"""
        print("🔌 WebSocket连接断开")

    def on_websocket_error(self, error_message: str):
        """WebSocket错误"""
        print(f"❌ WebSocket错误: {error_message}")

    def on_websocket_message(self, message_data: dict):
        """处理WebSocket消息"""
        message_type = message_data.get("type", "unknown")
        print(f"📨 收到WebSocket消息: {message_type}")

    def on_chat_message(self, message_data: dict):
        """处理聊天消息"""
        try:
            if not isinstance(message_data, dict):
                print(f"⚠️ 无效的消息数据类型: {type(message_data)}")
                return

            channel = message_data.get("channel", "WORLD")
            character_name = message_data.get("character_name", "Unknown")
            content = message_data.get("content", "")
            timestamp = message_data.get("timestamp", "")
            character_id = message_data.get("character_id", 0)

            # 验证必要字段
            if not content:
                print("⚠️ 消息内容为空，跳过处理")
                return

            # 格式化时间
            from datetime import datetime
            try:
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                else:
                    time_str = datetime.now().strftime("%H:%M")
            except Exception as time_error:
                print(f"⚠️ 时间格式化失败: {time_error}")
                time_str = datetime.now().strftime("%H:%M")

            # 判断是否是自己发送的消息
            is_own_message = False
            if hasattr(self, 'state_manager') and self.state_manager.current_character:
                current_character_id = self.state_manager.current_character.get('id', 0)
                is_own_message = (character_id == current_character_id)

            # 转义HTML特殊字符
            import html
            safe_content = html.escape(str(content))
            safe_character_name = html.escape(str(character_name))

            # 如果是自己的消息，检查是否已经显示过（去重）
            if is_own_message:
                message_key = f"{safe_content}_{time_str}"
                if hasattr(self, 'recent_sent_messages') and message_key in self.recent_sent_messages:
                    print(f"⚠️ 跳过重复消息: {content}")
                    return

            # 创建消息HTML
            new_message = self.create_chat_message_html(
                channel, safe_character_name, safe_content, time_str, is_own_message
            )

            self.add_message_to_chat_display(new_message)

        except Exception as e:
            print(f"❌ 处理聊天消息失败: {e}")
            import traceback
            traceback.print_exc()

    def create_chat_message_html(self, channel: str, character_name: str, content: str, time_str: str, is_own_message: bool = False):
        """创建聊天消息HTML - 适用于WebEngine渲染"""
        try:
            # 根据频道设置颜色类
            channel_class = "world-channel" if channel == "WORLD" else "other-channel"

            if is_own_message:
                # 自己的消息：右对齐，统一12px字体
                message_html = f"""
                <div style="text-align: right; margin: 0; padding: 0; line-height: 12px; clear: both;">
                    <div style="font-size: 12px; color: #007bff; font-weight: 600; margin: 0; padding: 0; line-height: 12px;">[{channel}] {character_name} {time_str}</div>
                    <div style="font-size: 12px; color: #333; margin: 0; padding: 0; line-height: 12px;">{content}</div>
                </div>
                """
            else:
                # 他人的消息：左对齐，统一12px字体
                message_html = f"""
                <div style="text-align: left; margin: 0; padding: 0; line-height: 12px; clear: both;">
                    <div style="font-size: 12px; color: #007bff; font-weight: 600; margin: 0; padding: 0; line-height: 12px;">[{channel}] {character_name} {time_str}</div>
                    <div style="font-size: 12px; color: #333; margin: 0; padding: 0; line-height: 12px;">{content}</div>
                </div>
                """

            return message_html

        except Exception as e:
            print(f"❌ 创建消息HTML失败: {e}")
            # 回退到简单格式
            return f"""
            <div class="message clearfix">
                <div class="message-left">
                    <div class="message-header {channel_class}">[{channel}] {character_name} {time_str}</div>
                    <div class="message-content">{content}</div>
                </div>
            </div>
            """

    def create_system_message_html(self, content: str, time_str: str):
        """创建系统消息HTML - 适用于WebEngine渲染"""
        try:
            # 系统消息：统一12px字体，固定行高
            message_html = f"""
            <div style="text-align: center; margin: 0; padding: 0; line-height: 12px;">
                <span style="color: #e65100; font-weight: 600; background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%); padding: 1px 4px; border-radius: 4px; border: 1px solid #ffcc02; font-size: 12px; line-height: 12px; display: inline-block;">🔔 [系统] {content} · {time_str}</span>
            </div>
            """
            return message_html

        except Exception as e:
            print(f"❌ 创建系统消息HTML失败: {e}")
            # 回退到简单格式
            return f"""
            <div style="margin: 8px 0; padding: 0; text-align: center;">
                <span style="color: #bf360c; font-weight: bold; font-size: 12px;">🔔 [系统]:</span>
                <span style="color: #856404; margin: 0 6px; font-size: 12px;">{content}</span>
                <span style="color: #8d6e63; font-size: 10px;">[{time_str}]</span>
            </div>
            """

    def on_system_message(self, message_data: dict):
        """处理系统消息"""
        try:
            if not isinstance(message_data, dict):
                print(f"⚠️ 无效的系统消息数据类型: {type(message_data)}")
                return

            content = message_data.get("content", "")
            timestamp = message_data.get("timestamp", "")

            # 验证消息内容
            if not content:
                print("⚠️ 系统消息内容为空，跳过处理")
                return

            # 格式化时间
            from datetime import datetime
            try:
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                else:
                    time_str = datetime.now().strftime("%H:%M")
            except Exception as time_error:
                print(f"⚠️ 系统消息时间格式化失败: {time_error}")
                time_str = datetime.now().strftime("%H:%M")

            # 转义HTML特殊字符
            import html
            safe_content = html.escape(str(content))

            # 创建系统消息HTML（居中显示）
            new_message = self.create_system_message_html(safe_content, time_str)

            self.add_message_to_chat_display(new_message)

        except Exception as e:
            print(f"❌ 处理系统消息失败: {e}")
            import traceback
            traceback.print_exc()

    def on_history_message(self, message_data: dict):
        """处理历史消息"""
        try:
            messages = message_data.get("messages", [])
            channel = message_data.get("channel", "WORLD")

            print(f"📜 收到历史消息: {len(messages)} 条")

            # 清空当前聊天显示
            if hasattr(self, 'chat_display'):
                self.chat_display.clear()

                # 添加历史消息
                for msg in messages:
                    character_name = msg.get("character_name", "Unknown")
                    content = msg.get("content", "")
                    timestamp = msg.get("timestamp", "")
                    character_id = msg.get("character_id", 0)
                    message_type = msg.get("message_type", "NORMAL")

                    # 格式化时间
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%H:%M")
                    except:
                        time_str = datetime.now().strftime("%H:%M")

                    # 转义HTML特殊字符
                    import html
                    safe_content = html.escape(str(content))
                    safe_character_name = html.escape(str(character_name))

                    # 根据消息类型创建不同样式的消息
                    if message_type == "SYSTEM":
                        new_message = self.create_system_message_html(safe_content, time_str)
                    else:
                        # 判断是否是自己发送的消息
                        is_own_message = False
                        if hasattr(self, 'state_manager') and self.state_manager.current_character:
                            current_character_id = self.state_manager.current_character.get('id', 0)
                            is_own_message = (character_id == current_character_id)

                        new_message = self.create_chat_message_html(
                            channel, safe_character_name, safe_content, time_str, is_own_message
                        )

                    self.add_message_to_chat_display(new_message)

        except Exception as e:
            print(f"❌ 处理历史消息失败: {e}")

    def add_message_to_chat_display(self, message_html: str):
        """添加消息到HTML聊天显示区域"""
        try:
            # 检查聊天显示组件是否存在
            if not hasattr(self, 'chat_display') or self.chat_display is None:
                print("⚠️ 聊天显示组件不存在，跳过消息添加")
                return

            # 检查消息内容
            if not message_html or not isinstance(message_html, str):
                print("⚠️ 无效的消息HTML内容")
                return

            # 使用JavaScript添加消息到HTML页面
            try:
                # 转义JavaScript字符串中的特殊字符
                escaped_html = message_html.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')

                # 执行JavaScript添加消息
                js_code = f"addMessage('{escaped_html}');"
                self.chat_display.page().runJavaScript(js_code)

                # 如果当前不在聊天视图，显示提示
                if not hasattr(self, 'current_lower_view') or self.current_lower_view != "chat":
                    print("💬 收到新消息！点击'频道'按钮查看聊天")
                    # 可以在这里添加视觉提示，比如让频道按钮闪烁
                    self.show_new_message_indicator()

            except Exception as js_error:
                print(f"❌ JavaScript执行失败: {js_error}")

        except Exception as e:
            print(f"❌ 添加消息到聊天显示失败: {e}")
            import traceback
            traceback.print_exc()

    def show_new_message_indicator(self):
        """显示新消息提示"""
        try:
            # 查找频道按钮并添加视觉提示
            if hasattr(self, 'function_menu_widget') and hasattr(self.function_menu_widget, 'buttons'):
                if "channel" in self.function_menu_widget.buttons:
                    channel_btn = self.function_menu_widget.buttons["channel"]
                    # 改变按钮样式以显示有新消息
                    channel_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ff6b6b;
                            color: white;
                            border: 2px solid #ff4757;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #ff5252;
                        }
                    """)
                    channel_btn.setToolTip("💬 有新消息！点击查看聊天")

            print("🔔 新消息提示：有新的聊天消息，请点击'频道'按钮查看")
        except Exception as e:
            print(f"❌ 显示新消息提示失败: {e}")

    def clear_new_message_indicator(self):
        """清除新消息提示"""
        try:
            # 恢复频道按钮的正常样式
            if hasattr(self, 'function_menu_widget') and hasattr(self.function_menu_widget, 'buttons'):
                if "channel" in self.function_menu_widget.buttons:
                    channel_btn = self.function_menu_widget.buttons["channel"]
                    # 恢复正常样式
                    channel_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f8f9fa;
                            border: 1px solid #dee2e6;
                            border-radius: 8px;
                            padding: 8px;
                            font-size: 16px;
                        }
                        QPushButton:hover {
                            background-color: #e9ecef;
                        }
                        QPushButton:pressed {
                            background-color: #dee2e6;
                        }
                    """)
                    if self.current_lower_view == "chat":
                        channel_btn.setToolTip("切换到修炼日志")
                    else:
                        channel_btn.setToolTip("切换到聊天频道")
        except Exception as e:
            print(f"❌ 清除新消息提示失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            print("🔄 正在关闭主窗口...")

            # 断开WebSocket连接
            if hasattr(self, 'websocket_client'):
                print("🔌 正在断开WebSocket连接...")
                self.websocket_client.disconnect()

            # 停止数据更新线程
            if hasattr(self, 'update_worker') and self.update_worker.isRunning():
                print("⏹️ 停止数据更新线程...")
                self.update_worker.stop_updates()

                # 等待线程结束，但设置超时避免卡死
                if not self.update_worker.wait(3000):  # 等待3秒
                    print("⚠️ 强制终止数据更新线程")
                    self.update_worker.terminate()
                    self.update_worker.wait(1000)  # 再等1秒

            print("✅ 主窗口关闭完成")
            event.accept()

        except Exception as e:
            print(f"❌ 关闭窗口时发生错误: {e}")
            event.accept()  # 即使出错也要关闭窗口


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("气运修仙")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("气运修仙工作室")

    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
