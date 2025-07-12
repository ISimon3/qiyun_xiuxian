# 登录/注册窗口

import re
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget,
    QMessageBox, QProgressBar, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette

from client.network.api_client import GameAPIClient, APIException
from client.state_manager import get_state_manager


class LoginWorker(QThread):
    """登录工作线程"""

    # 信号定义
    login_success = pyqtSignal(dict, dict)  # 登录成功信号 (user_info, token_data)
    login_failed = pyqtSignal(str)          # 登录失败信号
    register_success = pyqtSignal(dict)     # 注册成功信号
    register_failed = pyqtSignal(str)       # 注册失败信号

    def __init__(self, api_client: GameAPIClient):
        super().__init__()
        self.api_client = api_client
        self.operation = None
        self.params = {}

    def login(self, username: str, password: str):
        """设置登录操作"""
        self.operation = 'login'
        self.params = {'username': username, 'password': password}

    def register(self, username: str, email: str, password: str):
        """设置注册操作"""
        self.operation = 'register'
        self.params = {'username': username, 'email': email, 'password': password}

    def run(self):
        """执行操作"""
        try:
            if self.operation == 'login':
                response = self.api_client.auth.login(
                    self.params['username'],
                    self.params['password']
                )
                if response.get('success'):
                    user_info = response['data']['user']
                    token_data = response['data']['token']
                    self.login_success.emit(user_info, token_data)
                else:
                    self.login_failed.emit(response.get('message', '登录失败'))

            elif self.operation == 'register':
                response = self.api_client.auth.register(
                    self.params['username'],
                    self.params['email'],
                    self.params['password']
                )
                if response.get('success'):
                    self.register_success.emit(response['data'])
                else:
                    self.register_failed.emit(response.get('message', '注册失败'))

        except APIException as e:
            if self.operation == 'login':
                self.login_failed.emit(str(e))
            elif self.operation == 'register':
                self.register_failed.emit(str(e))
        except Exception as e:
            error_msg = f"操作失败: {str(e)}"
            if self.operation == 'login':
                self.login_failed.emit(error_msg)
            elif self.operation == 'register':
                self.register_failed.emit(error_msg)


