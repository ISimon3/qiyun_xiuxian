# 修炼日志组件

from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor

from shared.constants import CULTIVATION_FOCUS_TYPES
from shared.utils import get_realm_name, get_luck_level_name


class CultivationLogWidget(QWidget):
    """修炼日志组件"""

    # 信号定义
    clear_log_requested = pyqtSignal()  # 清空日志请求信号

    def __init__(self):
        super().__init__()

        # 日志数据
        self.log_entries: List[Dict[str, Any]] = []
        self.max_log_entries = 1000  # 最大日志条数

        # 修炼状态
        self.cultivation_status: Optional[Dict[str, Any]] = None
        self.last_exp = 0
        self.last_realm = 0

        self.init_ui()

        # 移除模拟修炼日志更新，改为真实数据驱动
        # self.update_timer = QTimer()
        # self.update_timer.timeout.connect(self.simulate_cultivation_log)
        # self.update_timer.start(60000)  # 每分钟更新一次

    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 标题栏
        self.create_title_bar(main_layout)

        # 日志显示区域
        self.create_log_area(main_layout)

        self.setLayout(main_layout)

        # 添加初始欢迎消息
        self.add_system_log("欢迎来到气运修仙世界！", "system")
        self.add_system_log("开始您的修仙之路吧！", "system")

    def create_title_bar(self, parent_layout: QVBoxLayout):
        """创建标题栏"""
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        # 标题
        title_label = QLabel("修炼日志")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # 清空日志按钮
        self.clear_button = QPushButton("清空日志")
        self.clear_button.setMaximumWidth(80)
        self.clear_button.setMinimumHeight(25)
        self.clear_button.clicked.connect(self.clear_log)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        title_layout.addWidget(self.clear_button)

        parent_layout.addLayout(title_layout)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        parent_layout.addWidget(line)

    def create_log_area(self, parent_layout: QVBoxLayout):
        """创建日志显示区域"""
        # 日志文本框
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(400)

        # 设置字体
        log_font = QFont("Consolas", 10)
        if not log_font.exactMatch():
            log_font = QFont("Courier New", 10)
        self.log_text_edit.setFont(log_font)

        # 设置样式
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 10px;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                background-color: #34495e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #7f8c8d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)

        parent_layout.addWidget(self.log_text_edit)

    def add_log_entry(self, message: str, log_type: str = "info", color: str = "#ecf0f1"):
        """添加日志条目"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 创建日志条目
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': log_type,
            'color': color
        }

        # 添加到日志列表
        self.log_entries.append(log_entry)

        # 限制日志条数
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries = self.log_entries[-self.max_log_entries:]

        # 更新显示
        self.update_log_display()

    def add_cultivation_log(self, exp_gained: int, attribute_gained: int,
                          attribute_type: str, luck_effect: str):
        """添加修炼日志"""
        focus_info = CULTIVATION_FOCUS_TYPES.get(attribute_type, {})
        focus_name = focus_info.get('name', '未知')
        focus_icon = focus_info.get('icon', '❓')

        message = f"修炼{focus_name}{focus_icon} 获得修为+{exp_gained}, {focus_name}+{attribute_gained} [{luck_effect}]"
        self.add_log_entry(message, "cultivation", "#3498db")

    def add_breakthrough_log(self, old_realm: int, new_realm: int, success: bool):
        """添加突破日志"""
        old_realm_name = get_realm_name(old_realm)
        new_realm_name = get_realm_name(new_realm)

        if success:
            message = f"🎉 突破成功！从 {old_realm_name} 突破至 {new_realm_name}！"
            self.add_log_entry(message, "breakthrough", "#f39c12")
        else:
            message = f"💥 突破失败！仍为 {old_realm_name}，继续努力修炼吧！"
            self.add_log_entry(message, "breakthrough", "#e74c3c")

    def add_luck_log(self, old_luck: int, new_luck: int, reason: str):
        """添加气运变化日志"""
        old_level = get_luck_level_name(old_luck)
        new_level = get_luck_level_name(new_luck)
        change = new_luck - old_luck

        if change > 0:
            message = f"🍀 {reason} 气运提升！{old_level}({old_luck}) → {new_level}({new_luck}) [+{change}]"
            color = "#27ae60"
        elif change < 0:
            message = f"💀 {reason} 气运下降！{old_level}({old_luck}) → {new_level}({new_luck}) [{change}]"
            color = "#e74c3c"
        else:
            message = f"⚖️ {reason} 气运无变化 {new_level}({new_luck})"
            color = "#95a5a6"

        self.add_log_entry(message, "luck", color)

    def add_system_log(self, message: str, log_type: str = "system"):
        """添加系统日志"""
        self.add_log_entry(f"[系统] {message}", log_type, "#9b59b6")

    def add_special_event_log(self, event_message: str):
        """添加特殊事件日志"""
        self.add_log_entry(f"✨ 特殊事件：{event_message}", "special", "#e67e22")

    def update_log_display(self):
        """更新日志显示"""
        # 清空当前显示
        self.log_text_edit.clear()

        # 重新添加所有日志
        for entry in self.log_entries:
            timestamp = entry['timestamp']
            message = entry['message']
            color = entry['color']

            # 添加带颜色的文本
            self.log_text_edit.setTextColor(QColor(color))
            self.log_text_edit.append(f"[{timestamp}] {message}")

        # 滚动到底部
        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text_edit.setTextCursor(cursor)

    def clear_log(self):
        """清空日志"""
        self.log_entries.clear()
        self.log_text_edit.clear()
        self.add_system_log("日志已清空")
        self.clear_log_requested.emit()

    def update_cultivation_status(self, cultivation_data: Dict[str, Any]):
        """更新修炼状态"""
        self.cultivation_status = cultivation_data

        # 检查修为变化
        current_exp = cultivation_data.get('current_exp', 0)
        current_realm = cultivation_data.get('current_realm', 0)

        # 如果修为增加，添加修炼日志
        if current_exp > self.last_exp and self.last_exp > 0:
            exp_gained = current_exp - self.last_exp
            # 这里可以根据实际情况添加更详细的修炼日志
            # 暂时使用模拟数据
            self.add_cultivation_log(exp_gained, 1, "HP", "气运平")

        # 检查境界突破
        if current_realm > self.last_realm and self.last_realm > 0:
            self.add_breakthrough_log(self.last_realm, current_realm, True)

        # 更新记录
        self.last_exp = current_exp
        self.last_realm = current_realm

    def simulate_cultivation_log(self):
        """模拟修炼日志（用于测试）"""
        if self.cultivation_status and self.cultivation_status.get('is_cultivating', False):
            # 模拟修炼获得
            import random
            exp_gained = random.randint(8, 15)
            attr_gained = random.randint(1, 3)

            focus = self.cultivation_status.get('cultivation_focus', 'HP')
            luck_effects = ["气运平", "小吉", "吉", "小凶"]
            luck_effect = random.choice(luck_effects)

            self.add_cultivation_log(exp_gained, attr_gained, focus, luck_effect)

            # 偶尔添加特殊事件
            if random.random() < 0.1:  # 10%概率
                events = [
                    "修炼时感悟天地灵气，修为增长加快",
                    "遇到灵气漩涡，吸收了大量灵气",
                    "修炼时心境平和，获得额外收获",
                    "感受到天地法则的波动，略有所得"
                ]
                self.add_special_event_log(random.choice(events))
