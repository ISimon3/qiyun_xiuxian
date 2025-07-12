# 炼丹界面

import sys
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QProgressBar, QGroupBox,
    QScrollArea, QFrame, QMessageBox, QSplitter
)
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from client.network.api_client import GameAPIClient
from client.state_manager import StateManager
from shared.constants import ITEM_QUALITY


class AlchemyWindow(QWidget):
    """炼丹界面"""
    
    # 信号
    alchemy_started = pyqtSignal(str)  # 开始炼丹
    alchemy_collected = pyqtSignal(int)  # 收取结果
    
    def __init__(self, api_client: GameAPIClient, state_manager: StateManager):
        super().__init__()
        self.api_client = api_client
        self.state_manager = state_manager
        
        # 数据
        self.alchemy_info = {}
        self.selected_recipe = None
        
        # 定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(1000)  # 每秒更新一次
        
        self.init_ui()
        self.load_alchemy_info()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("炼丹房")
        self.setFixedSize(900, 700)
        
        # 主布局
        main_layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：丹方列表
        left_widget = self.create_recipe_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：炼制状态
        right_widget = self.create_alchemy_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([400, 500])
        
    def create_recipe_panel(self) -> QWidget:
        """创建丹方面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title_label = QLabel("📜 可用丹方")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 丹方列表
        self.recipe_list = QListWidget()
        self.recipe_list.itemClicked.connect(self.on_recipe_selected)
        layout.addWidget(self.recipe_list)
        
        # 丹方详情
        self.recipe_detail = QTextEdit()
        self.recipe_detail.setMaximumHeight(150)
        self.recipe_detail.setReadOnly(True)
        layout.addWidget(self.recipe_detail)
        
        # 开始炼制按钮
        self.start_button = QPushButton("🔥 开始炼制")
        self.start_button.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_alchemy)
        self.start_button.setEnabled(False)
        layout.addWidget(self.start_button)
        
        return widget
        
    def create_alchemy_panel(self) -> QWidget:
        """创建炼制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 炼丹等级信息
        self.level_info = QLabel("炼丹等级: 1 (经验: 0)")
        self.level_info.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.level_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.level_info)
        
        # 活跃会话
        sessions_group = QGroupBox("🔥 炼制中")
        sessions_layout = QVBoxLayout(sessions_group)
        
        # 会话列表容器
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.sessions_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        sessions_layout.addWidget(scroll_area)
        
        layout.addWidget(sessions_group)
        
        # 材料库存
        materials_group = QGroupBox("📦 材料库存")
        materials_layout = QVBoxLayout(materials_group)
        
        self.materials_list = QListWidget()
        self.materials_list.setMaximumHeight(200)
        materials_layout.addWidget(self.materials_list)
        
        layout.addWidget(materials_group)
        
        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.load_alchemy_info)
        layout.addWidget(refresh_button)
        
        return widget
        
    def load_alchemy_info(self):
        """加载炼丹信息"""
        try:
            response = self.api_client.game.get_alchemy_info()
            if response.get('success'):
                self.alchemy_info = response.get('data', {})
                self.update_ui()
            else:
                QMessageBox.warning(self, "错误", response.get('message', '获取炼丹信息失败'))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取炼丹信息失败: {str(e)}")
            
    def update_ui(self):
        """更新界面"""
        if not self.alchemy_info:
            return
            
        # 更新炼丹等级信息
        level = self.alchemy_info.get('alchemy_level', 1)
        exp = self.alchemy_info.get('alchemy_exp', 0)
        self.level_info.setText(f"炼丹等级: {level} (经验: {exp})")
        
        # 更新丹方列表
        self.update_recipe_list()
        
        # 更新活跃会话
        self.update_active_sessions()
        
        # 更新材料库存
        self.update_materials_list()
        
    def update_recipe_list(self):
        """更新丹方列表"""
        self.recipe_list.clear()
        
        recipes = self.alchemy_info.get('available_recipes', [])
        for recipe in recipes:
            item = QListWidgetItem()
            
            # 设置文本
            name = recipe.get('name', '')
            quality = recipe.get('quality', 'COMMON')
            can_craft = recipe.get('can_craft', False)
            
            # 品质颜色
            quality_info = ITEM_QUALITY.get(quality, {"name": "普通", "color": "#333333"})
            color = quality_info["color"]
            
            # 状态标识
            status_icon = "✅" if can_craft else "❌"
            
            item.setText(f"{status_icon} {name} ({quality_info['name']})")
            
            # 设置颜色
            if can_craft:
                item.setForeground(QColor(color))
            else:
                item.setForeground(QColor("#888888"))
                
            # 存储数据
            item.setData(Qt.ItemDataRole.UserRole, recipe)
            
            self.recipe_list.addItem(item)
            
    def update_active_sessions(self):
        """更新活跃会话"""
        # 清空现有会话
        for i in reversed(range(self.sessions_layout.count())):
            child = self.sessions_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        sessions = self.alchemy_info.get('active_sessions', [])
        
        if not sessions:
            no_session_label = QLabel("暂无炼制中的丹药")
            no_session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_session_label.setStyleSheet("color: #888888; font-style: italic;")
            self.sessions_layout.addWidget(no_session_label)
        else:
            for session in sessions:
                session_widget = self.create_session_widget(session)
                self.sessions_layout.addWidget(session_widget)
                
    def create_session_widget(self, session: Dict[str, Any]) -> QWidget:
        """创建会话组件"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("QFrame { border: 1px solid #cccccc; border-radius: 5px; padding: 5px; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 丹药名称
        name_label = QLabel(session.get('recipe_name', '未知丹药'))
        name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # 进度条
        progress_bar = QProgressBar()
        progress = session.get('progress', 0.0)
        progress_bar.setValue(int(progress * 100))
        layout.addWidget(progress_bar)
        
        # 时间信息
        remaining_time = session.get('remaining_time_seconds', 0)
        if remaining_time > 0:
            hours = remaining_time // 3600
            minutes = (remaining_time % 3600) // 60
            seconds = remaining_time % 60
            time_text = f"剩余时间: {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_text = "已完成"
            
        time_label = QLabel(time_text)
        layout.addWidget(time_label)
        
        # 收取按钮
        if remaining_time <= 0:
            collect_button = QPushButton("📦 收取")
            collect_button.clicked.connect(lambda: self.collect_alchemy_result(session.get('id')))
            layout.addWidget(collect_button)
            
        return widget
        
    def update_materials_list(self):
        """更新材料列表"""
        self.materials_list.clear()
        
        materials = self.alchemy_info.get('materials_inventory', {})
        if not materials:
            item = QListWidgetItem("暂无材料")
            item.setForeground(QColor("#888888"))
            self.materials_list.addItem(item)
        else:
            for material_name, quantity in materials.items():
                item = QListWidgetItem(f"{material_name}: {quantity}")
                self.materials_list.addItem(item)
                
    def on_recipe_selected(self, item: QListWidgetItem):
        """选择丹方"""
        recipe = item.data(Qt.ItemDataRole.UserRole)
        if recipe:
            self.selected_recipe = recipe
            self.show_recipe_detail(recipe)
            self.start_button.setEnabled(recipe.get('can_craft', False))
            
    def show_recipe_detail(self, recipe: Dict[str, Any]):
        """显示丹方详情"""
        detail_text = f"""
