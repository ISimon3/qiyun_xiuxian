# 可视化数据库管理工具

import os
import sys
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QTabWidget,
    QMessageBox, QDialog, QFormLayout, QCheckBox, QGroupBox,
    QHeaderView, QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QIcon

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.database.models import User, Character
from server.config import settings
from shared.constants import CULTIVATION_REALMS, SPIRITUAL_ROOTS
from shared.utils import get_realm_name, get_luck_level_name


class DatabaseWorker(QThread):
    """数据库操作工作线程"""
    
    # 信号定义
    data_loaded = pyqtSignal(list)  # 数据加载完成
    operation_completed = pyqtSignal(bool, str)  # 操作完成 (成功, 消息)
    progress_updated = pyqtSignal(int)  # 进度更新
    
    def __init__(self):
        super().__init__()
        self.database_url = self._get_database_url()
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        self.operation = None
        self.params = {}
    
    def _get_database_url(self):
        """获取数据库URL"""
        # 使用配置中的正确数据库路径
        database_url = settings.get_database_url()
        if database_url.startswith("sqlite+aiosqlite"):
            database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
        elif database_url.startswith("postgresql+asyncpg"):
            database_url = database_url.replace("postgresql+asyncpg", "postgresql")
        return database_url
    
    def load_users(self):
        """加载用户数据"""
        self.operation = 'load_users'
        self.start()
    
    def load_user_game_data(self):
        """加载用户游戏数据"""
        self.operation = 'load_user_game_data'
        self.start()

    def update_user(self, user_id: int, data: Dict[str, Any]):
        """更新用户数据"""
        self.operation = 'update_user'
        self.params = {'user_id': user_id, 'data': data}
        self.start()

    def update_user_game_data(self, character_id: int, data: Dict[str, Any]):
        """更新用户游戏数据"""
        self.operation = 'update_user_game_data'
        self.params = {'character_id': character_id, 'data': data}
        self.start()
    
    def ban_user(self, user_id: int, ban: bool):
        """封禁/解封用户"""
        self.operation = 'ban_user'
        self.params = {'user_id': user_id, 'ban': ban}
        self.start()
    
    def delete_user(self, user_id: int):
        """删除用户"""
        self.operation = 'delete_user'
        self.params = {'user_id': user_id}
        self.start()
    
    def run(self):
        """执行数据库操作"""
        try:
            with self.SessionLocal() as session:
                if self.operation == 'load_users':
                    users = session.query(User).all()
                    user_data = []
                    for i, user in enumerate(users):
                        self.progress_updated.emit(int((i + 1) / len(users) * 100))

                        # 查询用户是否有游戏数据
                        has_game_data = session.query(Character).filter(Character.user_id == user.id).count() > 0

                        user_info = {
                            'id': user.id,
                            'username': user.username or '',
                            'email': user.email or '',
                            'hashed_password': user.hashed_password or '',
                            'plain_password': user.plain_password or '',  # 直接获取明文密码
                            'is_active': user.is_active if user.is_active is not None else True,
                            'is_verified': user.is_verified if user.is_verified is not None else False,
                            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录',
                            'has_game_data': '是' if has_game_data else '否'
                        }
                        user_data.append(user_info)

                    self.data_loaded.emit(user_data)
                
                elif self.operation == 'load_user_game_data':
                    characters = session.query(Character).all()
                    game_data = []
                    for i, char in enumerate(characters):
                        self.progress_updated.emit(int((i + 1) / len(characters) * 100))

                        # 查询关联的用户信息
                        user = session.query(User).filter(User.id == char.user_id).first()
                        username = user.username if user else '未知'

                        game_info = {
                            'id': char.id,
                            'user_id': char.user_id,
                            'username': username,
                            'name': char.name or '',
                            'cultivation_exp': char.cultivation_exp or 0,
                            'cultivation_realm': char.cultivation_realm or 0,
                            'realm_name': get_realm_name(char.cultivation_realm or 0),
                            'spiritual_root': char.spiritual_root or '未知',
                            'luck_value': char.luck_value or 50,
                            'luck_level': get_luck_level_name(char.luck_value or 50),
                            'gold': char.gold or 0,
                            'spirit_stone': char.spirit_stone or 0,
                            'created_at': char.created_at.strftime('%Y-%m-%d %H:%M:%S') if char.created_at else '',
                            'updated_at': char.updated_at.strftime('%Y-%m-%d %H:%M:%S') if char.updated_at else '',
                            'last_active': char.last_active.strftime('%Y-%m-%d %H:%M:%S') if char.last_active else '从未活跃',
                            'cultivation_focus': char.cultivation_focus or '无'
                        }
                        game_data.append(game_info)

                    self.data_loaded.emit(game_data)
                
                elif self.operation == 'update_user':
                    user_id = self.params['user_id']
                    data = self.params['data']
                    user = session.query(User).filter(User.id == user_id).first()
                    if user:
                        for key, value in data.items():
                            if hasattr(user, key):
                                setattr(user, key, value)
                        session.commit()
                        self.operation_completed.emit(True, f"用户 {user.username} 更新成功")
                    else:
                        self.operation_completed.emit(False, "用户不存在")
                
                elif self.operation == 'update_user_game_data':
                    character_id = self.params['character_id']
                    data = self.params['data']
                    char = session.query(Character).filter(Character.id == character_id).first()
                    if char:
                        for key, value in data.items():
                            if hasattr(char, key):
                                setattr(char, key, value)
                        session.commit()
                        self.operation_completed.emit(True, f"用户 {char.name} 的游戏数据更新成功")
                    else:
                        self.operation_completed.emit(False, "用户游戏数据不存在")
                
                elif self.operation == 'ban_user':
                    user_id = self.params['user_id']
                    ban = self.params['ban']
                    user = session.query(User).filter(User.id == user_id).first()
                    if user:
                        user.is_active = not ban
                        session.commit()
                        action = "封禁" if ban else "解封"
                        self.operation_completed.emit(True, f"用户 {user.username} {action}成功")
                    else:
                        self.operation_completed.emit(False, "用户不存在")
                
                elif self.operation == 'delete_user':
                    user_id = self.params['user_id']
                    user = session.query(User).filter(User.id == user_id).first()
                    if user:
                        username = user.username
                        session.delete(user)
                        session.commit()
                        self.operation_completed.emit(True, f"用户 {username} 删除成功")
                    else:
                        self.operation_completed.emit(False, "用户不存在")
                        
        except Exception as e:
            self.operation_completed.emit(False, f"操作失败: {str(e)}")