class LoginTab(QWidget):
    """登录标签页"""

    # 信号定义
    login_requested = pyqtSignal(str, str)  # 登录请求信号

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("用户登录")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # 用户名输入
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setMinimumHeight(35)
        form_layout.addRow("用户名:", self.username_edit)

        # 密码输入
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(35)
        form_layout.addRow("密码:", self.password_edit)

        layout.addLayout(form_layout)

        # 记住登录状态
        self.remember_checkbox = QCheckBox("记住登录状态")
        self.remember_checkbox.setChecked(True)
        layout.addWidget(self.remember_checkbox)

        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.on_login_clicked)
        layout.addWidget(self.login_button)

        # 回车键登录
        self.username_edit.returnPressed.connect(self.on_login_clicked)
        self.password_edit.returnPressed.connect(self.on_login_clicked)

        self.setLayout(layout)

    def on_login_clicked(self):
        """登录按钮点击事件"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        # 输入验证
        if not username:
            QMessageBox.warning(self, "输入错误", "请输入用户名")
            self.username_edit.setFocus()
            return

        if not password:
            QMessageBox.warning(self, "输入错误", "请输入密码")
            self.password_edit.setFocus()
            return

        # 发送登录请求信号
        self.login_requested.emit(username, password)

    def set_enabled(self, enabled: bool):
        """设置控件启用状态"""
        self.username_edit.setEnabled(enabled)
        self.password_edit.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)

    def clear_form(self):
        """清空表单"""
        self.password_edit.clear()
        self.username_edit.setFocus()


class RegisterTab(QWidget):
    """注册标签页"""

    # 信号定义
    register_requested = pyqtSignal(str, str, str)  # 注册请求信号

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("用户注册")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # 用户名输入
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("3-20个字符，支持字母数字下划线")
        self.username_edit.setMinimumHeight(35)
        form_layout.addRow("用户名:", self.username_edit)

        # 邮箱输入
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("请输入有效的邮箱地址")
        self.email_edit.setMinimumHeight(35)
        form_layout.addRow("邮箱:", self.email_edit)

        # 密码输入
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("6-50个字符")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(35)
        form_layout.addRow("密码:", self.password_edit)

        # 确认密码输入
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("请再次输入密码")
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setMinimumHeight(35)
        form_layout.addRow("确认密码:", self.confirm_password_edit)

        layout.addLayout(form_layout)

        # 注册按钮
        self.register_button = QPushButton("注册")
        self.register_button.setMinimumHeight(40)
        self.register_button.clicked.connect(self.on_register_clicked)
        layout.addWidget(self.register_button)

        # 回车键注册
        self.confirm_password_edit.returnPressed.connect(self.on_register_clicked)

        self.setLayout(layout)

    def on_register_clicked(self):
        """注册按钮点击事件"""
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        # 输入验证
        if not self.validate_input(username, email, password, confirm_password):
            return

        # 发送注册请求信号
        self.register_requested.emit(username, email, password)

    def validate_input(self, username: str, email: str, password: str, confirm_password: str) -> bool:
        """验证输入数据"""
        # 用户名验证
        if not username:
            QMessageBox.warning(self, "输入错误", "请输入用户名")
            self.username_edit.setFocus()
            return False

        if len(username) < 3 or len(username) > 20:
            QMessageBox.warning(self, "输入错误", "用户名长度必须在3-20个字符之间")
            self.username_edit.setFocus()
            return False

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            QMessageBox.warning(self, "输入错误", "用户名只能包含字母、数字和下划线")
            self.username_edit.setFocus()
            return False

        # 邮箱验证
        if not email:
            QMessageBox.warning(self, "输入错误", "请输入邮箱地址")
            self.email_edit.setFocus()
            return False

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            QMessageBox.warning(self, "输入错误", "请输入有效的邮箱地址")
            self.email_edit.setFocus()
            return False

        # 密码验证
        if not password:
            QMessageBox.warning(self, "输入错误", "请输入密码")
            self.password_edit.setFocus()
            return False

        if len(password) < 6 or len(password) > 50:
            QMessageBox.warning(self, "输入错误", "密码长度必须在6-50个字符之间")
            self.password_edit.setFocus()
            return False

        # 确认密码验证
        if password != confirm_password:
            QMessageBox.warning(self, "输入错误", "两次输入的密码不一致")
            self.confirm_password_edit.setFocus()
            return False

        return True

    def set_enabled(self, enabled: bool):
        """设置控件启用状态"""
        self.username_edit.setEnabled(enabled)
        self.email_edit.setEnabled(enabled)
        self.password_edit.setEnabled(enabled)
        self.confirm_password_edit.setEnabled(enabled)
        self.register_button.setEnabled(enabled)

    def clear_form(self):
        """清空表单"""
        self.username_edit.clear()
        self.email_edit.clear()
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        self.username_edit.setFocus()


class LoginWindow(QWidget):
    """登录窗口主类"""

    # 信号定义
    login_success = pyqtSignal(dict)  # 登录成功信号

    def __init__(self, server_url: str = "http://localhost:8000"):
        super().__init__()

        # 初始化组件
        self.api_client = GameAPIClient(server_url)
        self.state_manager = get_state_manager()
        self.worker = LoginWorker(self.api_client)

        # 连接工作线程信号
        self.worker.login_success.connect(self.on_login_success)
        self.worker.login_failed.connect(self.on_login_failed)
        self.worker.register_success.connect(self.on_register_success)
        self.worker.register_failed.connect(self.on_register_failed)

        self.init_ui()
        self.setup_connections()

        # 检查服务器连接
        self.check_server_connection()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("气运修仙 - 登录")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 服务器状态栏
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(30)
        self.status_frame.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc;")

        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.server_status_label = QLabel("检查服务器连接中...")
        self.server_status_label.setStyleSheet("color: #666; font-size: 12px;")
        status_layout.addWidget(self.server_status_label)
        status_layout.addStretch()

        main_layout.addWidget(self.status_frame)

        # 标签页容器
        self.tab_widget = QTabWidget()

        # 登录标签页
        self.login_tab = LoginTab()
        self.tab_widget.addTab(self.login_tab, "登录")

        # 注册标签页
        self.register_tab = RegisterTab()
        self.tab_widget.addTab(self.register_tab, "注册")

        main_layout.addWidget(self.tab_widget)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)

        # 居中显示
        self.center_window()

    def setup_connections(self):
        """设置信号连接"""
        # 连接标签页信号
        self.login_tab.login_requested.connect(self.on_login_requested)
        self.register_tab.register_requested.connect(self.on_register_requested)

    def center_window(self):
        """窗口居中显示"""
        screen = self.screen().availableGeometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())

    def check_server_connection(self):
        """检查服务器连接状态"""
        try:
            if self.api_client.test_connection():
                self.server_status_label.setText("✅ 服务器连接正常")
                self.server_status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            else:
                self.server_status_label.setText("❌ 无法连接到服务器")
                self.server_status_label.setStyleSheet("color: #F44336; font-size: 12px;")
        except Exception:
            self.server_status_label.setText("❌ 服务器连接异常")
            self.server_status_label.setStyleSheet("color: #F44336; font-size: 12px;")

    def on_login_requested(self, username: str, password: str):
        """处理登录请求"""
        self.set_loading(True, "正在登录...")
        self.worker.login(username, password)
        self.worker.start()

    def on_register_requested(self, username: str, email: str, password: str):
        """处理注册请求"""
        self.set_loading(True, "正在注册...")
        self.worker.register(username, email, password)
        self.worker.start()

    def set_loading(self, loading: bool, message: str = ""):
        """设置加载状态"""
        self.progress_bar.setVisible(loading)
        self.login_tab.set_enabled(not loading)
        self.register_tab.set_enabled(not loading)

        if loading and message:
            self.server_status_label.setText(message)
            self.server_status_label.setStyleSheet("color: #2196F3; font-size: 12px;")

    def on_login_success(self, user_info: dict, token_data: dict):
        """登录成功处理"""
        self.set_loading(False)

        # 更新状态管理器
        self.state_manager.login(user_info, token_data)

        # 显示成功消息
        QMessageBox.information(self, "登录成功", f"欢迎回来，{user_info.get('username')}！")

        # 发送登录成功信号
        self.login_success.emit(user_info)

        # 关闭登录窗口
        self.close()

    def on_login_failed(self, error_message: str):
        """登录失败处理"""
        self.set_loading(False)
        self.check_server_connection()  # 重新检查服务器状态

        QMessageBox.warning(self, "登录失败", error_message)
        self.login_tab.clear_form()

    def on_register_success(self, user_data: dict):
        """注册成功处理"""
        self.set_loading(False)

        username = user_data.get('username', '')
        QMessageBox.information(
            self,
            "注册成功",
            f"用户 {username} 注册成功！\n请使用新账户登录。"
        )

        # 切换到登录标签页并填入用户名
        self.tab_widget.setCurrentIndex(0)
        self.login_tab.username_edit.setText(username)
        self.login_tab.password_edit.setFocus()

        # 清空注册表单
        self.register_tab.clear_form()

    def on_register_failed(self, error_message: str):
        """注册失败处理"""
        self.set_loading(False)
        self.check_server_connection()  # 重新检查服务器状态

        QMessageBox.warning(self, "注册失败", error_message)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果工作线程正在运行，等待其完成
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()

        event.accept()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("气运修仙")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("气运修仙工作室")

    # 创建并显示登录窗口
    login_window = LoginWindow()
    login_window.show()

    sys.exit(app.exec())
