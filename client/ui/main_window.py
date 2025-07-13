# 主界面 (QQ风格)

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QPushButton, QMessageBox,
    QApplication, QSystemTrayIcon, QMenu, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QAction

from client.network.api_client import GameAPIClient, APIException
from client.network.websocket_client import websocket_manager
from client.state_manager import get_state_manager
from client.ui.widgets.upper_area_widget import UpperAreaWidget
from client.ui.widgets.lower_area_widget import LowerAreaWidget
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



        # 数据更新线程
        self.update_worker = DataUpdateWorker(self.api_client)
        self.setup_worker_connections()

        # 界面组件
        self.upper_area_widget = None
        self.lower_area_widget = None

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

        # 延迟加载初始数据，确保界面已完全初始化，在默认数据显示后加载真实数据
        QTimer.singleShot(500, self.load_initial_data)

        # 延迟启动自动修炼
        QTimer.singleShot(800, self.start_auto_cultivation)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("气运修仙")

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

        # 上区域 - HTML版本的角色信息和功能菜单
        self.upper_area_widget = UpperAreaWidget()
        # 移除固定高度限制，让分割器自由调整
        self.upper_area_widget.setStyleSheet("background-color: #f8f9fa; border-bottom: 2px solid #e1e5e9;")

        splitter.addWidget(self.upper_area_widget)

        # 下区域 - 使用新的下半区域管理器
        self.lower_area_widget = LowerAreaWidget(self)
        splitter.addWidget(self.lower_area_widget)

        # 设置分割器比例 (上半部分:下半部分 = 5:5)
        splitter.setSizes([int(window_height * 0.5), int(window_height * 0.5)])
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

        # 上半区域组件信号
        if self.upper_area_widget:
            self.upper_area_widget.function_selected.connect(self.on_function_selected)
            self.upper_area_widget.daily_sign_requested.connect(self.on_daily_sign_requested)
            self.upper_area_widget.cultivation_focus_changed.connect(self.on_cultivation_focus_changed)

        # 下半区域组件信号
        if self.lower_area_widget:
            self.lower_area_widget.view_switched.connect(self.on_lower_view_switched)

            # 延迟设置聊天频道信号连接，确保组件完全初始化
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.setup_chat_signals)

    def setup_chat_signals(self):
        """设置聊天信号连接"""
        try:
            if self.lower_area_widget:
                chat_widget = self.lower_area_widget.get_chat_channel_widget()
                if chat_widget:
                    chat_widget.new_message_received.connect(self.on_new_chat_message_received)
                    print("✅ 聊天信号连接已设置")
        except Exception as e:
            print(f"❌ 设置聊天信号失败: {e}")

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
                if self.lower_area_widget:
                    cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
                    if cultivation_log_widget:
                        cultivation_log_widget.add_system_log(f"修炼方向已切换为: {focus_name}{focus_icon}")

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

    def on_lower_view_switched(self, view_type: str):
        """处理下半区域视图切换"""
        # 更新频道按钮图标和提示
        if self.upper_area_widget:
            if view_type == "chat":
                self.upper_area_widget.update_channel_button("📋", "切换到修炼日志")
            else:
                self.upper_area_widget.update_channel_button("💬", "聊天频道")

    def on_new_chat_message_received(self):
        """处理新聊天消息接收"""
        # 如果当前不在聊天界面，显示新消息提示
        if self.lower_area_widget and self.lower_area_widget.get_current_view() != "chat":
            print("💬 收到新消息！点击'频道'按钮查看聊天")
            # 这里可以添加更多的新消息提示逻辑，比如闪烁按钮等

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

        # 消息回调现在由聊天组件处理

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
        if self.upper_area_widget:
            self.upper_area_widget.update_character_info(character_data)

    def on_cultivation_status_updated(self, cultivation_data: Dict[str, Any]):
        """修炼状态更新处理"""
        if self.upper_area_widget:
            self.upper_area_widget.update_cultivation_status(cultivation_data)

        # 更新修炼日志组件
        if self.lower_area_widget:
            cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
            if cultivation_log_widget:
                cultivation_log_widget.update_cultivation_status(cultivation_data)

    def on_luck_info_updated(self, luck_data: Dict[str, Any]):
        """气运信息更新处理"""
        if self.upper_area_widget:
            self.upper_area_widget.update_luck_info(luck_data)

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
            try:
                print("🔄 用户点击频道按钮")
                if self.lower_area_widget:
                    self.lower_area_widget.toggle_view()
                else:
                    print("❌ lower_area_widget 不存在")
            except Exception as e:
                print(f"❌ 频道切换失败: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "错误", f"频道切换失败: {str(e)}")
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
            # 注意：HTML版本的上半区域会通过数据更新自动刷新

            # 添加日志
            if self.lower_area_widget:
                cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
                if cultivation_log_widget:
                    cultivation_log_widget.add_special_event_log("完成副本探索，获得丰厚奖励！")

        except Exception as e:
            print(f"处理副本完成事件失败: {str(e)}")

    def show_worldboss_window(self):
        """显示世界boss窗口"""
        try:
            from client.ui.windows.worldboss_window import WorldBossWindow

            # 检查是否已经打开了世界boss窗口
            if hasattr(self, 'worldboss_window') and self.worldboss_window and not self.worldboss_window.isHidden():
                # 如果已经打开，就将其置于前台
                self.worldboss_window.raise_()
                self.worldboss_window.activateWindow()
                return

            # 创建新的世界boss窗口
            self.worldboss_window = WorldBossWindow(self)
            self.worldboss_window.boss_defeated.connect(self.on_boss_defeated)
            self.worldboss_window.show()  # 使用show()而不是exec()，实现非模态
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开世界boss窗口失败: {str(e)}")

    def on_boss_defeated(self, reward_data):
        """处理boss被击败事件"""
        try:
            # 刷新角色信息
            # 注意：HTML版本的上半区域会通过数据更新自动刷新

            # 添加日志已经在WorldBossWindow中处理了
            print(f"✅ Boss被击败，获得奖励: {reward_data}")

        except Exception as e:
            print(f"处理boss被击败事件失败: {str(e)}")

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
                    if self.lower_area_widget:
                        cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
                        if cultivation_log_widget:
                            cultivation_log_widget.add_system_log(f"自动开始修炼: {focus_name}{focus_icon}")
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
    app.setOrganizationName("Simonius")

    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
