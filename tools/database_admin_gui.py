# 可视化数据库管理工具

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QTabWidget,
    QMessageBox, QDialog, QFormLayout, QCheckBox, QGroupBox,
    QSplitter, QHeaderView, QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from server.database.models import User, Character, InventoryItem, EquippedItem, GameLog
from server.config import settings
from shared.constants import CULTIVATION_REALMS, LUCK_LEVELS, SPIRITUAL_ROOTS
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
        database_url = settings.DATABASE_URL
        if database_url.startswith("sqlite+aiosqlite"):
            database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
        elif database_url.startswith("postgresql+asyncpg"):
            database_url = database_url.replace("postgresql+asyncpg", "postgresql")
        return database_url
    
    def load_users(self):
        """加载用户数据"""
        self.operation = 'load_users'
        self.start()
    
    def load_characters(self):
        """加载角色数据"""
        self.operation = 'load_characters'
        self.start()
    
    def update_user(self, user_id: int, data: Dict[str, Any]):
        """更新用户数据"""
        self.operation = 'update_user'
        self.params = {'user_id': user_id, 'data': data}
        self.start()
    
    def update_character(self, character_id: int, data: Dict[str, Any]):
        """更新角色数据"""
        self.operation = 'update_character'
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
                        user_info = {
                            'id': user.id,
                            'username': user.username or '',
                            'email': user.email or '',
                            'is_active': user.is_active if user.is_active is not None else True,
                            'is_verified': user.is_verified if user.is_verified is not None else False,
                            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录',
                            'character_count': len(user.characters) if user.characters else 0
                        }
                        user_data.append(user_info)
                    self.data_loaded.emit(user_data)
                
                elif self.operation == 'load_characters':
                    characters = session.query(Character).all()
                    char_data = []
                    for i, char in enumerate(characters):
                        self.progress_updated.emit(int((i + 1) / len(characters) * 100))
                        char_info = {
                            'id': char.id,
                            'user_id': char.user_id,
                            'username': char.user.username if char.user else '未知',
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
                            'last_active': char.last_active.strftime('%Y-%m-%d %H:%M:%S') if char.last_active else '从未活跃',
                            'cultivation_focus': char.cultivation_focus or '无'
                        }
                        char_data.append(char_info)
                    self.data_loaded.emit(char_data)
                
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
                
                elif self.operation == 'update_character':
                    character_id = self.params['character_id']
                    data = self.params['data']
                    char = session.query(Character).filter(Character.id == character_id).first()
                    if char:
                        for key, value in data.items():
                            if hasattr(char, key):
                                setattr(char, key, value)
                        session.commit()
                        self.operation_completed.emit(True, f"角色 {char.name} 更新成功")
                    else:
                        self.operation_completed.emit(False, "角色不存在")
                
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
        return {
            'username': self.username_edit.text(),
            'email': self.email_edit.text(),
            'is_active': self.active_checkbox.isChecked(),
            'is_verified': self.verified_checkbox.isChecked()
        }