<h3>{recipe.get('name', '')}</h3>
<p><b>描述:</b> {recipe.get('description', '')}</p>
<p><b>品质:</b> {ITEM_QUALITY.get(recipe.get('quality', 'COMMON'), {}).get('name', '普通')}</p>
<p><b>需要境界:</b> {recipe.get('required_realm', 0)}</p>
<p><b>炼制时间:</b> {recipe.get('base_time_minutes', 0)}分钟</p>
<p><b>成功率:</b> {recipe.get('base_success_rate', 0.7) * 100:.1f}%</p>

<h4>所需材料:</h4>
<ul>
"""
        
        materials = recipe.get('materials', {})
        for material_name, quantity in materials.items():
            detail_text += f"<li>{material_name}: {quantity}</li>"
            
        detail_text += "</ul>"
        
        # 显示缺少的材料
        missing_materials = recipe.get('missing_materials')
        if missing_materials:
            detail_text += "<h4 style='color: red;'>缺少材料:</h4><ul>"
            for material_name, quantity in missing_materials.items():
                detail_text += f"<li style='color: red;'>{material_name}: {quantity}</li>"
            detail_text += "</ul>"
            
        self.recipe_detail.setHtml(detail_text)
        
    def start_alchemy(self):
        """开始炼丹"""
        if not self.selected_recipe:
            QMessageBox.warning(self, "提示", "请先选择丹方")
            return
            
        recipe_id = self.selected_recipe.get('id')
        if not recipe_id:
            QMessageBox.warning(self, "错误", "丹方ID无效")
            return
            
        try:
            response = self.api_client.game.start_alchemy(recipe_id)
            if response.get('success'):
                QMessageBox.information(self, "成功", response.get('message', '开始炼制'))
                self.load_alchemy_info()  # 刷新信息
                self.alchemy_started.emit(recipe_id)
            else:
                QMessageBox.warning(self, "失败", response.get('message', '开始炼制失败'))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"开始炼制失败: {str(e)}")
            
    def collect_alchemy_result(self, session_id: int):
        """收取炼丹结果"""
        try:
            response = self.api_client.game.collect_alchemy_result(session_id)
            if response.get('success'):
                QMessageBox.information(self, "成功", response.get('message', '收取成功'))
                self.load_alchemy_info()  # 刷新信息
                self.alchemy_collected.emit(session_id)
            else:
                QMessageBox.warning(self, "失败", response.get('message', '收取失败'))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"收取失败: {str(e)}")
            
    def update_progress(self):
        """更新进度"""
        # 重新加载活跃会话以更新进度
        if self.alchemy_info.get('active_sessions'):
            self.load_alchemy_info()
            
    def closeEvent(self, event):
        """关闭事件"""
        self.update_timer.stop()
        event.accept()
