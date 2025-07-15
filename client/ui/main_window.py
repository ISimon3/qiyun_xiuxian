# 主界面 (QQ风格)

import sys
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QPushButton, QMessageBox,
    QApplication, QSystemTrayIcon, QMenu, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
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
    user_data_updated = pyqtSignal(dict)  # 用户数据更新信号
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

        while self.running and not self.isInterruptionRequested():
            try:
                # 检查API客户端是否有token
                if not self.api_client.access_token:
                    self.update_failed.emit("未设置访问令牌，请重新登录")
                    break

                # 获取用户游戏数据
                user_data_response = self.api_client.user.get_character_detail()
                if user_data_response.get('success'):
                    self.user_data_updated.emit(user_data_response['data'])
                else:
                    error_msg = user_data_response.get('message', '获取用户数据失败')
                    self.update_failed.emit(f"用户数据: {error_msg}")

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




class CultivationWorker(QObject):
    """修炼相关异步操作工作类"""

    # 信号定义
    cultivation_focus_changed = pyqtSignal(dict)  # 修炼方向切换完成信号
    cultivation_completed = pyqtSignal(dict)  # 修炼完成信号
    cultivation_started = pyqtSignal(dict)  # 修炼开始信号
    cultivation_countdown_ready = pyqtSignal(dict)  # 修炼倒计时准备就绪信号
    operation_failed = pyqtSignal(str)  # 操作失败信号

    # 数据更新信号（复用DataUpdateWorker的信号定义）
    user_data_updated = pyqtSignal(dict)  # 用户数据更新信号
    cultivation_status_updated = pyqtSignal(dict)  # 修炼状态更新信号
    luck_info_updated = pyqtSignal(dict)  # 气运信息更新信号

    # 内部触发信号（用于从主线程触发后台线程操作）
    force_cultivation_cycle_requested = pyqtSignal()  # 请求强制修炼周期信号
    refresh_all_data_requested = pyqtSignal()  # 请求刷新所有数据信号
    change_cultivation_focus_requested = pyqtSignal(str)  # 请求切换修炼方向信号
    get_cultivation_countdown_info_requested = pyqtSignal(str)  # 请求获取修炼倒计时信息信号
    get_cultivation_status_for_restart_requested = pyqtSignal()  # 请求获取修炼状态用于重启信号
    get_cultivation_status_for_auto_start_requested = pyqtSignal()  # 请求获取修炼状态用于自动开始信号

    def __init__(self, api_client: GameAPIClient):
        super().__init__()
        self.api_client = api_client

        # 连接内部信号到对应的方法
        self.force_cultivation_cycle_requested.connect(self.force_cultivation_cycle)
        self.refresh_all_data_requested.connect(self.refresh_all_data)
        self.change_cultivation_focus_requested.connect(self.change_cultivation_focus)
        self.get_cultivation_countdown_info_requested.connect(self.get_cultivation_countdown_info)
        self.get_cultivation_status_for_restart_requested.connect(self.get_cultivation_status_for_restart)
        self.get_cultivation_status_for_auto_start_requested.connect(self.get_cultivation_status_for_auto_start)

    def change_cultivation_focus(self, focus_type: str):
        """异步切换修炼方向"""
        try:
            response = self.api_client.game.change_cultivation_focus(focus_type)
            if response.get('success'):
                self.cultivation_focus_changed.emit({
                    'focus_type': focus_type,
                    'response': response
                })
            else:
                error_msg = response.get('message', '修炼方向切换失败')
                self.operation_failed.emit(f"切换修炼方向失败: {error_msg}")
        except Exception as e:
            self.operation_failed.emit(f"切换修炼方向时发生错误: {str(e)}")

    def get_cultivation_countdown_info(self, focus_type: str):
        """异步获取修炼倒计时信息"""
        try:
            response = self.api_client.game.get_next_cultivation_time()
            if response.get('success'):
                self.cultivation_countdown_ready.emit({
                    'focus_type': focus_type,
                    'response': response
                })
            else:
                error_msg = response.get('message', '获取修炼时间失败')
                self.operation_failed.emit(f"获取修炼倒计时失败: {error_msg}")
        except Exception as e:
            self.operation_failed.emit(f"获取修炼倒计时时发生错误: {str(e)}")

    def force_cultivation_cycle(self):
        """异步强制执行修炼周期"""
        try:
            force_response = self.api_client.game.force_cultivation_cycle()
            self.cultivation_completed.emit({
                'response': force_response
            })
        except Exception as e:
            self.operation_failed.emit(f"修炼完成处理失败: {str(e)}")

    def start_cultivation(self, focus_type: str):
        """异步开始修炼"""
        try:
            start_response = self.api_client.game.start_cultivation(focus_type)
            self.cultivation_started.emit({
                'focus_type': focus_type,
                'response': start_response
            })
        except Exception as e:
            self.operation_failed.emit(f"开始修炼失败: {str(e)}")

    def get_cultivation_status_for_restart(self):
        """异步获取修炼状态用于重启倒计时"""
        try:
            cultivation_response = self.api_client.game.get_cultivation_status()
            if cultivation_response.get('success'):
                cultivation_data = cultivation_response['data']
                current_focus = cultivation_data.get('cultivation_focus', 'PHYSICAL_ATTACK')
                # 获取倒计时信息
                self.get_cultivation_countdown_info(current_focus)
            else:
                self.operation_failed.emit("获取修炼状态失败")
        except Exception as e:
            self.operation_failed.emit(f"重启修炼倒计时失败: {str(e)}")

    def get_cultivation_status_for_auto_start(self):
        """异步获取修炼状态用于自动开始修炼"""
        try:
            response = self.api_client.game.get_cultivation_status()
            if response.get('success'):
                cultivation_data = response['data']
                is_cultivating = cultivation_data.get('is_cultivating', False)
                current_focus = cultivation_data.get('cultivation_focus', 'PHYSICAL_ATTACK')

                if not is_cultivating:
                    # 需要开始修炼
                    self.start_cultivation(current_focus)
                else:
                    # 已经在修炼，直接启动倒计时
                    self.cultivation_started.emit({
                        'focus_type': current_focus,
                        'response': {'success': True, 'already_cultivating': True}
                    })
            else:
                self.operation_failed.emit("无法获取修炼状态，跳过自动修炼")
        except Exception as e:
            self.operation_failed.emit(f"自动修炼启动异常: {str(e)}")

    def refresh_all_data(self):
        """异步刷新所有游戏数据"""
        try:
            # 获取用户游戏数据
            user_data_response = self.api_client.user.get_character_detail()
            if user_data_response.get('success'):
                self.user_data_updated.emit(user_data_response['data'])

            # 获取修炼状态
            cultivation_response = self.api_client.game.get_cultivation_status()
            if cultivation_response.get('success'):
                self.cultivation_status_updated.emit(cultivation_response['data'])

            # 获取气运信息
            luck_response = self.api_client.game.get_luck_info()
            if luck_response.get('success'):
                self.luck_info_updated.emit(luck_response['data'])

        except Exception as e:
            self.operation_failed.emit(f"刷新数据失败: {str(e)}")





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

        # 初始化修炼工作线程
        self.cultivation_thread = QThread()
        self.cultivation_worker = CultivationWorker(self.api_client)
        self.cultivation_worker.moveToThread(self.cultivation_thread)
        self.setup_cultivation_worker_connections()
        self.cultivation_thread.start()

        # 界面组件
        self.upper_area_widget = None
        self.lower_area_widget = None

        self.init_ui()
        self.setup_connections()

        # 检查登录状态
        if not self.state_manager.is_logged_in or self.state_manager.is_token_expired():
            # 延迟触发登出，确保窗口已完全初始化
            QTimer.singleShot(100, self.state_manager.logout)
            return

        # 优化启动流程，避免过度并发
        # 第一阶段：界面初始化完成后加载数据（给界面更多时间渲染）
        if self.state_manager.user_data:
            QTimer.singleShot(1000, self.load_initial_data_async)  # 使用异步版本，避免阻塞UI
        else:
            QTimer.singleShot(1500, self.load_initial_data_async)  # 使用异步版本，避免阻塞UI

        # 第二阶段：数据加载完成后启动后台服务（进一步延迟）
        QTimer.singleShot(3000, self.start_background_services)  # 3秒后启动后台服务

    def start_background_services(self):
        """启动后台服务（分阶段启动，避免过度并发）"""
        # 第一步：启动数据更新线程
        self.start_data_updates()

        # 第二步：延迟启动自动修炼（再延迟2秒）
        QTimer.singleShot(2000, self.start_auto_cultivation)

    def start_data_updates(self):
        """启动数据更新线程"""
        if not self.update_worker.isRunning():
            self.update_worker.start_updates()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("纸上修仙模拟器")

        # 设置窗口图标
        try:
            import os
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(project_root, "appicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"⚠️ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"❌ 设置窗口图标失败: {e}")

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
            self.upper_area_widget.cave_window_requested.connect(self.show_cave_window)

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
        except Exception as e:
            pass  # 聊天信号连接失败

    def on_daily_sign_requested(self):
        """处理每日签到请求"""
        try:
            response = self.api_client.game.daily_sign_in()
            if response.get('success'):
                data = response['data']
                message = data.get('message', '签到成功')
                QMessageBox.information(self, "签到成功", message)
                # 异步刷新数据
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
        """处理修炼方向变更（异步版本）"""
        # 发送信号到后台线程处理修炼方向切换
        self.cultivation_worker.change_cultivation_focus_requested.emit(focus_type)

    def on_cultivation_focus_changed_async(self, data: dict):
        """异步修炼方向切换完成处理"""
        focus_type = data['focus_type']
        response = data['response']

        focus_info = CULTIVATION_FOCUS_TYPES.get(focus_type, {})
        focus_name = focus_info.get('name', '未知')
        focus_icon = focus_info.get('icon', '❓')

        # 添加日志（使用特殊类型，只保留最后一条）
        if self.lower_area_widget:
            cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
            if cultivation_log_widget:
                cultivation_log_widget.add_system_log(f"修炼方向已切换为: {focus_name}{focus_icon}", "cultivation_switch")

                # 立即停止当前倒计时并启动新的倒计时（立即切换，无需等待）
                cultivation_log_widget.stop_countdown()
                # 异步获取倒计时信息
                self.cultivation_worker.get_cultivation_countdown_info_requested.emit(focus_type)

    def on_cultivation_operation_failed(self, error_message: str):
        """修炼操作失败处理"""
        if "401" in error_message or "认证失败" in error_message:
            QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
            self.state_manager.logout()
        else:
            QMessageBox.warning(self, "操作失败", error_message)
            # 异步刷新数据以恢复状态
            self.load_initial_data()

    def start_cultivation_countdown(self, focus_type: str):
        """启动修炼倒计时（异步版本）"""
        # 发送信号到后台线程获取倒计时信息
        self.cultivation_worker.get_cultivation_countdown_info_requested.emit(focus_type)

    def on_cultivation_countdown_ready_async(self, data: dict):
        """异步修炼倒计时信息准备完成处理"""
        focus_type = data['focus_type']
        response = data['response']

        if response.get('success'):
            data_info = response['data']
            remaining_seconds = data_info.get('remaining_seconds', 5)
            server_time_str = data_info.get('server_time')

            # 导入datetime相关模块
            from datetime import datetime, timedelta
            import dateutil.parser

            if server_time_str:
                server_time = dateutil.parser.parse(server_time_str).replace(tzinfo=None)
                client_time = datetime.now()
                time_offset = (server_time - client_time).total_seconds()



                # 基于服务器时间计算下次修炼时间
                if remaining_seconds <= 0:
                    # 修炼时间已到，立即开始下一轮倒计时
                    cultivation_interval = data_info.get('cultivation_interval', 5)
                    next_time = client_time + timedelta(seconds=cultivation_interval) + timedelta(seconds=time_offset)
                else:
                    # 使用服务器返回的剩余时间，但调整时间差
                    next_time = client_time + timedelta(seconds=remaining_seconds) + timedelta(seconds=time_offset)
            else:
                # 没有服务器时间信息，使用本地时间
                if remaining_seconds <= 0:
                    remaining_seconds = 5
                next_time = datetime.now() + timedelta(seconds=remaining_seconds)



            # 启动修炼倒计时
            if self.lower_area_widget:
                cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
                if cultivation_log_widget:
                    cultivation_log_widget.start_cultivation_countdown(focus_type, next_time)

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
            # 这里可以添加更多的新消息提示逻辑，比如闪烁按钮等
            pass

    def on_cultivation_completed(self):
        """修炼完成处理（异步版本）"""
        # 发送信号到后台线程处理修炼完成
        self.cultivation_worker.force_cultivation_cycle_requested.emit()

    def on_cultivation_completed_async(self, data: dict):
        """异步修炼完成处理"""
        force_response = data['response']

        # 如果有修炼结果数据，添加到修炼日志
        if force_response.get('success') and force_response.get('data'):
            cultivation_result = force_response['data']

            if self.lower_area_widget:
                cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
                if cultivation_log_widget:
                    cultivation_log_widget.add_cultivation_result_log(cultivation_result)
        else:
            # 如果修炼周期未到，说明客户端倒计时与服务器不同步
            remaining_time = force_response.get('data', {}).get('remaining_time', 0)


            if remaining_time > 0 and remaining_time <= 3:  # 如果剩余时间很短，稍后重试
                QTimer.singleShot(int(remaining_time * 1000) + 200, self.on_cultivation_completed)
                return

        # 异步刷新角色数据和修炼状态
        self.cultivation_worker.refresh_all_data_requested.emit()

        # 延迟一点时间后重新启动倒计时，确保数据已更新
        QTimer.singleShot(1500, self.restart_cultivation_countdown)

    def on_cultivation_started_async(self, data: dict):
        """异步修炼开始处理"""
        focus_type = data['focus_type']
        response = data['response']

        if response.get('success'):
            if not response.get('already_cultivating', False):
                # 新开始修炼
                focus_info = CULTIVATION_FOCUS_TYPES.get(focus_type, {})
                focus_name = focus_info.get('name', '体修')
                focus_icon = focus_info.get('icon', '🛡️')

                # 添加系统日志
                if self.lower_area_widget:
                    cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
                    if cultivation_log_widget:
                        cultivation_log_widget.add_system_log(f"自动开始修炼: {focus_name}{focus_icon}")

            # 启动修炼倒计时
            self.start_cultivation_countdown(focus_type)
        else:
            error_msg = response.get('message', '自动修炼启动失败')

    def restart_cultivation_countdown(self):
        """重新启动修炼倒计时（异步版本）"""
        # 发送信号到后台线程获取修炼状态并重启倒计时
        self.cultivation_worker.get_cultivation_status_for_restart_requested.emit()

    def setup_worker_connections(self):
        """设置工作线程信号连接"""
        self.update_worker.user_data_updated.connect(self.on_user_data_updated)
        self.update_worker.cultivation_status_updated.connect(self.on_cultivation_status_updated)
        self.update_worker.luck_info_updated.connect(self.on_luck_info_updated)
        self.update_worker.update_failed.connect(self.on_update_failed)

    def setup_cultivation_worker_connections(self):
        """设置修炼工作线程的信号连接"""
        self.cultivation_worker.cultivation_focus_changed.connect(self.on_cultivation_focus_changed_async)
        self.cultivation_worker.cultivation_completed.connect(self.on_cultivation_completed_async)
        self.cultivation_worker.cultivation_started.connect(self.on_cultivation_started_async)
        self.cultivation_worker.cultivation_countdown_ready.connect(self.on_cultivation_countdown_ready_async)
        self.cultivation_worker.operation_failed.connect(self.on_cultivation_operation_failed)

        # 连接数据刷新信号（复用DataUpdateWorker的信号）
        self.cultivation_worker.user_data_updated.connect(self.on_user_data_updated)
        self.cultivation_worker.cultivation_status_updated.connect(self.on_cultivation_status_updated)
        self.cultivation_worker.luck_info_updated.connect(self.on_luck_info_updated)

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
                self.websocket_client.connect()
        except Exception as e:
            pass  # WebSocket连接失败
            import traceback
            traceback.print_exc()

    def load_initial_data(self):
        """加载初始数据（异步版本）"""
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

        # 发送信号到后台线程获取最新的游戏数据
        self.cultivation_worker.refresh_all_data_requested.emit()

    def load_initial_data_async(self):
        """加载初始数据（异步版本，用于初始化时）"""
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

        # 异步获取最新的游戏数据
        self.cultivation_worker.refresh_all_data_requested.emit()

    def load_initial_data_sync(self):
        """加载初始数据（同步版本，仅用于初始化时）"""
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

            # 获取最新的游戏数据
            user_data_response = self.api_client.user.get_character_detail()
            if user_data_response.get('success'):
                self.on_user_data_updated(user_data_response['data'])

            cultivation_response = self.api_client.game.get_cultivation_status()
            if cultivation_response.get('success'):
                self.on_cultivation_status_updated(cultivation_response['data'])

            luck_response = self.api_client.game.get_luck_info()
            if luck_response.get('success'):
                self.on_luck_info_updated(luck_response['data'])

        except APIException as e:
            if "401" in str(e):
                QMessageBox.warning(self, "认证失败", "登录状态已过期，请重新登录")
                self.state_manager.logout()  # 触发登出，会自动关闭窗口
            else:
                QMessageBox.warning(self, "数据加载失败", f"无法加载游戏数据: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def on_user_data_updated(self, user_data: Dict[str, Any]):
        """用户数据更新处理"""
        # 更新状态管理器中的用户数据
        self.state_manager.update_user_data(user_data)

        # 更新界面显示
        if self.upper_area_widget:
            self.upper_area_widget.update_character_info(user_data)

    def on_cultivation_status_updated(self, cultivation_data: Dict[str, Any]):
        """修炼状态更新处理"""
        if self.upper_area_widget:
            self.upper_area_widget.update_cultivation_status(cultivation_data)

        # 更新修炼日志组件
        if self.lower_area_widget:
            cultivation_log_widget = self.lower_area_widget.get_cultivation_log_widget()
            if cultivation_log_widget:
                cultivation_log_widget.update_cultivation_status(cultivation_data)

                # 连接修炼完成信号（只连接一次）- 使用新的异步版本
                if not hasattr(self, '_cultivation_signal_connected'):
                    cultivation_log_widget.cultivation_completed.connect(self.on_cultivation_completed)
                    self._cultivation_signal_connected = True

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
                if self.lower_area_widget:
                    self.lower_area_widget.toggle_view()
            except Exception as e:
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
            pass

        except Exception as e:
            pass  # 处理boss被击败事件失败

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
        """启动自动修炼（异步版本）"""
        # 检查登录状态
        if not self.state_manager.is_logged_in or self.state_manager.is_token_expired():
            return

        # 发送信号到后台线程获取修炼状态并自动开始修炼
        self.cultivation_worker.get_cultivation_status_for_auto_start_requested.emit()

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
        pass

    def on_websocket_disconnected(self):
        """WebSocket连接断开"""
        pass

    def on_websocket_error(self, error_message: str):
        """WebSocket错误"""
        pass  # 可以在这里添加错误处理逻辑

    def on_websocket_message(self, message_data: dict):
        """处理WebSocket消息"""
        message_type = message_data.get("type", "unknown")

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 断开WebSocket连接
            if hasattr(self, 'websocket_client'):
                self.websocket_client.disconnect()

            # 停止数据更新线程
            if hasattr(self, 'update_worker') and self.update_worker.isRunning():
                self.update_worker.stop_updates()

                # 等待线程结束，但设置超时避免卡死
                if not self.update_worker.wait(3000):  # 等待3秒
                    self.update_worker.terminate()
                    self.update_worker.wait(1000)  # 再等1秒

            # 停止修炼工作线程
            if hasattr(self, 'cultivation_thread') and self.cultivation_thread.isRunning():
                print("⏹️ 停止修炼工作线程...")
                self.cultivation_thread.quit()

                # 等待线程结束，但设置超时避免卡死
                if not self.cultivation_thread.wait(3000):  # 等待3秒
                    self.cultivation_thread.terminate()
                    self.cultivation_thread.wait(1000)  # 再等1秒

            event.accept()

        except Exception as e:
            event.accept()  # 即使出错也要关闭窗口


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("纸上修仙模拟器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Simonius")

    # 设置应用程序图标
    try:
        import os
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(project_root, "appicon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠️ 图标文件不存在: {icon_path}")
    except Exception as e:
        print(f"❌ 设置应用程序图标失败: {e}")

    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