class UserEditDialog(QDialog):
    """用户编辑对话框"""
    
    def __init__(self, user_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"编辑用户 - {self.user_data['username']}")
        self.setFixedSize(400, 300)

        # 设置窗口图标
        try:
            self.setWindowIcon(QIcon("appicon.ico"))
        except Exception:
            pass
        
        layout = QVBoxLayout()
        
        # 表单
        form_layout = QFormLayout()
        
        # 用户名
        self.username_edit = QLineEdit(self.user_data['username'])
        form_layout.addRow("用户名:", self.username_edit)
        
        # 邮箱
        self.email_edit = QLineEdit(self.user_data['email'])
        form_layout.addRow("邮箱:", self.email_edit)
        
        # 激活状态
        self.active_checkbox = QCheckBox()
        self.active_checkbox.setChecked(self.user_data['is_active'])
        form_layout.addRow("激活状态:", self.active_checkbox)
        
        # 验证状态
        self.verified_checkbox = QCheckBox()
        self.verified_checkbox.setChecked(self.user_data['is_verified'])
        form_layout.addRow("验证状态:", self.verified_checkbox)

        # 密码重置
        password_group = QGroupBox("密码重置")
        password_layout = QFormLayout()

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setPlaceholderText("留空则不修改密码")
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addRow("新密码:", self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("确认新密码")
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addRow("确认密码:", self.confirm_password_edit)

        password_group.setLayout(password_layout)

        layout.addLayout(form_layout)
        layout.addWidget(password_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """获取编辑后的数据"""
        data = {
            'username': self.username_edit.text(),
            'email': self.email_edit.text(),
            'is_active': self.active_checkbox.isChecked(),
            'is_verified': self.verified_checkbox.isChecked()
        }

        # 检查密码重置
        new_password = self.new_password_edit.text().strip()
        confirm_password = self.confirm_password_edit.text().strip()

        if new_password:
            if new_password != confirm_password:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "密码错误", "两次输入的密码不一致！")
                return None
            if len(new_password) < 6:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "密码错误", "密码长度至少6个字符！")
                return None

            # 生成密码哈希
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            data['hashed_password'] = pwd_context.hash(new_password)

        return data


