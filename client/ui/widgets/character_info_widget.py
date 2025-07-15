# 顶部角色信息面板

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette

from shared.constants import CULTIVATION_REALMS, LUCK_LEVELS, CULTIVATION_FOCUS_TYPES
from shared.utils import get_realm_name, get_luck_level_name


class CharacterInfoWidget(QWidget):
    """用户信息面板组件"""

    # 信号定义
    daily_sign_requested = pyqtSignal()  # 每日签到请求信号
    cultivation_focus_changed = pyqtSignal(str)  # 修炼方向变更信号

    def __init__(self):
        super().__init__()

        # 数据缓存
        self.character_data: Optional[Dict[str, Any]] = None
        self.cultivation_status: Optional[Dict[str, Any]] = None
        self.luck_info: Optional[Dict[str, Any]] = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 角色基本信息区域
        self.create_basic_info_section(main_layout)

        # 修炼状态区域
        self.create_cultivation_section(main_layout)

        # 资源和气运区域
        self.create_resources_section(main_layout)

        self.setLayout(main_layout)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
            .title-label {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
            }
            .value-label {
                font-weight: bold;
                color: #27ae60;
            }
            .progress-label {
                font-size: 11px;
                color: #666;
            }
        """)

    def create_basic_info_section(self, parent_layout: QVBoxLayout):
        """创建基本信息区域"""
        # 修仙者名称和境界
        info_layout = QHBoxLayout()

        # 修仙者名称
        self.name_label = QLabel("修仙者名称")
        self.name_label.setProperty("class", "title-label")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.name_label.setFont(font)
        info_layout.addWidget(self.name_label)

        info_layout.addStretch()

        # 境界
        self.realm_label = QLabel("凡人")
        self.realm_label.setProperty("class", "value-label")
        realm_font = QFont()
        realm_font.setPointSize(12)
        realm_font.setBold(True)
        self.realm_label.setFont(realm_font)
        info_layout.addWidget(self.realm_label)

        parent_layout.addLayout(info_layout)

        # 修为进度条
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(2)

        self.exp_progress_bar = QProgressBar()
        self.exp_progress_bar.setMinimumHeight(20)
        self.exp_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 10px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 9px;
            }
        """)
        progress_layout.addWidget(self.exp_progress_bar)

        self.exp_progress_label = QLabel("修为: 0 / 100 (0.0%)")
        self.exp_progress_label.setProperty("class", "progress-label")
        self.exp_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.exp_progress_label)

        parent_layout.addLayout(progress_layout)

    def create_cultivation_section(self, parent_layout: QVBoxLayout):
        """创建修炼状态区域"""
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        parent_layout.addWidget(line)

        # 修炼状态
        cultivation_layout = QHBoxLayout()

        # 修炼方向选择
        focus_layout = QVBoxLayout()
        focus_layout.setSpacing(2)

        focus_title = QLabel("修炼方向:")
        focus_title.setProperty("class", "title-label")
        focus_layout.addWidget(focus_title)

        # 修炼方向下拉框
        self.cultivation_focus_combo = QComboBox()
        self.cultivation_focus_combo.setMinimumHeight(25)

        # 添加修炼方向选项
        focus_options = []
        for focus_key, focus_info in CULTIVATION_FOCUS_TYPES.items():
            name = focus_info['name']
            icon = focus_info['icon']
            focus_options.append((f"{icon} {name}", focus_key))

        for display_name, focus_key in focus_options:
            self.cultivation_focus_combo.addItem(display_name, focus_key)

        self.cultivation_focus_combo.currentTextChanged.connect(self.on_focus_changed)
        self.cultivation_focus_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 11px;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        focus_layout.addWidget(self.cultivation_focus_combo)

        cultivation_layout.addLayout(focus_layout)

        cultivation_layout.addStretch()

        # 修炼状态
        status_layout = QVBoxLayout()
        status_layout.setSpacing(2)

        status_title = QLabel("修炼状态:")
        status_title.setProperty("class", "title-label")
        status_layout.addWidget(status_title)

        self.cultivation_status_label = QLabel("挂机中...")
        self.cultivation_status_label.setProperty("class", "value-label")
        status_layout.addWidget(self.cultivation_status_label)

        cultivation_layout.addLayout(status_layout)

        parent_layout.addLayout(cultivation_layout)

    def create_resources_section(self, parent_layout: QVBoxLayout):
        """创建资源和气运区域"""
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        parent_layout.addWidget(line)

        # 资源信息网格
        resources_layout = QGridLayout()
        resources_layout.setSpacing(5)

        # 金币
        gold_title = QLabel("金币:")
        self.gold_label = QLabel("0")
        self.gold_label.setProperty("class", "value-label")
        resources_layout.addWidget(gold_title, 0, 0)
        resources_layout.addWidget(self.gold_label, 0, 1)

        # 灵石
        spirit_title = QLabel("灵石:")
        self.spirit_stone_label = QLabel("0")
        self.spirit_stone_label.setProperty("class", "value-label")
        resources_layout.addWidget(spirit_title, 0, 2)
        resources_layout.addWidget(self.spirit_stone_label, 0, 3)

        # 气运
        luck_title = QLabel("气运:")
        self.luck_label = QLabel("平 (50)")
        self.luck_label.setProperty("class", "value-label")
        resources_layout.addWidget(luck_title, 1, 0)
        resources_layout.addWidget(self.luck_label, 1, 1)

        # 每日签到按钮
        self.daily_sign_button = QPushButton("每日签到")
        self.daily_sign_button.setMinimumHeight(25)
        self.daily_sign_button.clicked.connect(self.daily_sign_requested.emit)
        self.daily_sign_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        resources_layout.addWidget(self.daily_sign_button, 1, 2, 1, 2)

        parent_layout.addLayout(resources_layout)

    def update_character_info(self, character_data: Dict[str, Any]):
        """更新用户信息"""
        self.character_data = character_data

        # 更新修仙者名称
        name = character_data.get('name', '未知修仙者')
        self.name_label.setText(name)

        # 更新境界
        realm_level = character_data.get('cultivation_realm', 0)
        realm_name = get_realm_name(realm_level)
        self.realm_label.setText(realm_name)

        # 更新修为进度
        current_exp = character_data.get('cultivation_exp', 0)
        self.update_cultivation_progress(current_exp, realm_level)

        # 更新资源
        gold = character_data.get('gold', 0)
        spirit_stone = character_data.get('spirit_stone', 0)
        self.gold_label.setText(f"{gold:,}")
        self.spirit_stone_label.setText(f"{spirit_stone:,}")

        # 更新气运
        luck_value = character_data.get('luck_value', 50)
        self.update_luck_display(luck_value)

        # 更新修炼方向
        cultivation_focus = character_data.get('cultivation_focus', 'HP')
        self.update_cultivation_focus(cultivation_focus)

    def update_cultivation_status(self, cultivation_data: Dict[str, Any]):
        """更新修炼状态"""
        self.cultivation_status = cultivation_data

        # 更新修炼状态显示
        is_cultivating = cultivation_data.get('is_cultivating', False)
        if is_cultivating:
            self.cultivation_status_label.setText("挂机中...")
            self.cultivation_status_label.setStyleSheet("color: #27ae60;")
        else:
            self.cultivation_status_label.setText("未修炼")
            self.cultivation_status_label.setStyleSheet("color: #e74c3c;")

        # 更新修为进度（如果有更新的数据）
        current_exp = cultivation_data.get('current_exp')
        current_realm = cultivation_data.get('current_realm')
        if current_exp is not None and current_realm is not None:
            self.update_cultivation_progress(current_exp, current_realm)

    def update_luck_info(self, luck_data: Dict[str, Any]):
        """更新气运信息"""
        self.luck_info = luck_data

        # 更新气运显示
        current_luck = luck_data.get('current_luck', 50)
        self.update_luck_display(current_luck)

        # 更新每日签到按钮状态
        can_sign_today = luck_data.get('can_sign_today', True)
        self.daily_sign_button.setEnabled(can_sign_today)
        if not can_sign_today:
            self.daily_sign_button.setText("已签到")
        else:
            self.daily_sign_button.setText("每日签到")

    def update_cultivation_progress(self, current_exp: int, realm_level: int):
        """更新修为进度条"""
        from shared.constants import CULTIVATION_EXP_REQUIREMENTS

        # 获取当前境界和下一境界的修为需求
        current_realm_exp = CULTIVATION_EXP_REQUIREMENTS.get(realm_level, 0)
        next_realm_exp = CULTIVATION_EXP_REQUIREMENTS.get(realm_level + 1, current_realm_exp + 1000)

        # 计算当前境界内的进度
        if next_realm_exp > current_realm_exp:
            progress_exp = current_exp - current_realm_exp
            required_exp = next_realm_exp - current_realm_exp
            progress_percent = (progress_exp / required_exp) * 100 if required_exp > 0 else 0
        else:
            progress_exp = 0
            required_exp = 1
            progress_percent = 100

        # 更新进度条
        self.exp_progress_bar.setValue(int(progress_percent))

        # 更新进度标签
        self.exp_progress_label.setText(
            f"修为: {progress_exp:,} / {required_exp:,} ({progress_percent:.1f}%)"
        )

    def update_luck_display(self, luck_value: int):
        """更新气运显示"""
        luck_level_name = get_luck_level_name(luck_value)

        # 获取气运等级颜色
        luck_color = "#808080"  # 默认颜色
        for level_name, level_info in LUCK_LEVELS.items():
            if level_name == luck_level_name:
                luck_color = level_info.get("color", "#808080")
                break

        # 更新气运标签（不显示具体数值）
        self.luck_label.setText(f"{luck_level_name}")
        self.luck_label.setStyleSheet(f"color: {luck_color}; font-weight: bold;")

    def update_cultivation_focus(self, focus_type: str):
        """更新修炼方向显示"""
        # 在下拉框中选择对应的修炼方向
        for i in range(self.cultivation_focus_combo.count()):
            if self.cultivation_focus_combo.itemData(i) == focus_type:
                self.cultivation_focus_combo.setCurrentIndex(i)
                break

    def on_focus_changed(self):
        """修炼方向变更处理"""
        current_focus = self.cultivation_focus_combo.currentData()
        if current_focus:
            self.cultivation_focus_changed.emit(current_focus)

    def get_character_summary(self) -> Dict[str, Any]:
        """获取用户信息摘要"""
        if not self.character_data:
            return {}

        return {
            'name': self.character_data.get('name', ''),
            'realm': get_realm_name(self.character_data.get('cultivation_realm', 0)),
            'cultivation_exp': self.character_data.get('cultivation_exp', 0),
            'luck_value': self.character_data.get('luck_value', 50),
            'gold': self.character_data.get('gold', 0),
            'spirit_stone': self.character_data.get('spirit_stone', 0),
            'cultivation_focus': self.character_data.get('cultivation_focus', 'HP')
        }