class CharacterEditDialog(QDialog):
    """角色编辑对话框"""
    
    def __init__(self, character_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.character_data = character_data
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"编辑角色 - {self.character_data['name']}")
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout()
        
        # 表单
        form_layout = QFormLayout()
        
        # 角色名
        self.name_edit = QLineEdit(self.character_data['name'])
        form_layout.addRow("角色名:", self.name_edit)
        
        # 修为
        self.exp_spinbox = QSpinBox()
        self.exp_spinbox.setRange(0, 999999999)
        self.exp_spinbox.setValue(self.character_data['cultivation_exp'])
        form_layout.addRow("修为:", self.exp_spinbox)
        
        # 境界
        self.realm_combo = QComboBox()
        self.realm_combo.addItems([f"{i} - {realm}" for i, realm in enumerate(CULTIVATION_REALMS)])
        self.realm_combo.setCurrentIndex(self.character_data['cultivation_realm'])
        form_layout.addRow("境界:", self.realm_combo)
        
        # 灵根
        self.root_combo = QComboBox()
        self.root_combo.addItems(list(SPIRITUAL_ROOTS.keys()))
        self.root_combo.setCurrentText(self.character_data['spiritual_root'])
        form_layout.addRow("灵根:", self.root_combo)
        
        # 气运
        self.luck_spinbox = QSpinBox()
        self.luck_spinbox.setRange(0, 100)
        self.luck_spinbox.setValue(self.character_data['luck_value'])
        form_layout.addRow("气运值:", self.luck_spinbox)
        
        # 金币
        self.gold_spinbox = QSpinBox()
        self.gold_spinbox.setRange(0, 999999999)
        self.gold_spinbox.setValue(self.character_data['gold'])
        form_layout.addRow("金币:", self.gold_spinbox)
        
        # 灵石
        self.spirit_spinbox = QSpinBox()
        self.spirit_spinbox.setRange(0, 999999999)
        self.spirit_spinbox.setValue(self.character_data['spirit_stone'])
        form_layout.addRow("灵石:", self.spirit_spinbox)
        
        # 修炼方向
        self.focus_combo = QComboBox()
        focus_options = ["无", "HP", "PHYSICAL_ATTACK", "MAGIC_ATTACK", "PHYSICAL_DEFENSE", "MAGIC_DEFENSE"]
        self.focus_combo.addItems(focus_options)
        current_focus = self.character_data.get('cultivation_focus', '无')
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
        self.characters_data = []

        self.init_ui()

        # 自动加载数据
        QTimer.singleShot(500, self.load_users_data)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("气运修仙 - 数据库管理工具")
        self.setGeometry(100, 100, 1200, 800)

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

        # 角色管理标签页
        self.create_characters_tab()
        self.tab_widget.addTab(self.characters_tab, "🎮 角色管理")

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

    def create_characters_tab(self):
        """创建角色管理标签页"""
        self.characters_tab = QWidget()
        layout = QVBoxLayout()

        # 操作按钮
        button_layout = QHBoxLayout()

        self.edit_character_button = QPushButton("✏️ 编辑角色")
        self.edit_character_button.clicked.connect(self.edit_selected_character)
        self.edit_character_button.setEnabled(False)
        button_layout.addWidget(self.edit_character_button)

        self.reset_character_button = QPushButton("🔄 重置角色")
        self.reset_character_button.clicked.connect(self.reset_selected_character)
        self.reset_character_button.setEnabled(False)
        self.reset_character_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        button_layout.addWidget(self.reset_character_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 角色表格
        self.characters_table = QTableWidget()
        self.characters_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.characters_table.setAlternatingRowColors(True)
        self.characters_table.itemSelectionChanged.connect(self.on_character_selection_changed)
        layout.addWidget(self.characters_table)

        self.characters_tab.setLayout(layout)

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

    def load_characters_data(self):
        """加载角色数据"""
        self.status_label.setText("正在加载角色数据...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.db_worker.load_characters()

    def refresh_current_tab(self):
        """刷新当前标签页数据"""
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:  # 用户管理
            self.load_users_data()
        elif current_index == 1:  # 角色管理
            self.load_characters_data()

    def filter_data(self):
        """过滤数据"""
        keyword = self.search_edit.text().lower()
        current_index = self.tab_widget.currentIndex()

        if current_index == 0:  # 用户管理
            self.filter_users_table(keyword)
        elif current_index == 1:  # 角色管理
            self.filter_characters_table(keyword)

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

    def filter_characters_table(self, keyword: str):
        """过滤角色表格"""
        for row in range(self.characters_table.rowCount()):
            show_row = False
            for col in range(self.characters_table.columnCount()):
                item = self.characters_table.item(row, col)
                if item and keyword in item.text().lower():
                    show_row = True
                    break
            self.characters_table.setRowHidden(row, not show_row)

    def on_data_loaded(self, data: List[Dict[str, Any]]):
        """数据加载完成处理"""
        current_index = self.tab_widget.currentIndex()

        if current_index == 0:  # 用户数据
            self.users_data = data
            self.populate_users_table(data)
            self.status_label.setText(f"用户数据加载完成，共 {len(data)} 条记录")
        elif current_index == 1:  # 角色数据
            self.characters_data = data
            self.populate_characters_table(data)
            self.status_label.setText(f"角色数据加载完成，共 {len(data)} 条记录")

        self.progress_bar.setVisible(False)

    def populate_users_table(self, users_data: List[Dict[str, Any]]):
        """填充用户表格"""
        if not users_data:
            return

        # 设置表格
        headers = ['ID', '用户名', '邮箱', '激活状态', '验证状态', '创建时间', '最后登录', '角色数量']
        self.users_table.setColumnCount(len(headers))
        self.users_table.setHorizontalHeaderLabels(headers)
        self.users_table.setRowCount(len(users_data))

        # 填充数据
        for row, user in enumerate(users_data):
            try:
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))

                # 激活状态
                is_active = user.get('is_active', True)
                active_item = QTableWidgetItem("✅ 激活" if is_active else "❌ 封禁")
                active_item.setForeground(QColor("#28a745") if is_active else QColor("#dc3545"))
                self.users_table.setItem(row, 3, active_item)

                # 验证状态
                is_verified = user.get('is_verified', False)
                verified_item = QTableWidgetItem("✅ 已验证" if is_verified else "❌ 未验证")
                verified_item.setForeground(QColor("#28a745") if is_verified else QColor("#ffc107"))
                self.users_table.setItem(row, 4, verified_item)

                self.users_table.setItem(row, 5, QTableWidgetItem(user.get('created_at', '')))
                self.users_table.setItem(row, 6, QTableWidgetItem(user.get('last_login', '')))
                self.users_table.setItem(row, 7, QTableWidgetItem(str(user.get('character_count', 0))))

            except Exception as e:
                print(f"填充用户表格第{row}行时出错: {e}")
                print(f"用户数据: {user}")
                continue

        # 调整列宽
        self.users_table.resizeColumnsToContents()
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 用户名列自适应
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 邮箱列自适应

    def populate_characters_table(self, characters_data: List[Dict[str, Any]]):
        """填充角色表格"""
        if not characters_data:
            return

        # 设置表格
        headers = ['ID', '用户ID', '用户名', '角色名', '修为', '境界', '灵根', '气运', '金币', '灵石', '修炼方向', '创建时间']
        self.characters_table.setColumnCount(len(headers))
        self.characters_table.setHorizontalHeaderLabels(headers)
        self.characters_table.setRowCount(len(characters_data))

        # 填充数据
        for row, char in enumerate(characters_data):
            try:
                self.characters_table.setItem(row, 0, QTableWidgetItem(str(char.get('id', ''))))
                self.characters_table.setItem(row, 1, QTableWidgetItem(str(char.get('user_id', ''))))
                self.characters_table.setItem(row, 2, QTableWidgetItem(char.get('username', '')))
                self.characters_table.setItem(row, 3, QTableWidgetItem(char.get('name', '')))
                self.characters_table.setItem(row, 4, QTableWidgetItem(f"{char.get('cultivation_exp', 0):,}"))

                # 境界
                realm_item = QTableWidgetItem(char.get('realm_name', ''))
                realm_item.setForeground(QColor("#007acc"))
                self.characters_table.setItem(row, 5, realm_item)

                self.characters_table.setItem(row, 6, QTableWidgetItem(char.get('spiritual_root', '')))

                # 气运
                luck_value = char.get('luck_value', 50)
                luck_level = char.get('luck_level', '平')
                luck_item = QTableWidgetItem(f"{luck_level} ({luck_value})")
                luck_color = "#28a745" if luck_value >= 70 else "#ffc107" if luck_value >= 30 else "#dc3545"
                luck_item.setForeground(QColor(luck_color))
                self.characters_table.setItem(row, 7, luck_item)

                self.characters_table.setItem(row, 8, QTableWidgetItem(f"{char.get('gold', 0):,}"))
                self.characters_table.setItem(row, 9, QTableWidgetItem(f"{char.get('spirit_stone', 0):,}"))
                self.characters_table.setItem(row, 10, QTableWidgetItem(char.get('cultivation_focus', '')))
                self.characters_table.setItem(row, 11, QTableWidgetItem(char.get('created_at', '')))

            except Exception as e:
                print(f"填充角色表格第{row}行时出错: {e}")
                print(f"角色数据: {char}")
                continue

        # 调整列宽
        self.characters_table.resizeColumnsToContents()
        header = self.characters_table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # 角色名列自适应

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
            is_active = "激活" in self.users_table.item(row, 3).text()

            self.ban_user_button.setEnabled(is_active)
            self.unban_user_button.setEnabled(not is_active)

            self.status_label.setText(f"已选择用户: {username} (ID: {user_id})")
        else:
            self.status_label.setText("就绪")

    def on_character_selection_changed(self):
        """角色选择变更处理"""
        selected_rows = self.characters_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self.edit_character_button.setEnabled(has_selection)
        self.reset_character_button.setEnabled(has_selection)

        if has_selection:
            row = selected_rows[0].row()
            char_id = int(self.characters_table.item(row, 0).text())
            char_name = self.characters_table.item(row, 3).text()

            self.status_label.setText(f"已选择角色: {char_name} (ID: {char_id})")
        else:
            self.status_label.setText("就绪")

    def on_progress_updated(self, value: int):
        """进度更新处理"""
        self.progress_bar.setValue(value)

    def on_operation_completed(self, success: bool, message: str):
        """操作完成处理"""
        if success:
            QMessageBox.information(self, "操作成功", message)
            self.refresh_current_tab()
        else:
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

    def edit_selected_character(self):
        """编辑选中的角色"""
        selected_rows = self.characters_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        char_id = int(self.characters_table.item(row, 0).text())

        # 查找角色数据
        char_data = None
        for char in self.characters_data:
            if char['id'] == char_id:
                char_data = char
                break

        if not char_data:
            QMessageBox.warning(self, "错误", "未找到角色数据")
            return

        # 打开编辑对话框
        dialog = CharacterEditDialog(char_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self.status_label.setText("正在更新角色数据...")
            self.db_worker.update_character(char_id, new_data)

    def reset_selected_character(self):
        """重置选中的角色"""
        selected_rows = self.characters_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        char_id = int(self.characters_table.item(row, 0).text())
        char_name = self.characters_table.item(row, 3).text()

        reply = QMessageBox.question(
            self, "确认重置",
            f"确定要重置角色 '{char_name}' 吗？\n\n"
            f"重置操作将：\n"
            f"• 修为重置为 0\n"
            f"• 境界重置为凡人\n"
            f"• 气运重置为 50\n"
            f"• 金币和灵石重置为初始值\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            reset_data = {
                'cultivation_exp': 0,
                'cultivation_realm': 0,
                'luck_value': 50,
                'gold': 1000,
                'spirit_stone': 0,
                'cultivation_focus': None
            }
            self.status_label.setText("正在重置角色...")
            self.db_worker.update_character(char_id, reset_data)


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

    # 自动加载角色数据
    QTimer.singleShot(2000, main_window.load_characters_data)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