class UserGameDataEditDialog(QDialog):
    """用户游戏数据编辑对话框"""

    def __init__(self, game_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"编辑用户游戏数据 - {self.game_data['name']}")
        self.setFixedSize(500, 600)

        # 设置窗口图标
        try:
            self.setWindowIcon(QIcon("appicon.ico"))
        except Exception:
            pass

        layout = QVBoxLayout()

        # 表单
        form_layout = QFormLayout()

        # 用户名
        self.name_edit = QLineEdit(self.game_data['name'])
        form_layout.addRow("用户名:", self.name_edit)
        
        # 修为
        self.exp_spinbox = QSpinBox()
        self.exp_spinbox.setRange(0, 999999999)
        self.exp_spinbox.setValue(self.game_data['cultivation_exp'])
        form_layout.addRow("修为:", self.exp_spinbox)

        # 境界
        self.realm_combo = QComboBox()
        self.realm_combo.addItems([f"{i} - {realm}" for i, realm in enumerate(CULTIVATION_REALMS)])
        self.realm_combo.setCurrentIndex(self.game_data['cultivation_realm'])
        form_layout.addRow("境界:", self.realm_combo)
        
        # 灵根
        self.root_combo = QComboBox()
        self.root_combo.addItems(list(SPIRITUAL_ROOTS.keys()))
        self.root_combo.setCurrentText(self.game_data['spiritual_root'])
        form_layout.addRow("灵根:", self.root_combo)

        # 气运
        self.luck_spinbox = QSpinBox()
        self.luck_spinbox.setRange(0, 100)
        self.luck_spinbox.setValue(self.game_data['luck_value'])
        form_layout.addRow("气运值:", self.luck_spinbox)

        # 金币
        self.gold_spinbox = QSpinBox()
        self.gold_spinbox.setRange(0, 999999999)
        self.gold_spinbox.setValue(self.game_data['gold'])
        form_layout.addRow("金币:", self.gold_spinbox)

        # 灵石
        self.spirit_spinbox = QSpinBox()
        self.spirit_spinbox.setRange(0, 999999999)
        self.spirit_spinbox.setValue(self.game_data['spirit_stone'])
        form_layout.addRow("灵石:", self.spirit_spinbox)
        
        # 修炼方向
        self.focus_combo = QComboBox()
        focus_options = ["无", "HP", "PHYSICAL_ATTACK", "MAGIC_ATTACK", "PHYSICAL_DEFENSE", "MAGIC_DEFENSE"]
        self.focus_combo.addItems(focus_options)
        current_focus = self.game_data.get('cultivation_focus', '无')
        if current_focus in focus_options:
            self.focus_combo.setCurrentText(current_focus)
        form_layout.addRow("修炼方向:", self.focus_combo)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """获取编辑后的数据"""
        focus = self.focus_combo.currentText()
        return {
            'name': self.name_edit.text(),
            'cultivation_exp': self.exp_spinbox.value(),
            'cultivation_realm': self.realm_combo.currentIndex(),
            'spiritual_root': self.root_combo.currentText(),
            'luck_value': self.luck_spinbox.value(),
            'gold': self.gold_spinbox.value(),
            'spirit_stone': self.spirit_spinbox.value(),
            'cultivation_focus': focus if focus != '无' else None
        }


class DatabaseAdminMainWindow(QMainWindow):
    """数据库管理主窗口"""

    def __init__(self):
        super().__init__()

        # 数据库工作线程
        self.db_worker = DatabaseWorker()
        self.setup_worker_connections()

        # 数据缓存
        self.users_data = []
        self.game_data = []

        # 防止在加载数据时触发编辑事件
        self.loading_data = False

        self.init_ui()

        # 自动加载数据
        QTimer.singleShot(500, self.load_users_data)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("纸上修仙模拟器 - 数据库管理工具")
        self.setGeometry(100, 100, 1200, 800)

        # 设置窗口图标
        try:
            import os
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(project_root, "appicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"⚠️ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"❌ 设置窗口图标失败: {e}")

        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()

        # 工具栏
        self.create_toolbar(main_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 标签页
        self.tab_widget = QTabWidget()

        # 用户管理标签页
        self.create_users_tab()
        self.tab_widget.addTab(self.users_tab, "👥 用户管理")

        # 游戏数据管理标签页
        self.create_game_data_tab()
        self.tab_widget.addTab(self.game_data_tab, "🎮 游戏数据管理")

        # 添加标签页切换事件
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        central_widget.setLayout(main_layout)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007acc;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    def create_toolbar(self, parent_layout: QVBoxLayout):
        """创建工具栏"""
        toolbar_layout = QHBoxLayout()

        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新数据")
        refresh_button.clicked.connect(self.refresh_current_tab)
        toolbar_layout.addWidget(refresh_button)

        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索用户名、邮箱或角色名...")
        self.search_edit.textChanged.connect(self.filter_data)
        toolbar_layout.addWidget(self.search_edit)

        # 搜索按钮
        search_button = QPushButton("🔍 搜索")
        search_button.clicked.connect(self.filter_data)
        toolbar_layout.addWidget(search_button)

        toolbar_layout.addStretch()

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; padding: 8px;")
        toolbar_layout.addWidget(self.status_label)

        parent_layout.addLayout(toolbar_layout)

    def create_users_tab(self):
        """创建用户管理标签页"""
        self.users_tab = QWidget()
        layout = QVBoxLayout()

        # 操作按钮
        button_layout = QHBoxLayout()

        self.edit_user_button = QPushButton("✏️ 编辑用户")
        self.edit_user_button.clicked.connect(self.edit_selected_user)
        self.edit_user_button.setEnabled(False)
        button_layout.addWidget(self.edit_user_button)

        self.ban_user_button = QPushButton("🚫 封禁用户")
        self.ban_user_button.clicked.connect(self.ban_selected_user)
        self.ban_user_button.setEnabled(False)
        button_layout.addWidget(self.ban_user_button)

        self.unban_user_button = QPushButton("✅ 解封用户")
        self.unban_user_button.clicked.connect(self.unban_selected_user)
        self.unban_user_button.setEnabled(False)
        button_layout.addWidget(self.unban_user_button)

        self.delete_user_button = QPushButton("🗑️ 删除用户")
        self.delete_user_button.clicked.connect(self.delete_selected_user)
        self.delete_user_button.setEnabled(False)
        self.delete_user_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        button_layout.addWidget(self.delete_user_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 用户表格
        self.users_table = QTableWidget()
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.itemSelectionChanged.connect(self.on_user_selection_changed)
        layout.addWidget(self.users_table)

        self.users_tab.setLayout(layout)

    def create_game_data_tab(self):
        """创建游戏数据管理标签页"""
        self.game_data_tab = QWidget()
        layout = QVBoxLayout()

        # 操作按钮
        button_layout = QHBoxLayout()

        self.edit_game_data_button = QPushButton("✏️ 编辑游戏数据")
        self.edit_game_data_button.clicked.connect(self.edit_selected_game_data)
        self.edit_game_data_button.setEnabled(False)
        button_layout.addWidget(self.edit_game_data_button)

        self.reset_game_data_button = QPushButton("🔄 重置游戏数据")
        self.reset_game_data_button.clicked.connect(self.reset_selected_game_data)
        self.reset_game_data_button.setEnabled(False)
        self.reset_game_data_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        button_layout.addWidget(self.reset_game_data_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 游戏数据表格
        self.game_data_table = QTableWidget()
        self.game_data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.game_data_table.setAlternatingRowColors(True)
        self.game_data_table.itemSelectionChanged.connect(self.on_game_data_selection_changed)
        self.game_data_table.itemChanged.connect(self.on_game_data_item_changed)
        layout.addWidget(self.game_data_table)

        self.game_data_tab.setLayout(layout)

    def setup_worker_connections(self):
        """设置工作线程信号连接"""
        self.db_worker.data_loaded.connect(self.on_data_loaded)
        self.db_worker.operation_completed.connect(self.on_operation_completed)
        self.db_worker.progress_updated.connect(self.on_progress_updated)

    def load_users_data(self):
        """加载用户数据"""
        self.status_label.setText("正在加载用户数据...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.db_worker.load_users()

    def load_game_data(self):
        """加载游戏数据"""
        self.status_label.setText("正在加载游戏数据...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.db_worker.load_user_game_data()

    def on_tab_changed(self, index: int):
        """标签页切换处理"""
        if index == 0:  # 用户管理
            if not self.users_data:  # 如果还没有加载用户数据
                self.load_users_data()
        elif index == 1:  # 游戏数据管理
            if not self.game_data:  # 如果还没有加载游戏数据
                self.load_game_data()

    def refresh_current_tab(self):
        """刷新当前标签页数据"""
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:  # 用户管理
            self.load_users_data()
        elif current_index == 1:  # 游戏数据管理
            self.load_game_data()

    def filter_data(self):
        """过滤数据"""
        keyword = self.search_edit.text().lower()
        current_index = self.tab_widget.currentIndex()

        if current_index == 0:  # 用户管理
            self.filter_users_table(keyword)
        elif current_index == 1:  # 游戏数据管理
            self.filter_game_data_table(keyword)

    def filter_users_table(self, keyword: str):
        """过滤用户表格"""
        for row in range(self.users_table.rowCount()):
            show_row = False
            for col in range(self.users_table.columnCount()):
                item = self.users_table.item(row, col)
                if item and keyword in item.text().lower():
                    show_row = True
                    break
            self.users_table.setRowHidden(row, not show_row)

    def filter_game_data_table(self, keyword: str):
        """过滤游戏数据表格"""
        for row in range(self.game_data_table.rowCount()):
            show_row = False
            for col in range(self.game_data_table.columnCount()):
                item = self.game_data_table.item(row, col)
                if item and keyword in item.text().lower():
                    show_row = True
                    break
            self.game_data_table.setRowHidden(row, not show_row)

    def on_data_loaded(self, data: List[Dict[str, Any]]):
        """数据加载完成处理"""
        # 根据数据类型判断，优先检查游戏数据特有字段
        if data and 'cultivation_exp' in data[0]:  # 游戏数据
            self.game_data = data
            self.populate_game_data_table(data)
            self.status_label.setText(f"游戏数据加载完成，共 {len(data)} 条记录")
        elif data and 'email' in data[0]:  # 用户数据
            self.users_data = data
            self.populate_users_table(data)
            self.status_label.setText(f"用户数据加载完成，共 {len(data)} 条记录")

        self.progress_bar.setVisible(False)

    def populate_users_table(self, users_data: List[Dict[str, Any]]):
        """填充用户表格"""
        if not users_data:
            return

        # 设置表格
        headers = ['ID', '用户名', '邮箱', '明文密码', '密码哈希', '激活状态', '验证状态', '创建时间', '最后登录', '有游戏数据']
        self.users_table.setColumnCount(len(headers))
        self.users_table.setHorizontalHeaderLabels(headers)
        self.users_table.setRowCount(len(users_data))

        # 填充数据
        for row, user in enumerate(users_data):
            try:
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))

                # 明文密码
                plain_password = user.get('plain_password', '')
                password_item = QTableWidgetItem(plain_password)
                if plain_password:
                    password_item.setForeground(QColor("#28a745"))  # 绿色显示密码
                else:
                    password_item.setForeground(QColor("#dc3545"))  # 红色显示空密码
                    password_item.setText("无密码")
                self.users_table.setItem(row, 3, password_item)

                # 密码哈希 - 显示前30个字符，后面用...表示
                password_hash = user.get('hashed_password', '')
                if len(password_hash) > 30:
                    display_hash = password_hash[:30] + '...'
                else:
                    display_hash = password_hash
                hash_item = QTableWidgetItem(display_hash)
                hash_item.setToolTip(password_hash)  # 完整密码哈希作为工具提示
                hash_item.setForeground(QColor("#666666"))  # 灰色显示
                self.users_table.setItem(row, 4, hash_item)

                # 激活状态
                is_active = user.get('is_active', True)
                active_item = QTableWidgetItem("✅ 激活" if is_active else "❌ 封禁")
                active_item.setForeground(QColor("#28a745") if is_active else QColor("#dc3545"))
                self.users_table.setItem(row, 5, active_item)

                # 验证状态
                is_verified = user.get('is_verified', False)
                verified_item = QTableWidgetItem("✅ 已验证" if is_verified else "❌ 未验证")
                verified_item.setForeground(QColor("#28a745") if is_verified else QColor("#ffc107"))
                self.users_table.setItem(row, 6, verified_item)

                self.users_table.setItem(row, 7, QTableWidgetItem(user.get('created_at', '')))
                self.users_table.setItem(row, 8, QTableWidgetItem(user.get('last_login', '')))
                self.users_table.setItem(row, 9, QTableWidgetItem(user.get('has_game_data', '否')))

            except Exception as e:
                print(f"填充用户表格第{row}行时出错: {e}")
                print(f"用户数据: {user}")
                continue

        # 调整列宽
        self.users_table.resizeColumnsToContents()
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 用户名列自适应
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 邮箱列自适应
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # 明文密码列可调整
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # 密码哈希列可调整

    def populate_game_data_table(self, game_data: List[Dict[str, Any]]):
        """填充游戏数据表格"""
        if not game_data:
            return

        # 设置加载标志，防止触发编辑事件
        self.loading_data = True

        # 设置表格 - 优化后的列结构
        headers = ['用户ID', '修仙者名', '修为', '境界', '灵根', '气运', '金币', '灵石', '更新时间']
        self.game_data_table.setColumnCount(len(headers))
        self.game_data_table.setHorizontalHeaderLabels(headers)
        self.game_data_table.setRowCount(len(game_data))

        # 填充数据
        for row, data in enumerate(game_data):
            try:
                # 使用用户ID作为唯一标识 - 不可编辑
                id_item = QTableWidgetItem(str(data.get('user_id', '')))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.game_data_table.setItem(row, 0, id_item)

                # 修仙者名（就是用户名）- 可编辑
                name_item = QTableWidgetItem(data.get('name', ''))
                self.game_data_table.setItem(row, 1, name_item)

                # 修为 - 可编辑
                exp_item = QTableWidgetItem(str(data.get('cultivation_exp', 0)))
                self.game_data_table.setItem(row, 2, exp_item)

                # 境界 - 不可编辑（由修为决定）
                realm_item = QTableWidgetItem(data.get('realm_name', ''))
                realm_item.setForeground(QColor("#007acc"))
                realm_item.setFlags(realm_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.game_data_table.setItem(row, 3, realm_item)

                # 灵根 - 不可编辑
                root_item = QTableWidgetItem(data.get('spiritual_root', ''))
                root_item.setFlags(root_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.game_data_table.setItem(row, 4, root_item)

                # 气运 - 不可编辑（由系统管理）
                luck_value = data.get('luck_value', 50)
                luck_level = data.get('luck_level', '平')
                luck_item = QTableWidgetItem(f"{luck_level} ({luck_value})")
                luck_color = "#28a745" if luck_value >= 70 else "#ffc107" if luck_value >= 30 else "#dc3545"
                luck_item.setForeground(QColor(luck_color))
                luck_item.setFlags(luck_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.game_data_table.setItem(row, 5, luck_item)

                # 金币 - 可编辑
                gold_item = QTableWidgetItem(str(data.get('gold', 0)))
                self.game_data_table.setItem(row, 6, gold_item)

                # 灵石 - 可编辑
                spirit_item = QTableWidgetItem(str(data.get('spirit_stone', 0)))
                self.game_data_table.setItem(row, 7, spirit_item)

                # 更新时间（数据最后变动时间）- 不可编辑
                update_time = data.get('updated_at', data.get('created_at', ''))
                time_item = QTableWidgetItem(update_time)
                time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.game_data_table.setItem(row, 8, time_item)

            except Exception as e:
                print(f"填充游戏数据表格第{row}行时出错: {e}")
                print(f"游戏数据: {data}")
                continue

        # 调整列宽
        self.game_data_table.resizeColumnsToContents()
        header = self.game_data_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 修仙者名列自适应

        # 重置加载标志
        self.loading_data = False

    def on_user_selection_changed(self):
        """用户选择变更处理"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self.edit_user_button.setEnabled(has_selection)
        self.ban_user_button.setEnabled(has_selection)
        self.unban_user_button.setEnabled(has_selection)
        self.delete_user_button.setEnabled(has_selection)

        if has_selection:
            row = selected_rows[0].row()
            user_id = int(self.users_table.item(row, 0).text())
            username = self.users_table.item(row, 1).text()
            is_active = "激活" in self.users_table.item(row, 5).text()  # 激活状态列索引改为5

            self.ban_user_button.setEnabled(is_active)
            self.unban_user_button.setEnabled(not is_active)

            self.status_label.setText(f"已选择用户: {username} (ID: {user_id})")
        else:
            self.status_label.setText("就绪")

    def on_game_data_selection_changed(self):
        """游戏数据选择变更处理"""
        selected_rows = self.game_data_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self.edit_game_data_button.setEnabled(has_selection)
        self.reset_game_data_button.setEnabled(has_selection)

        if has_selection:
            row = selected_rows[0].row()
            user_id = int(self.game_data_table.item(row, 0).text())
            user_name = self.game_data_table.item(row, 1).text()

            self.status_label.setText(f"已选择用户: {user_name} (用户ID: {user_id})")
        else:
            self.status_label.setText("就绪")

    def on_progress_updated(self, value: int):
        """进度更新处理"""
        self.progress_bar.setValue(value)

    def on_operation_completed(self, success: bool, message: str):
        """操作完成处理"""
        if success:
            # 只在状态栏显示成功信息，不弹出对话框
            self.status_label.setText(f"✅ {message}")
            self.refresh_current_tab()
        else:
            # 失败时仍然弹出警告
            QMessageBox.warning(self, "操作失败", message)
            self.status_label.setText("就绪")

    def edit_selected_user(self):
        """编辑选中的用户"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())

        # 查找用户数据
        user_data = None
        for user in self.users_data:
            if user['id'] == user_id:
                user_data = user
                break

        if not user_data:
            QMessageBox.warning(self, "错误", "未找到用户数据")
            return

        # 打开编辑对话框
        dialog = UserEditDialog(user_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if new_data is not None:  # 检查密码验证是否通过
                self.status_label.setText("正在更新用户数据...")
                self.db_worker.update_user(user_id, new_data)

    def ban_selected_user(self):
        """封禁选中的用户"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())
        username = self.users_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "确认封禁",
            f"确定要封禁用户 '{username}' 吗？\n封禁后用户将无法登录游戏。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText("正在封禁用户...")
            self.db_worker.ban_user(user_id, True)

    def unban_selected_user(self):
        """解封选中的用户"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())
        username = self.users_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "确认解封",
            f"确定要解封用户 '{username}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText("正在解封用户...")
            self.db_worker.ban_user(user_id, False)

    def delete_selected_user(self):
        """删除选中的用户"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        user_id = int(self.users_table.item(row, 0).text())
        username = self.users_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "⚠️ 危险操作",
            f"确定要删除用户 '{username}' 吗？\n\n"
            f"⚠️ 警告：此操作将永久删除用户及其所有角色数据，无法恢复！\n"
            f"请输入用户名确认删除：",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 二次确认
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(
                self, "确认删除",
                f"请输入用户名 '{username}' 确认删除："
            )

            if ok and text == username:
                self.status_label.setText("正在删除用户...")
                self.db_worker.delete_user(user_id)
            elif ok:
                QMessageBox.warning(self, "删除取消", "用户名不匹配，删除操作已取消")

    def edit_selected_game_data(self):
        """编辑选中的游戏数据"""
        selected_rows = self.game_data_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        user_id = int(self.game_data_table.item(row, 0).text())

        # 查找游戏数据
        game_data = None
        for data in self.game_data:
            if data['user_id'] == user_id:
                game_data = data
                break

        if not game_data:
            QMessageBox.warning(self, "错误", "未找到游戏数据")
            return

        # 打开编辑对话框
        dialog = UserGameDataEditDialog(game_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self.status_label.setText("正在更新游戏数据...")
            # 使用角色ID进行更新
            character_id = game_data['id']
            self.db_worker.update_user_game_data(character_id, new_data)

    def reset_selected_game_data(self):
        """重置选中的游戏数据"""
        selected_rows = self.game_data_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        user_id = int(self.game_data_table.item(row, 0).text())
        user_name = self.game_data_table.item(row, 1).text()

        # 查找游戏数据以获取角色ID
        game_data = None
        for data in self.game_data:
            if data['user_id'] == user_id:
                game_data = data
                break

        if not game_data:
            QMessageBox.warning(self, "错误", "未找到游戏数据")
            return

        reply = QMessageBox.question(
            self, "确认重置",
            f"确定要重置用户 '{user_name}' 的游戏数据吗？\n\n"
            f"重置操作将：\n"
            f"• 修为重置为 0\n"
            f"• 境界重置为凡人\n"
            f"• 气运重置为 50\n"
            f"• 金币和灵石重置为初始值\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 生成随机气运值而不是固定50
            from shared.utils import generate_daily_luck
            reset_data = {
                'cultivation_exp': 0,
                'cultivation_realm': 0,
                'luck_value': generate_daily_luck(),  # 使用随机气运值
                'gold': 1000,
                'spirit_stone': 0,
                'cultivation_focus': None,
                'last_sign_date': None  # 重置签到日期，允许重新签到
            }
            self.status_label.setText("正在重置游戏数据...")
            # 使用角色ID进行更新
            character_id = game_data['id']
            self.db_worker.update_user_game_data(character_id, reset_data)

    def on_game_data_item_changed(self, item):
        """游戏数据表格项变更处理"""
        if not item or self.loading_data:
            return

        row = item.row()
        col = item.column()

        # 获取用户ID
        user_id_item = self.game_data_table.item(row, 0)
        if not user_id_item:
            return

        try:
            user_id = int(user_id_item.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "无效的用户ID")
            return

        # 查找游戏数据以获取角色ID
        game_data = None
        for data in self.game_data:
            if data['user_id'] == user_id:
                game_data = data
                break

        if not game_data:
            QMessageBox.warning(self, "错误", "未找到游戏数据")
            return

        character_id = game_data['id']

        # 定义可编辑的列和对应的字段名
        editable_columns = {
            1: 'name',           # 修仙者名
            2: 'cultivation_exp', # 修为
            6: 'gold',           # 金币
            7: 'spirit_stone'    # 灵石
        }

        if col not in editable_columns:
            return

        field_name = editable_columns[col]
        new_value = item.text()

        # 数据类型转换
        try:
            if field_name in ['cultivation_exp', 'gold', 'spirit_stone']:
                # 移除逗号分隔符并转换为整数
                new_value = int(new_value.replace(',', ''))
        except ValueError:
            QMessageBox.warning(self, "错误", f"无效的数值: {item.text()}")
            # 恢复原值
            self.load_game_data()
            return

        # 更新数据库
        update_data = {field_name: new_value}
        self.status_label.setText(f"正在更新 {field_name}...")
        self.db_worker.update_user_game_data(character_id, update_data)


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("气运修仙数据库管理工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("气运修仙工作室")

    # 创建并显示主窗口
    main_window = DatabaseAdminMainWindow()
    main_window.show()

    # 不再自动加载游戏数据，让用户手动切换标签页时加载

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
