# 背包窗口

import os
import base64
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QMessageBox, QMenu, QComboBox,
    QToolTip, QApplication, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QFont, QCursor, QAction, QIcon

# 检查WebEngine是否可用
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("⚠️ WebEngine不可用，背包界面将使用传统PyQt组件")

from client.network.api_client import GameAPIClient
from shared.constants import ITEM_QUALITY, EQUIPMENT_SLOTS, ITEM_TYPES


class BackpackJSBridge(QWidget):
    """背包界面JavaScript桥接类"""

    # 定义信号
    resize_window_signal = pyqtSignal(int, int)

    def __init__(self, backpack_window):
        super().__init__()
        self.backpack_window = backpack_window

    def resizeWindow(self, width: int, height: int):
        """调整窗口大小（JavaScript调用的方法）"""
        try:
            self.backpack_window.resize_window_from_js(width, height)
        except Exception as e:
            print(f"❌ 桥接调用窗口大小调整失败: {e}")

    def on_equipment_click(self, slot: str):
        """装备点击事件"""
        if slot in self.backpack_window.equipment_items:
            equipment_data = self.backpack_window.equipment_items[slot]
            self.backpack_window.on_equipment_clicked(equipment_data, slot)

    def on_item_click(self, index: int):
        """物品点击事件"""
        start_index = self.backpack_window.current_page * self.backpack_window.items_per_page
        actual_index = start_index + index
        if actual_index < len(self.backpack_window.inventory_items):
            item_data = self.backpack_window.inventory_items[actual_index]
            self.backpack_window.on_item_clicked(item_data)


class CharacterAttributesWidget(QFrame):
    """角色属性显示组件"""

    def __init__(self, api_client=None):
        super().__init__()
        self.character_data = None
        self.api_client = api_client
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFixedSize(220, 220)  # 增加高度以容纳灵根信息

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 标题
        title = QLabel("道友属性")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; font-weight: bold;")
        layout.addWidget(title)

        # 属性显示区域
        attrs_layout = QGridLayout()
        attrs_layout.setSpacing(5)

        # 创建属性标签
        self.hp_label = QLabel("生命值: 0")
        self.physical_attack_label = QLabel("物理攻击: 0")
        self.magic_attack_label = QLabel("法术攻击: 0")
        self.physical_defense_label = QLabel("物理防御: 0")
        self.magic_defense_label = QLabel("法术防御: 0")
        self.critical_rate_label = QLabel("暴击率: 0%")
        self.critical_damage_label = QLabel("暴击伤害: 0%")

        # 设置标签样式
        labels = [
            self.hp_label, self.physical_attack_label, self.magic_attack_label,
            self.physical_defense_label, self.magic_defense_label,
            self.critical_rate_label, self.critical_damage_label
        ]

        for label in labels:
            label.setStyleSheet("""
                QLabel {
                    color: #333;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 2px;
                }
            """)

        # 布局属性标签（2列）
        attrs_layout.addWidget(self.hp_label, 0, 0)
        attrs_layout.addWidget(self.physical_attack_label, 1, 0)
        attrs_layout.addWidget(self.magic_attack_label, 2, 0)
        attrs_layout.addWidget(self.physical_defense_label, 0, 1)
        attrs_layout.addWidget(self.magic_defense_label, 1, 1)
        attrs_layout.addWidget(self.critical_rate_label, 3, 0)
        attrs_layout.addWidget(self.critical_damage_label, 3, 1)

        layout.addLayout(attrs_layout)
        layout.addStretch()

        self.setLayout(layout)

    def update_attributes(self, character_data: Dict[str, Any]):
        """更新属性显示"""
        self.character_data = character_data

        if not character_data:
            return

        # 获取属性数据
        attributes = character_data.get('attributes', {})

        # 更新显示（不使用千位分隔符）
        self.hp_label.setText(f"生命值: {attributes.get('hp', 0)}")
        self.physical_attack_label.setText(f"物理攻击: {attributes.get('physical_attack', 0)}")
        self.magic_attack_label.setText(f"法术攻击: {attributes.get('magic_attack', 0)}")
        self.physical_defense_label.setText(f"物理防御: {attributes.get('physical_defense', 0)}")
        self.magic_defense_label.setText(f"法术防御: {attributes.get('magic_defense', 0)}")
        self.critical_rate_label.setText(f"暴击率: {attributes.get('critical_rate', 0):.1f}%")
        self.critical_damage_label.setText(f"暴击伤害: {attributes.get('critical_damage', 0):.1f}%")

    def refresh_attributes_only(self):
        """仅刷新属性显示，不刷新其他数据"""
        if not self.api_client:
            print("刷新属性失败: API客户端未设置")
            return

        try:
            character_response = self.api_client.user.get_character_detail()
            if character_response.get('success'):
                self.character_data = character_response['data']
                self.update_attributes(self.character_data)
        except Exception as e:
            print(f"刷新属性失败: {str(e)}")


class CompactEquipmentSlotWidget(QFrame):
    """紧凑型装备槽位组件"""

    # 信号
    equipment_clicked = pyqtSignal(dict, str)  # 装备点击信号
    equipment_right_clicked = pyqtSignal(dict, QPoint, str)  # 装备右键信号

    def __init__(self, slot_key: str, slot_name: str):
        super().__init__()
        self.slot_key = slot_key
        self.slot_name = slot_name
        self.equipment_data = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setFixedSize(200, 50)  # 更紧凑的尺寸
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)

        # 使用水平布局
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 装备图标区域（较小）
        self.equipment_icon = QLabel()
        self.equipment_icon.setFixedSize(40, 40)
        self.equipment_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.equipment_icon.setStyleSheet("""
            QLabel {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 20px;
            }
        """)
        layout.addWidget(self.equipment_icon)

        # 装备信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)

        # 槽位名称
        self.slot_label = QLabel(self.slot_name)
        self.slot_label.setStyleSheet("font-weight: bold; color: #333; font-size: 10px;")
        info_layout.addWidget(self.slot_label)

        # 装备名称
        self.equipment_name = QLabel("无装备")
        self.equipment_name.setStyleSheet("color: #666; font-size: 9px;")
        self.equipment_name.setWordWrap(True)
        info_layout.addWidget(self.equipment_name)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        self.setLayout(layout)
        self.update_display()

    def set_equipment(self, equipment_data: Optional[Dict]):
        """设置装备数据"""
        self.equipment_data = equipment_data
        self.update_display()

    def update_display(self):
        """更新显示"""
        if self.equipment_data:
            item_info = self.equipment_data.get('item_info', {})
            name = item_info.get('name', '未知装备')
            quality = item_info.get('quality', 'COMMON')
            equipment_slot = item_info.get('equipment_slot', '')

            # 根据装备类型设置不同图标
            slot_icons = {
                'WEAPON': '⚔️',
                'ARMOR': '🛡️',
                'HELMET': '⛑️',
                'BOOTS': '👢',
                'BRACELET': '📿',
                'MAGIC_WEAPON': '🔮'
            }
            icon = slot_icons.get(equipment_slot, '⚔️')
            self.equipment_icon.setText(icon)

            # 设置装备名称，使用更明显的颜色
            quality_colors = {
                'COMMON': '#666666',      # 深灰色
                'UNCOMMON': '#00AA00',    # 绿色
                'RARE': '#0066CC',        # 蓝色
                'EPIC': '#AA00AA',        # 紫色
                'LEGENDARY': '#FF8800',   # 橙色
                'MYTHIC': '#FF0066'       # 红色
            }
            color = quality_colors.get(quality, '#666666')
            self.equipment_name.setText(name)
            self.equipment_name.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: bold;")

            # 设置工具提示
            tooltip = self.build_tooltip(item_info)
            self.setToolTip(tooltip)
        else:
            # 无装备 - 显示空图标
            self.equipment_icon.setText("")
            self.equipment_name.setText("无装备")
            self.equipment_name.setStyleSheet("color: #666; font-size: 9px;")
            self.setToolTip("")

    def build_tooltip(self, item_info: Dict) -> str:
        """构建工具提示"""
        name = item_info.get('name', '未知装备')
        description = item_info.get('description', '')
        quality = item_info.get('quality', 'COMMON')
        required_realm = item_info.get('required_realm', 0)

        quality_name = ITEM_QUALITY.get(quality, {}).get('name', '普通')

        tooltip = f"""
        <b>{name}</b><br>
        品质: <span style="color: {ITEM_QUALITY.get(quality, {}).get('color', '#FFFFFF')}">{quality_name}</span><br>
        需求境界: {required_realm}<br>
        """

        if self.equipment_data:
            actual_attrs = self.equipment_data.get('actual_attributes', {})
            if actual_attrs:
                tooltip += "<br><b>属性加成:</b><br>"
                for attr_name, value in actual_attrs.items():
                    if value > 0:
                        attr_display = {
                            'hp': '生命值',
                            'physical_attack': '物理攻击',
                            'magic_attack': '法术攻击',
                            'physical_defense': '物理防御',
                            'magic_defense': '法术防御',
                            'critical_rate': '暴击率',
                            'critical_damage': '暴击伤害',
                            'cultivation_speed': '修炼速度',
                            'luck_bonus': '气运加成'
                        }.get(attr_name, attr_name)

                        if attr_name in ['critical_rate', 'critical_damage']:
                            tooltip += f"{attr_display}: +{value:.1f}%<br>"
                        elif attr_name == 'cultivation_speed':
                            tooltip += f"{attr_display}: +{value:.2f}x<br>"
                        else:
                            tooltip += f"{attr_display}: +{value}<br>"

        if description:
            tooltip += f"<br>{description}"

        return tooltip.strip()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.RightButton and self.equipment_data:
            self.equipment_right_clicked.emit(self.equipment_data, event.globalPosition().toPoint(), self.slot_key)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 卸下装备"""
        if event.button() == Qt.MouseButton.LeftButton and self.equipment_data:
            self.equipment_clicked.emit(self.equipment_data, self.slot_key)
        super().mouseDoubleClickEvent(event)


class EquipmentSlotWidget(QFrame):
    """装备槽位组件"""

    # 信号
    equipment_clicked = pyqtSignal(dict, str)  # 装备点击信号
    equipment_right_clicked = pyqtSignal(dict, QPoint, str)  # 装备右键信号

    def __init__(self, slot_key: str, slot_name: str):
        super().__init__()
        self.slot_key = slot_key
        self.slot_name = slot_name
        self.equipment_data = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setFixedSize(180, 80)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)

        # 使用水平布局
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 装备图标区域（完整显示）
        self.equipment_icon = QLabel()
        self.equipment_icon.setFixedSize(60, 60)
        self.equipment_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.equipment_icon.setStyleSheet("""
            QLabel {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 32px;
            }
        """)
        layout.addWidget(self.equipment_icon)

        # 装备信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # 槽位名称
        self.slot_label = QLabel(self.slot_name)
        self.slot_label.setStyleSheet("font-weight: bold; color: #333;")
        info_layout.addWidget(self.slot_label)

        # 装备名称
        self.equipment_name = QLabel("无装备")
        self.equipment_name.setStyleSheet("color: #666; font-size: 11px;")
        self.equipment_name.setWordWrap(True)
        info_layout.addWidget(self.equipment_name)

        # 装备属性简述
        self.equipment_attrs = QLabel("")
        self.equipment_attrs.setStyleSheet("color: #888; font-size: 10px;")
        self.equipment_attrs.setWordWrap(True)
        info_layout.addWidget(self.equipment_attrs)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        self.setLayout(layout)
        self.update_display()

    def set_equipment(self, equipment_data: Optional[Dict]):
        """设置装备数据"""
        self.equipment_data = equipment_data
        self.update_display()

    def update_display(self):
        """更新显示"""
        if self.equipment_data:
            item_info = self.equipment_data.get('item_info', {})
            name = item_info.get('name', '未知装备')
            quality = item_info.get('quality', 'COMMON')
            equipment_slot = item_info.get('equipment_slot', '')

            # 根据装备类型设置不同图标
            slot_icons = {
                'WEAPON': '⚔️',
                'ARMOR': '🛡️',
                'HELMET': '⛑️',
                'BOOTS': '👢',
                'BRACELET': '📿',
                'MAGIC_WEAPON': '🔮'
            }
            icon = slot_icons.get(equipment_slot, '⚔️')
            self.equipment_icon.setText(icon)

            # 设置装备名称，使用更明显的颜色
            quality_colors = {
                'COMMON': '#666666',      # 深灰色
                'UNCOMMON': '#00AA00',    # 绿色
                'RARE': '#0066CC',        # 蓝色
                'EPIC': '#AA00AA',        # 紫色
                'LEGENDARY': '#FF8800',   # 橙色
                'MYTHIC': '#FF0066'       # 红色
            }
            color = quality_colors.get(quality, '#666666')
            self.equipment_name.setText(name)
            self.equipment_name.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")

            # 设置装备属性简述
            attrs_text = self.build_attributes_text(self.equipment_data)
            self.equipment_attrs.setText(attrs_text)

            # 设置工具提示
            tooltip = self.build_tooltip(item_info)
            self.setToolTip(tooltip)
        else:
            # 无装备 - 显示空图标
            self.equipment_icon.setText("")
            self.equipment_name.setText("无装备")
            self.equipment_name.setStyleSheet("color: #666; font-size: 11px;")
            self.equipment_attrs.setText("")
            self.setToolTip("")

    def build_attributes_text(self, equipment_data: Dict) -> str:
        """构建属性简述文本"""
        actual_attrs = equipment_data.get('actual_attributes', {})
        if not actual_attrs:
            return ""

        # 显示主要属性
        attrs = []
        if actual_attrs.get('physical_attack', 0) > 0:
            attrs.append(f"+{actual_attrs['physical_attack']}物攻")
        if actual_attrs.get('magic_attack', 0) > 0:
            attrs.append(f"+{actual_attrs['magic_attack']}法攻")
        if actual_attrs.get('physical_defense', 0) > 0:
            attrs.append(f"+{actual_attrs['physical_defense']}物防")
        if actual_attrs.get('magic_defense', 0) > 0:
            attrs.append(f"+{actual_attrs['magic_defense']}法防")
        if actual_attrs.get('hp', 0) > 0:
            attrs.append(f"+{actual_attrs['hp']}生命")

        return " ".join(attrs[:2])  # 只显示前两个属性

    def build_tooltip(self, item_info: Dict) -> str:
        """构建工具提示"""
        name = item_info.get('name', '未知装备')
        description = item_info.get('description', '')
        quality = item_info.get('quality', 'COMMON')
        required_realm = item_info.get('required_realm', 0)

        quality_name = ITEM_QUALITY.get(quality, {}).get('name', '普通')

        tooltip = f"""
        <b>{name}</b><br>
        品质: <span style="color: {ITEM_QUALITY.get(quality, {}).get('color', '#FFFFFF')}">{quality_name}</span><br>
        需求境界: {required_realm}<br>
        """

        if self.equipment_data:
            actual_attrs = self.equipment_data.get('actual_attributes', {})
            if actual_attrs:
                tooltip += "<br><b>属性加成:</b><br>"
                for attr_name, value in actual_attrs.items():
                    if value > 0:
                        attr_display = {
                            'hp': '生命值',
                            'physical_attack': '物理攻击',
                            'magic_attack': '法术攻击',
                            'physical_defense': '物理防御',
                            'magic_defense': '法术防御',
                            'critical_rate': '暴击率',
                            'critical_damage': '暴击伤害',
                            'cultivation_speed': '修炼速度',
                            'luck_bonus': '气运加成'
                        }.get(attr_name, attr_name)

                        if attr_name in ['critical_rate', 'critical_damage']:
                            tooltip += f"{attr_display}: +{value:.1f}%<br>"
                        elif attr_name == 'cultivation_speed':
                            tooltip += f"{attr_display}: +{value:.2f}x<br>"
                        else:
                            tooltip += f"{attr_display}: +{value}<br>"

        if description:
            tooltip += f"<br>{description}"

        return tooltip.strip()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.RightButton and self.equipment_data:
            self.equipment_right_clicked.emit(self.equipment_data, event.globalPosition().toPoint(), self.slot_key)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 卸下装备"""
        if event.button() == Qt.MouseButton.LeftButton and self.equipment_data:
            self.equipment_clicked.emit(self.equipment_data, self.slot_key)
        super().mouseDoubleClickEvent(event)


class ItemWidget(QFrame):
    """物品格子组件"""

    # 信号
    item_clicked = pyqtSignal(dict)  # 物品点击信号
    item_right_clicked = pyqtSignal(dict, QPoint)  # 物品右键信号
    item_selected = pyqtSignal(dict, bool)  # 物品选中状态改变信号

    def __init__(self, item_data: Optional[Dict] = None):
        super().__init__()
        self.item_data = item_data
        self.is_selected = False  # 选中状态
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setFixedSize(70, 85)  # 增加高度以容纳物品名称
        self.setFrameStyle(QFrame.Shape.Box)

        # 物品图标（暂时用文字代替）
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setGeometry(5, 5, 60, 25)  # 调整位置和大小
        self.icon_label.setStyleSheet("font-size: 20px; background: transparent; border: none;")

        # 装备类型标签（中间位置）
        self.equipment_type_label = QLabel(self)
        self.equipment_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.equipment_type_label.setGeometry(5, 38, 60, 15)  # 调整到更居中的位置
        self.equipment_type_label.setStyleSheet("""
            color: #666;
            font-size: 8px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        self.equipment_type_label.hide()  # 默认隐藏

        # 物品名称标签（底部居中显示）
        self.name_label = QLabel(self)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setGeometry(2, 65, 66, 15)  # 底部位置
        self.name_label.setStyleSheet("""
            color: #000;
            font-size: 9px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        self.name_label.setWordWrap(True)

        # 数量标签（居中显示）
        self.quantity_label = QLabel(self)
        self.quantity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quantity_label.setGeometry(5, 45, 60, 15)  # 居中位置
        self.quantity_label.setStyleSheet("""
            color: #000;
            font-size: 11px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        # 品质等级标签（左下角，为装备等级预留）
        self.level_label = QLabel(self)
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.level_label.setGeometry(5, 45, 25, 15)  # 左下角位置
        self.level_label.setStyleSheet("""
            color: #000;
            font-size: 9px;
            font-weight: bold;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 2px;
            padding: 1px 2px;
        """)

        # 品质指示器（左上角小色块）
        self.quality_indicator = QLabel(self)
        self.quality_indicator.setGeometry(3, 3, 10, 10)
        self.quality_indicator.setStyleSheet("border-radius: 5px;")

        # 选中标记（右上角）
        self.selected_indicator = QLabel(self)
        self.selected_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_indicator.setGeometry(55, 3, 12, 12)
        self.selected_indicator.setStyleSheet("""
            color: #00AA00;
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        self.selected_indicator.setText("☑️")
        self.selected_indicator.hide()

        self.update_display()

    def update_display(self):
        """更新显示"""
        if self.item_data:
            item_info = self.item_data.get('item_info', {})
            quantity = self.item_data.get('quantity', 1)
            name = item_info.get('name', '未知物品')

            # 设置背景颜色和边框（根据品质和选中状态）
            quality = item_info.get('quality', 'COMMON')
            quality_info = ITEM_QUALITY.get(quality, ITEM_QUALITY['COMMON'])

            # 改进的品质颜色方案，确保文本可见
            quality_colors = {
                'COMMON': {'bg': '#f5f5f5'},      # 浅灰色背景
                'UNCOMMON': {'bg': '#e8f5e8'},    # 浅绿色背景
                'RARE': {'bg': '#e3f2fd'},        # 浅蓝色背景
                'EPIC': {'bg': '#f3e5f5'},        # 浅紫色背景
                'LEGENDARY': {'bg': '#fff3e0'},   # 浅橙色背景
                'MYTHIC': {'bg': '#ffe6e6'}       # 浅红色背景
            }

            color_scheme = quality_colors.get(quality, quality_colors['COMMON'])

            # 默认无边框，选中时显示黑色边框
            if self.is_selected:
                border_style = "2px solid #000000"
            else:
                border_style = "1px solid transparent"

            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {color_scheme['bg']};
                    border: {border_style};
                    border-radius: 6px;
                }}
                QFrame:hover {{
                    border: 1px solid #666;
                    background-color: {color_scheme['bg']};
                }}
            """)

            # 设置品质指示器颜色
            self.quality_indicator.setStyleSheet(f"""
                background-color: {quality_info['color']};
                border-radius: 5px;
                border: 1px solid #333;
            """)

            # 设置图标（简化显示）
            item_type = item_info.get('item_type', 'MISC')
            type_icons = {
                'EQUIPMENT': '⚔️',
                'CONSUMABLE': '🧪',
                'PILL': '💊',
                'MATERIAL': '🔧',
                'SEED': '🌱',
                'MISC': '📦'
            }
            icon = type_icons.get(item_type, '📦')
            self.icon_label.setText(icon)

            # 设置物品名称（底部居中显示）
            # 根据品质设置名称颜色，确保在浅色背景上可见
            name_colors = {
                'COMMON': '#000000',      # 黑色
                'UNCOMMON': '#00AA00',    # 绿色
                'RARE': '#0066CC',        # 蓝色
                'EPIC': '#AA00AA',        # 紫色
                'LEGENDARY': '#FF8800',   # 橙色
                'MYTHIC': '#CC0066'       # 深红色
            }
            name_color = name_colors.get(quality, '#000000')
            self.name_label.setText(name)
            self.name_label.setStyleSheet(f"""
                color: {name_color};
                font-size: 9px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)
            self.name_label.show()

            # 设置数量
            if quantity > 1:
                self.quantity_label.setText(str(quantity))
                self.quantity_label.show()
            else:
                self.quantity_label.hide()

            # 设置装备等级（如果是装备）
            if item_type == 'EQUIPMENT':
                required_realm = item_info.get('required_realm', 0)
                if required_realm > 0:
                    self.level_label.setText(f"Lv{required_realm}")
                    self.level_label.show()
                else:
                    self.level_label.hide()

                # 显示装备类型
                equipment_slot = item_info.get('equipment_slot', '')
                slot_type_names = {
                    'WEAPON': '武器',
                    'ARMOR': '护甲',
                    'HELMET': '头盔',
                    'BOOTS': '靴子',
                    'BRACELET': '手镯',
                    'MAGIC_WEAPON': '法宝'
                }
                type_name = slot_type_names.get(equipment_slot, '装备')
                self.equipment_type_label.setText(type_name)
                self.equipment_type_label.show()
            else:
                self.level_label.hide()
                self.equipment_type_label.hide()

            # 设置选中标记
            if self.is_selected:
                self.selected_indicator.show()
            else:
                self.selected_indicator.hide()

            # 设置工具提示
            tooltip = self.build_tooltip(item_info, quantity)
            self.setToolTip(tooltip)
        else:
            # 空格子 - 不可选中
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #f8f8f8;
                    border: 1px solid transparent;
                    border-radius: 6px;
                }}
                QFrame:hover {{
                    border: 1px solid #aaa;
                }}
            """)
            self.icon_label.setText("")
            self.name_label.setText("")
            self.name_label.hide()
            self.quantity_label.hide()
            self.level_label.hide()
            self.equipment_type_label.hide()
            self.quality_indicator.setStyleSheet("background: transparent;")
            self.selected_indicator.hide()
            self.setToolTip("")

    def build_tooltip(self, item_info: Dict, quantity: int) -> str:
        """构建工具提示"""
        name = item_info.get('name', '未知物品')
        description = item_info.get('description', '')
        quality = item_info.get('quality', 'COMMON')
        item_type = item_info.get('item_type', 'MISC')

        quality_name = ITEM_QUALITY.get(quality, {}).get('name', '普通')
        type_name = ITEM_TYPES.get(item_type, '杂物')

        tooltip = f"""
        <b>{name}</b><br>
        品质: <span style="color: {ITEM_QUALITY.get(quality, {}).get('color', '#FFFFFF')}">{quality_name}</span><br>
        类型: {type_name}<br>
        数量: {quantity}
        """

        if description:
            tooltip += f"<br><br>{description}"

        return tooltip.strip()

    def set_selected(self, selected: bool):
        """设置选中状态"""
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_display()
            if self.item_data:
                self.item_selected.emit(self.item_data, selected)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.item_data:
            # 左键点击切换选中状态（只有有物品时才可选中）
            self.set_selected(not self.is_selected)
        elif event.button() == Qt.MouseButton.RightButton and self.item_data:
            # 右键点击显示菜单
            self.item_right_clicked.emit(self.item_data, event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 使用/装备物品"""
        if self.item_data and event.button() == Qt.MouseButton.LeftButton:
            self.item_clicked.emit(self.item_data)
        super().mouseDoubleClickEvent(event)


class BackpackWindow(QDialog):
    """背包窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用父窗口的API客户端，确保token正确传递
        if hasattr(parent, 'api_client'):
            self.api_client = parent.api_client
        else:
            self.api_client = GameAPIClient()

        from client.state_manager import get_state_manager
        self.state_manager = get_state_manager()
        self.inventory_items = []
        self.equipment_items = {}
        self.character_data = {}

        # 翻页相关属性
        self.current_page = 0
        self.items_per_page = 48  # 6x8 = 48个格子
        self.max_unlocked_pages = 3  # 默认解锁3页（第三页显示为禁用状态）
        self.total_pages = 5  # 总共5页

        # 物品相关属性
        self.warehouse_visible = False
        self.warehouse_items = []

        # 根据WebEngine可用性选择实现方式
        if WEBENGINE_AVAILABLE:
            self.setup_html_ui()
            # HTML版本通过loadFinished信号加载数据
        else:
            self.setup_ui()
            self.load_data()

    def get_character_image_base64(self):
        """获取角色图片的base64编码"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            image_path = os.path.join(project_root, "client", "assets", "images", "backpack", "Taoistmonk.png")

            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    return f"data:image/png;base64,{encoded_string}"
            else:
                print(f"⚠️ 角色图片文件不存在: {image_path}")
                return None
        except Exception as e:
            print(f"❌ 读取角色图片失败: {e}")
            return None

    def setup_html_ui(self):
        """设置HTML版本的UI"""
        self.setWindowTitle("背包")
        self.setFixedSize(400, 800)  # 默认只显示左侧面板的宽度
        self.setModal(False)  # 改为非模态窗口

        # 设置窗口图标
        try:
            import os
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(project_root, "appicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"⚠️ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"❌ 设置窗口图标失败: {e}")

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()

        # 标题
        title_label = QLabel("背包管理")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        toolbar_layout.addWidget(title_label)

        toolbar_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        toolbar_layout.addWidget(refresh_btn)

        main_layout.addLayout(toolbar_layout)

        # HTML显示区域
        self.backpack_display = QWebEngineView()
        self.backpack_display.setMinimumHeight(700)

        # 禁用右键上下文菜单
        self.backpack_display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 设置样式（与聊天界面、修炼日志保持一致）
        self.backpack_display.setStyleSheet("""
            QWebEngineView {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)

        # 初始化HTML内容
        self.init_backpack_html()

        # 设置JavaScript桥接
        self.setup_js_bridge()

        main_layout.addWidget(self.backpack_display)

        # 存储原始窗口大小
        self.collapsed_size = (400, 800)
        self.expanded_size = (1000, 800)

        self.setLayout(main_layout)

        # 标记HTML是否已加载完成
        self.html_loaded = False

        # 创建属性组件（即使在HTML版本中也需要，用于数据更新）
        self.attributes_widget = CharacterAttributesWidget()
        self.attributes_widget.api_client = self.api_client

    def init_backpack_html(self):
        """初始化背包HTML页面"""
        # 获取角色图片
        character_image_data = self.get_character_image_base64()

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>背包管理</title>
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
                    line-height: 1.4;
                    overflow: hidden;
                    height: 100vh;
                    margin: 0;
                    padding: 0;
                }

                .backpack-container {
                    padding: 10px;
                    margin: 0;
                    width: 100%;
                    height: 100vh;
                    display: flex;
                    gap: 10px;
                    background-color: #fafbfc;
                    box-sizing: border-box;
                    transition: all 0.3s ease;
                    overflow: hidden;
                }

                /* 左列 - 装备面板 */
                .left-panel {
                    width: 380px;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    flex-shrink: 0;
                    overflow: hidden;
                }

                .equipment-panel {
                    background: #ffffff;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 15px;
                    flex: 1;
                    position: relative;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }

                /* 用户名显示 */
                .username-display {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 15px;
                    padding: 8px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    border: 1px solid #e1e5e9;
                    flex-shrink: 0;
                }

                .character-model-container {
                    position: relative;
                    width: 100%;
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 0;
                    padding: 80px 80px 80px 80px;
                }

                .character-model {
                    width: 200px;
                    height: 200px;
                    background: transparent;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    z-index: 1;
                    overflow: hidden;
                }

                .character-image {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 6px;
                }

                .character-placeholder {
                    font-size: 40px;
                    color: #6c757d;
                }

                .equipment-slot {
                    position: absolute;
                    width: 70px;
                    height: 70px;
                    background: #f8f9fa;
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 4px;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .equipment-slot:hover {
                    border-color: #3498db;
                    box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
                    transform: translateY(-1px);
                    background: #e3f2fd;
                }

                .equipment-slot.equipped {
                    border: 2px solid #28a745;
                    box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
                    background: #d4edda;
                }

                /* 装备槽位定位 - 根据设计图调整，固定位置避免悬浮移动 */
                .slot-helmet {
                    position: absolute;
                    top: 10px;
                    left: calc(50% - 35px); /* 固定位置，避免transform导致的移动 */
                }
                .slot-weapon {
                    position: absolute;
                    top: 90px;
                    left: 10px;
                }
                .slot-bracelet {
                    position: absolute;
                    top: 180px;
                    left: 10px;
                }
                .slot-armor {
                    position: absolute;
                    top: 90px;
                    right: 10px;
                }
                .slot-magic-weapon {
                    position: absolute;
                    top: 180px;
                    right: 10px;
                }
                .slot-boots {
                    position: absolute;
                    bottom: 10px;
                    left: calc(50% - 35px); /* 固定位置，避免transform导致的移动 */
                }

                /* 空槽位样式 */
                .equipment-slot.empty {
                    background: #ffffff;
                    border: 2px dashed #ced4da;
                }

                .equipment-icon {
                    font-size: 20px;
                    margin-bottom: 2px;
                }

                .equipment-name {
                    font-size: 8px;
                    font-weight: bold;
                    color: #495057;
                    text-align: center;
                    line-height: 1.0;
                    max-width: 60px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .slot-label {
                    font-size: 7px;
                    color: #6c757d;
                    margin-top: 1px;
                }

                /* 角色属性面板 - 重新设计 */
                .character-attributes {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 6px;
                    padding: 12px;
                    flex-shrink: 0;
                }

                .attributes-title {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                    text-align: center;
                }

                /* 角色属性网格布局 - 按设计图排列 */
                .attributes-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    grid-template-rows: repeat(4, 1fr);
                    gap: 6px;
                    margin-bottom: 10px;
                }

                .attribute-item {
                    font-size: 11px;
                    color: #495057;
                    padding: 4px 6px;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    text-align: center;
                    font-weight: bold;
                }

                /* 生命值单独显示 */
                .hp-display {
                    font-size: 12px;
                    color: #dc3545;
                    padding: 6px;
                    background-color: #fff5f5;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    text-align: center;
                    font-weight: bold;
                    margin-bottom: 8px;
                }

                .warehouse-toggle {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 12px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                    flex-shrink: 0;
                }

                .warehouse-toggle:hover {
                    background-color: #138496;
                }

                /* 右列 - 背包物品栏 */
                .right-panel {
                    flex: 1;
                    display: none; /* 默认隐藏 */
                    flex-direction: column;
                    gap: 10px;
                    min-width: 500px;  /* 6×70px + 5×8px间距 + 左右padding = 420 + 40 + 40 ≈ 500px */
                }

                .right-panel.visible {
                    display: flex; /* 展开时显示 */
                }

                .inventory-panel {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 15px;
                    flex: 1;
                }

                .inventory-title {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 15px;
                    text-align: center;
                }

                .inventory-grid {
                    display: grid;
                    grid-template-columns: repeat(6, 70px);  /* 改为6列 */
                    grid-template-rows: repeat(8, 70px);     /* 改为8行 */
                    gap: 8px;
                    margin-bottom: 15px;
                    justify-content: center;  /* 居中对齐 */
                }

                .item-slot {
                    width: 70px;
                    height: 70px;
                    background-color: #e9ecef;  /* 空槽位灰色背景 */
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 4px;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    position: relative;
                    box-sizing: border-box;
                }

                /* 空槽位显示"空"字 */
                .item-slot.empty::before {
                    content: "空";
                    font-size: 18px;
                    color: #6c757d;
                    font-weight: bold;
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                }

                .item-slot:hover {
                    border-color: #007bff;
                    background-color: #e3f2fd;
                }

                .item-slot.has-item {
                    border-color: #28a745;
                    background-color: #f8f9fa;  /* 有物品时恢复浅色背景 */
                }

                /* 禁用的槽位样式（需要解锁） */
                .item-slot.disabled {
                    background-color: #6c757d;
                    border: 1px solid #495057;
                    cursor: not-allowed;
                    opacity: 0.6;
                }

                .item-slot.disabled::before {
                    content: "✕";
                    font-size: 28px;  /* 增大字体 */
                    color: #ffffff;
                    font-weight: bold;
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                }

                .item-slot.disabled:hover {
                    border-color: #495057;
                    background-color: #6c757d;
                }

                .item-icon {
                    font-size: 20px;
                    margin-bottom: 2px;
                }

                .item-name {
                    font-size: 8px;
                    font-weight: bold;
                    color: #495057;
                    text-align: center;
                    line-height: 1.1;
                    max-height: 16px;
                    overflow: hidden;
                }

                .item-quantity {
                    position: absolute;
                    bottom: 2px;
                    right: 2px;
                    background-color: #007bff;
                    color: white;
                    border-radius: 8px;
                    padding: 1px 4px;
                    font-size: 8px;
                    font-weight: bold;
                }

                .quality-indicator {
                    position: absolute;
                    top: 2px;
                    left: 2px;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                }

                .pagination-controls {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                    padding: 10px 0;
                }

                .page-btn {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: background-color 0.3s ease;
                }

                .page-btn:hover {
                    background-color: #5a6268;
                }

                .page-btn.active {
                    background-color: #007bff;
                }

                .page-btn:disabled {
                    background-color: #dee2e6;
                    color: #6c757d;
                    cursor: not-allowed;
                }

                .warehouse-panel {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 15px;
                    display: none;
                }

                .warehouse-panel.visible {
                    display: block;
                }

                .warehouse-title {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                    text-align: center;
                }

                .warehouse-grid {
                    display: grid;
                    grid-template-columns: repeat(5, 70px);  /* 固定每列70px */
                    grid-template-rows: repeat(7, 70px);     /* 固定每行70px */
                    gap: 6px;
                    justify-content: center;  /* 居中对齐 */
                }

                /* 品质颜色 */
                .quality-common { background-color: #6c757d; }
                .quality-uncommon { background-color: #28a745; }
                .quality-rare { background-color: #007bff; }
                .quality-epic { background-color: #6f42c1; }
                .quality-legendary { background-color: #fd7e14; }
                .quality-mythic { background-color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="backpack-container" id="backpackContainer">
                <!-- 左列 - 装备面板 -->
                <div class="left-panel">
                    <!-- 装备面板 -->
                    <div class="equipment-panel">
                        <!-- 用户名显示 -->
                        <div class="username-display" id="usernameDisplay">
                            用户名: User
                        </div>

                        <div class="character-model-container" id="equipmentContainer">
                            <!-- 中央角色模型 -->
                            <div class="character-model" id="characterModel">
                                <!-- 角色图片将通过JavaScript动态设置 -->
                            </div>
                            <!-- 装备槽位将通过JavaScript动态生成并定位 -->
                        </div>
                    </div>

                    <!-- 角色属性 -->
                    <div class="character-attributes">
                        <div class="attributes-title">角色属性</div>
                        <!-- 生命值单独显示 -->
                        <div class="hp-display" id="hpDisplay">
                            生命值: 100
                        </div>
                        <div class="attributes-grid" id="attributesGrid">
                            <!-- 属性将通过JavaScript动态更新 -->
                        </div>
                    </div>

                    <!-- 物品按钮 -->
                    <button class="warehouse-toggle" onclick="toggleInventory()" id="inventoryToggleBtn">
                        物品
                    </button>
                </div>

                <!-- 右列 - 背包物品栏 -->
                <div class="right-panel" id="rightPanel">
                    <!-- 背包面板 -->
                    <div class="inventory-panel">
                        <div class="inventory-title">背包物品</div>
                        <div class="inventory-grid" id="inventoryGrid">
                            <!-- 物品槽位将通过JavaScript动态生成 -->
                        </div>
                        <div class="pagination-controls" id="paginationControls">
                            <!-- 翻页控件将通过JavaScript动态生成 -->
                        </div>
                    </div>

                    <!-- 物品面板 -->
                    <div class="warehouse-panel" id="warehousePanel">
                        <div class="warehouse-title">物品存储</div>
                        <div class="warehouse-grid" id="warehouseGrid">
                            <!-- 物品物品将通过JavaScript动态生成 -->
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // 全局变量
                let currentPage = 0;
                let maxPages = 3;  // 增加第三页
                let totalPages = 5;
                let inventoryItems = [];
                let equipmentItems = {};
                let characterAttributes = {};
                let inventoryVisible = false;

                // 初始化背包界面
                function initBackpack() {
                    generateEquipmentSlots();
                    generateInventorySlots();
                    generatePaginationControls();
                    generateWarehouseSlots();  // 添加物品槽位生成
                    // 延迟调用updateDisplay，确保所有元素都已创建
                    setTimeout(updateDisplay, 100);
                }

                // 生成装备槽位
                function generateEquipmentSlots() {
                    const equipmentContainer = document.getElementById('equipmentContainer');
                    const slots = [
                        {key: 'HELMET', name: '头盔', icon: '⛑️', class: 'slot-helmet'},
                        {key: 'WEAPON', name: '武器', icon: '⚔️', class: 'slot-weapon'},
                        {key: 'BRACELET', name: '手镯', icon: '📿', class: 'slot-bracelet'},
                        {key: 'ARMOR', name: '护甲', icon: '🛡️', class: 'slot-armor'},
                        {key: 'MAGIC_WEAPON', name: '法宝', icon: '🔮', class: 'slot-magic-weapon'},
                        {key: 'BOOTS', name: '靴子', icon: '👢', class: 'slot-boots'}
                    ];

                    // 为每个装备槽位创建元素并定位
                    slots.forEach(slot => {
                        const slotElement = document.createElement('div');
                        slotElement.className = `equipment-slot empty ${slot.class}`;
                        slotElement.id = 'equipment-' + slot.key;
                        slotElement.innerHTML = `
                            <div class="equipment-icon">${slot.icon}</div>
                            <div class="equipment-name" id="name-${slot.key}">空</div>
                            <div class="slot-label">${slot.name}</div>
                        `;
                        slotElement.onclick = () => onEquipmentClick(slot.key);
                        slotElement.oncontextmenu = (e) => {
                            e.preventDefault();
                            onEquipmentRightClick(slot.key, e);
                        };

                        // 添加悬浮提示
                        slotElement.title = `${slot.name}槽位`;

                        equipmentContainer.appendChild(slotElement);
                    });
                }

                // 生成背包物品槽位
                function generateInventorySlots() {
                    const inventoryGrid = document.getElementById('inventoryGrid');
                    inventoryGrid.innerHTML = '';

                    for (let i = 0; i < 48; i++) {  // 改为48个槽位（6列×8行）
                        const slotElement = document.createElement('div');
                        slotElement.className = 'item-slot empty';  // 初始状态添加empty类
                        slotElement.id = 'item-' + i;
                        slotElement.onclick = () => onItemClick(i);
                        slotElement.oncontextmenu = (e) => {
                            e.preventDefault();
                            onItemRightClick(i, e);
                        };
                        inventoryGrid.appendChild(slotElement);
                    }
                }

                // 生成翻页控件
                function generatePaginationControls() {
                    const paginationControls = document.getElementById('paginationControls');
                    paginationControls.innerHTML = `
                        <button class="page-btn" id="prevBtn" onclick="prevPage()">◀ 上一页</button>
                        <span id="pageInfo">第 ${currentPage + 1} 页 / 共 ${maxPages} 页</span>
                        <button class="page-btn" id="nextBtn" onclick="nextPage()">下一页 ▶</button>
                    `;
                    updatePaginationState();
                }

                // 更新翻页状态
                function updatePaginationState() {
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    const pageInfo = document.getElementById('pageInfo');

                    if (prevBtn) prevBtn.disabled = currentPage <= 0;
                    if (nextBtn) nextBtn.disabled = currentPage >= maxPages - 1;
                    if (pageInfo) pageInfo.textContent = `第 ${currentPage + 1} 页 / 共 ${maxPages} 页`;
                }

                // 切换背包物品栏显示
                function toggleInventory() {
                    inventoryVisible = !inventoryVisible;
                    const rightPanel = document.getElementById('rightPanel');
                    const toggleBtn = document.getElementById('inventoryToggleBtn');

                    if (inventoryVisible) {
                        rightPanel.classList.add('visible');
                        toggleBtn.textContent = '关闭物品';
                        // 调整窗口大小以适应展开的内容
                        console.log('展开物品，调整窗口大小到 1000x800');
                        if (window.pyBackpack && window.pyBackpack.resizeWindow) {
                            window.pyBackpack.resizeWindow(1000, 800);
                        } else {
                            // 回退方案：通过标题传递消息
                            document.title = 'RESIZE:1000,800';
                        }
                    } else {
                        rightPanel.classList.remove('visible');
                        toggleBtn.textContent = '打开物品';
                        // 恢复窗口大小
                        console.log('收起物品，调整窗口大小到 400x800');
                        if (window.pyBackpack && window.pyBackpack.resizeWindow) {
                            window.pyBackpack.resizeWindow(400, 800);
                        } else {
                            // 回退方案：通过标题传递消息
                            document.title = 'RESIZE:400,800';
                        }
                    }
                }

                // 生成物品槽位
                function generateWarehouseSlots() {
                    const warehouseGrid = document.getElementById('warehouseGrid');
                    warehouseGrid.innerHTML = '';

                    for (let i = 0; i < 35; i++) {  // 改为35个槽位（5列×7行）
                        const slotElement = document.createElement('div');
                        slotElement.className = 'item-slot empty';  // 初始状态添加empty类
                        slotElement.id = 'warehouse-' + i;
                        slotElement.onclick = () => onWarehouseItemClick(i);
                        slotElement.oncontextmenu = (e) => {
                            e.preventDefault();
                            onWarehouseItemRightClick(i, e);
                        };
                        warehouseGrid.appendChild(slotElement);
                    }
                }

                // 更新显示
                function updateDisplay() {
                    updateEquipmentDisplay();
                    updateInventoryDisplay();
                    updateAttributesDisplay();
                }

                // 更新装备显示
                function updateEquipmentDisplay() {
                    const slots = ['HELMET', 'ARMOR', 'WEAPON', 'BOOTS', 'BRACELET', 'MAGIC_WEAPON'];
                    slots.forEach(slot => {
                        const slotElement = document.getElementById('equipment-' + slot);
                        const nameElement = document.getElementById('name-' + slot);

                        if (equipmentItems[slot]) {
                            const equipment = equipmentItems[slot];
                            const itemInfo = equipment.item_info || {};
                            slotElement.classList.remove('empty');
                            slotElement.classList.add('equipped');
                            nameElement.textContent = itemInfo.name || '未知';
                            nameElement.style.color = getQualityColor(itemInfo.quality || 'COMMON');

                            // 更新悬浮提示
                            slotElement.title = buildEquipmentTooltip(equipment);
                        } else {
                            slotElement.classList.remove('equipped');
                            slotElement.classList.add('empty');
                            nameElement.textContent = '空';
                            nameElement.style.color = '#bdc3c7';

                            // 恢复默认提示
                            const slotNames = {
                                'HELMET': '头盔', 'ARMOR': '护甲', 'WEAPON': '武器',
                                'BOOTS': '靴子', 'BRACELET': '手镯', 'MAGIC_WEAPON': '法宝'
                            };
                            slotElement.title = `${slotNames[slot]}槽位`;
                        }
                    });
                }

                // 更新背包显示
                function updateInventoryDisplay() {
                    const startIndex = currentPage * 48;  // 改为48
                    const endIndex = startIndex + 48;     // 改为48
                    const pageItems = inventoryItems.slice(startIndex, endIndex);

                    for (let i = 0; i < 48; i++) {        // 改为48
                        const slotElement = document.getElementById('item-' + i);
                        const item = pageItems[i];

                        // 第三页（currentPage === 2）的槽位显示为禁用状态
                        if (currentPage === 2) {
                            slotElement.className = 'item-slot disabled';
                            slotElement.innerHTML = '';  // 清空内容，显示锁图标
                        } else if (item) {
                            updateItemSlot(slotElement, item);
                        } else {
                            clearItemSlot(slotElement);
                        }
                    }
                }

                // 更新物品槽位
                function updateItemSlot(slotElement, item) {
                    const itemInfo = item.item_info || {};
                    const quantity = item.quantity || 1;

                    slotElement.classList.remove('empty');  // 移除empty类
                    slotElement.classList.add('has-item');
                    slotElement.innerHTML = `
                        <div class="quality-indicator quality-${(itemInfo.quality || 'common').toLowerCase()}"></div>
                        <div class="item-icon">${getItemIcon(itemInfo.item_type)}</div>
                        <div class="item-name" style="color: ${getQualityColor(itemInfo.quality)}">${itemInfo.name || '未知物品'}</div>
                        ${quantity > 1 ? `<div class="item-quantity">${quantity}</div>` : ''}
                    `;

                    slotElement.title = buildItemTooltip(item);
                }

                // 清空物品槽位
                function clearItemSlot(slotElement) {
                    slotElement.classList.remove('has-item');
                    slotElement.classList.remove('disabled');
                    slotElement.className = 'item-slot empty';  // 添加empty类显示"空"字
                    slotElement.innerHTML = '';
                    slotElement.title = '';
                }

                // 更新属性显示
                function updateAttributesDisplay() {
                    const attributesGrid = document.getElementById('attributesGrid');
                    const hpDisplay = document.getElementById('hpDisplay');
                    const usernameDisplay = document.getElementById('usernameDisplay');
                    const attributes = characterAttributes.attributes || {};

                    // 更新用户名显示
                    const username = characterAttributes.username || 'User';
                    usernameDisplay.textContent = `${username}`;

                    // 更新生命值显示
                    hpDisplay.textContent = `生命值: ${attributes.hp || 100}`;

                    // 更新其他属性（按设计图布局）
                    attributesGrid.innerHTML = `
                        <div class="attribute-item">物理攻击: ${attributes.physical_attack || 100}</div>
                        <div class="attribute-item">法术攻击: ${attributes.magic_attack || 100}</div>
                        <div class="attribute-item">物理防御: ${attributes.physical_defense || 100}</div>
                        <div class="attribute-item">法术防御: ${attributes.magic_defense || 100}</div>
                        <div class="attribute-item">暴击率: ${(attributes.critical_rate || 20).toFixed(0)}%</div>
                        <div class="attribute-item">暴击伤害: ${(attributes.critical_damage || 150).toFixed(0)}%</div>
                    `;
                }

                // 获取物品图标
                function getItemIcon(itemType) {
                    const icons = {
                        'EQUIPMENT': '⚔️',
                        'CONSUMABLE': '🧪',
                        'PILL': '💊',
                        'MATERIAL': '🔧',
                        'SEED': '🌱',
                        'MISC': '📦'
                    };
                    return icons[itemType] || '📦';
                }

                // 获取品质颜色
                function getQualityColor(quality) {
                    const colors = {
                        'COMMON': '#6c757d',
                        'UNCOMMON': '#28a745',
                        'RARE': '#007bff',
                        'EPIC': '#6f42c1',
                        'LEGENDARY': '#fd7e14',
                        'MYTHIC': '#dc3545'
                    };
                    return colors[quality] || colors['COMMON'];
                }

                // 构建物品提示
                function buildItemTooltip(item) {
                    const itemInfo = item.item_info || {};
                    const quantity = item.quantity || 1;

                    let tooltip = `${itemInfo.name || '未知物品'}\\n`;
                    tooltip += `品质: ${getQualityName(itemInfo.quality)}\\n`;
                    tooltip += `类型: ${getTypeName(itemInfo.item_type)}\\n`;
                    tooltip += `数量: ${quantity}`;

                    if (itemInfo.description) {
                        tooltip += `\\n\\n${itemInfo.description}`;
                    }

                    return tooltip;
                }

                // 构建装备提示
                function buildEquipmentTooltip(equipment) {
                    const itemInfo = equipment.item_info || {};
                    const attributes = equipment.actual_attributes || {};

                    let tooltip = `${itemInfo.name || '未知装备'}\\n`;
                    tooltip += `品质: ${getQualityName(itemInfo.quality)}\\n`;
                    tooltip += `类型: 装备\\n`;

                    // 添加属性信息
                    const attrNames = {
                        'hp': '生命值',
                        'physical_attack': '物理攻击',
                        'magic_attack': '法术攻击',
                        'physical_defense': '物理防御',
                        'magic_defense': '法术防御',
                        'critical_rate': '暴击率',
                        'critical_damage': '暴击伤害'
                    };

                    Object.keys(attributes).forEach(key => {
                        if (attributes[key] > 0) {
                            const name = attrNames[key] || key;
                            const value = key.includes('rate') || key.includes('damage') ?
                                attributes[key].toFixed(1) + '%' : attributes[key];
                            tooltip += `\\n${name}: +${value}`;
                        }
                    });

                    if (itemInfo.description) {
                        tooltip += `\\n\\n${itemInfo.description}`;
                    }

                    return tooltip;
                }

                // 获取品质名称
                function getQualityName(quality) {
                    const names = {
                        'COMMON': '普通',
                        'UNCOMMON': '优秀',
                        'RARE': '稀有',
                        'EPIC': '史诗',
                        'LEGENDARY': '传说',
                        'MYTHIC': '神话'
                    };
                    return names[quality] || names['COMMON'];
                }

                // 获取类型名称
                function getTypeName(itemType) {
                    const names = {
                        'EQUIPMENT': '装备',
                        'CONSUMABLE': '消耗品',
                        'PILL': '丹药',
                        'MATERIAL': '材料',
                        'SEED': '种子',
                        'MISC': '杂物'
                    };
                    return names[itemType] || names['MISC'];
                }

                // 翻页功能
                function prevPage() {
                    if (currentPage > 0) {
                        currentPage--;
                        updateInventoryDisplay();
                        updatePaginationState();
                    }
                }

                function nextPage() {
                    if (currentPage < maxPages - 1) {
                        currentPage++;
                        updateInventoryDisplay();
                        updatePaginationState();
                    }
                }

                // 事件处理函数（这些将通过Python调用）
                function onEquipmentClick(slot) {
                    // 通过Qt的JavaScript桥接调用Python方法
                    if (window.pyBackpack) {
                        window.pyBackpack.onEquipmentClick(slot);
                    }
                }

                function onEquipmentRightClick(slot, event) {
                    if (window.pyBackpack) {
                        window.pyBackpack.onEquipmentRightClick(slot, event.clientX, event.clientY);
                    }
                }

                function onItemClick(index) {
                    if (window.pyBackpack) {
                        window.pyBackpack.onItemClick(index);
                    }
                }

                function onItemRightClick(index, event) {
                    if (window.pyBackpack) {
                        window.pyBackpack.onItemRightClick(index, event.clientX, event.clientY);
                    }
                }

                function onWarehouseItemClick(index) {
                    if (window.pyBackpack) {
                        window.pyBackpack.onWarehouseItemClick(index);
                    }
                }

                function onWarehouseItemRightClick(index, event) {
                    if (window.pyBackpack) {
                        window.pyBackpack.onWarehouseItemRightClick(index, event.clientX, event.clientY);
                    }
                }

                // 设置角色图片
                function setCharacterImage(imageData) {
                    const characterModel = document.getElementById('characterModel');
                    if (imageData && characterModel) {
                        characterModel.innerHTML = `
                            <img src="${imageData}"
                                 alt="角色模型"
                                 class="character-image"
                                 onerror="this.style.display='none';">
                        `;
                    } else if (characterModel) {
                        // 如果没有图片数据，显示占位符
                        characterModel.innerHTML = '<div class="character-placeholder">👤</div>';
                    }
                }

                // 页面加载完成后初始化
                document.addEventListener('DOMContentLoaded', function() {
                    initBackpack();

                    // 设置角色图片
                    if (window.characterImageData) {
                        setCharacterImage(window.characterImageData);
                    } else {
                        // 如果没有角色图片数据，显示占位符
                        setCharacterImage(null);
                    }
                });
            </script>
        </body>
        </html>
        """

        # 将角色图片数据注入到HTML中
        if character_image_data:
            html_template = html_template.replace(
                '</body>',
                f'<script>window.characterImageData = "{character_image_data}";</script></body>'
            )

        self.backpack_display.setHtml(html_template)

        # 监听页面加载完成事件
        self.backpack_display.loadFinished.connect(self.on_html_load_finished)

    def on_html_load_finished(self, success: bool):
        """HTML页面加载完成回调"""
        if success:
            print("✅ HTML页面加载完成")
            self.html_loaded = True
            # 页面加载完成后，延迟一点时间再加载数据，确保JavaScript也初始化完成
            QTimer.singleShot(100, self.load_initial_data)
        else:
            print("❌ HTML页面加载失败")

    def load_initial_data(self):
        """加载初始数据（仅用于HTML版本）"""
        if hasattr(self, 'html_loaded') and self.html_loaded:
            print("🔄 开始加载初始数据...")
            self.load_data()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("背包")
        self.setFixedSize(950, 800)  # 保持窗口大小
        self.setModal(False)  # 改为非模态窗口

        # 设置窗口图标
        try:
            import os
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(project_root, "appicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"⚠️ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"❌ 设置窗口图标失败: {e}")

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()

        # 整理按钮
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按类型排序", "按品质排序", "按名称排序"])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        toolbar_layout.addWidget(QLabel("整理:"))
        toolbar_layout.addWidget(self.sort_combo)

        toolbar_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(refresh_btn)

        main_layout.addLayout(toolbar_layout)

        # 内容区域
        content_layout = QHBoxLayout()

        # 左侧：属性和装备区域
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel)

        # 右侧：背包格子
        inventory_frame = self.create_inventory_frame()
        content_layout.addWidget(inventory_frame)

        main_layout.addLayout(content_layout)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # 设置属性组件的API客户端
        self.attributes_widget.api_client = self.api_client

    def create_left_panel(self) -> QFrame:
        """创建左侧面板（属性+装备）"""
        panel = QFrame()
        panel.setFixedWidth(240)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 上部：角色属性
        self.attributes_widget = CharacterAttributesWidget()
        layout.addWidget(self.attributes_widget)

        # 下部：装备栏
        equipment_frame = self.create_equipment_frame()
        layout.addWidget(equipment_frame)

        panel.setLayout(layout)
        return panel

    def create_equipment_frame(self) -> QFrame:
        """创建装备栏框架"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setFixedSize(220, 380)  # 固定大小，更紧凑

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)  # 减少间距

        # 标题
        title = QLabel("装备栏")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; font-weight: bold;")
        layout.addWidget(title)

        # 装备槽位
        self.equipment_slots = {}

        for slot_key, slot_name in EQUIPMENT_SLOTS.items():
            equipment_slot = CompactEquipmentSlotWidget(slot_key, slot_name)
            equipment_slot.equipment_clicked.connect(self.on_equipment_clicked)
            equipment_slot.equipment_right_clicked.connect(self.on_equipment_right_clicked)

            layout.addWidget(equipment_slot)
            self.equipment_slots[slot_key] = equipment_slot

        layout.addStretch()
        frame.setLayout(layout)
        return frame

    def create_inventory_frame(self) -> QFrame:
        """创建背包格子框架"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题和页面信息
        header_layout = QHBoxLayout()

        title = QLabel("背包")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 页面信息标签
        self.page_info_label = QLabel(f"第 {self.current_page + 1} 页 / 共 {self.total_pages} 页")
        header_layout.addWidget(self.page_info_label)

        layout.addLayout(header_layout)

        # 背包格子容器（不使用滚动区域）
        self.inventory_widget = QWidget()
        self.inventory_layout = QGridLayout()
        self.inventory_layout.setSpacing(8)  # 增加间距以适应更高的格子
        self.inventory_layout.setContentsMargins(5, 5, 5, 5)

        # 创建背包格子（6x6 = 36个格子）
        self.inventory_slots = []
        self.selected_slots = []  # 记录选中的格子
        for row in range(6):
            for col in range(6):
                item_widget = ItemWidget()
                item_widget.item_clicked.connect(self.on_item_clicked)
                item_widget.item_right_clicked.connect(self.on_item_right_clicked)
                item_widget.item_selected.connect(self.on_item_selected)

                self.inventory_layout.addWidget(item_widget, row, col)
                self.inventory_slots.append(item_widget)

        self.inventory_widget.setLayout(self.inventory_layout)
        layout.addWidget(self.inventory_widget)

        # 翻页控件
        page_layout = QHBoxLayout()

        # 上一页按钮
        self.prev_page_btn = QPushButton("◀ 上一页")
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.prev_page_btn.setEnabled(False)  # 初始在第一页
        page_layout.addWidget(self.prev_page_btn)

        page_layout.addStretch()

        # 页面指示器
        self.page_indicator_layout = QHBoxLayout()
        self.update_page_indicators()
        page_layout.addLayout(self.page_indicator_layout)

        page_layout.addStretch()

        # 下一页按钮
        self.next_page_btn = QPushButton("下一页 ▶")
        self.next_page_btn.clicked.connect(self.next_page)
        page_layout.addWidget(self.next_page_btn)

        layout.addLayout(page_layout)

        frame.setLayout(layout)
        return frame

    def load_data(self):
        """加载数据"""
        # 如果没有API客户端，跳过数据加载
        if not self.api_client:
            print("⚠️ 没有API客户端，跳过数据加载")
            # 如果使用HTML版本，更新HTML显示
            if WEBENGINE_AVAILABLE and hasattr(self, 'backpack_display'):
                self.update_html_display()
            return

        try:
            # 加载角色属性数据
            character_response = self.api_client.user.get_character_detail()
            if character_response.get('success'):
                self.character_data = character_response['data']
                if hasattr(self, 'attributes_widget'):
                    self.attributes_widget.update_attributes(self.character_data)

            # 加载背包数据
            inventory_response = self.api_client.inventory.get_inventory()
            if inventory_response.get('success'):
                self.inventory_items = inventory_response['data']['items']
                self.update_inventory_display()

            # 加载装备数据
            equipment_response = self.api_client.inventory.get_equipment()
            if equipment_response.get('success'):
                equipment_data = equipment_response['data'].get('equipment', {}) or {}
                self.equipment_items = equipment_data
                self.update_equipment_display()

        except Exception as e:
            print(f"❌ 加载数据失败: {str(e)}")
            # 不显示错误对话框，避免影响用户体验

        # 如果使用HTML版本，更新HTML显示
        if WEBENGINE_AVAILABLE and hasattr(self, 'backpack_display'):
            self.update_html_display()

    def update_html_display(self):
        """更新HTML显示"""
        if not hasattr(self, 'backpack_display'):
            return

        # 确保HTML页面已加载完成
        if hasattr(self, 'html_loaded') and not self.html_loaded:
            print("⚠️ HTML页面尚未加载完成，跳过数据更新")
            return

        try:
            # 更新JavaScript变量
            js_code = f"""
                if (typeof inventoryItems !== 'undefined') {{
                    inventoryItems = {self.inventory_items_to_js()};
                    equipmentItems = {self.equipment_items_to_js()};
                    characterAttributes = {self.character_data_to_js()};
                    currentPage = {self.current_page};
                    maxPages = {self.max_unlocked_pages};
                    totalPages = {self.total_pages};
                    if (typeof updateDisplay === 'function') {{
                        updateDisplay();
                    }}
                }}
            """

            # 异步执行JavaScript
            self.backpack_display.page().runJavaScript(js_code, lambda result: None)

        except Exception as e:
            print(f"❌ 更新HTML显示失败: {e}")

    def inventory_items_to_js(self):
        """将背包物品转换为JavaScript格式"""
        import json
        try:
            return json.dumps(self.inventory_items, ensure_ascii=False)
        except:
            return "[]"

    def equipment_items_to_js(self):
        """将装备物品转换为JavaScript格式"""
        import json
        try:
            return json.dumps(self.equipment_items, ensure_ascii=False)
        except:
            return "{}"

    def character_data_to_js(self):
        """将角色数据转换为JavaScript格式"""
        import json
        try:
            # 确保包含用户名信息
            data = self.character_data.copy() if self.character_data else {}

            # 用户名应该从状态管理器的user_info中获取，而不是从character_data
            # 因为character_data只包含角色游戏数据，不包含登录用户名
            if hasattr(self, 'state_manager') and self.state_manager:
                user_info = self.state_manager.user_info  # 使用属性而不是方法
                if user_info and 'username' in user_info:
                    data['username'] = user_info['username']
                    print(f"✅ 从状态管理器获取用户名: {user_info['username']}")
                else:
                    data['username'] = 'User'
                    print(f"⚠️ 状态管理器中没有用户名，user_info: {user_info}")
            else:
                data['username'] = 'User'
                print("⚠️ 没有状态管理器，使用默认用户名")

            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 转换角色数据到JS失败: {e}")
            return '{"username": "User"}'

    def load_equipment_and_inventory(self):
        """仅加载装备和背包数据，不加载角色属性"""
        try:
            # 加载背包数据
            inventory_response = self.api_client.inventory.get_inventory()
            if inventory_response.get('success'):
                self.inventory_items = inventory_response['data']['items']
                self.update_inventory_display()

            # 加载装备数据
            equipment_response = self.api_client.inventory.get_equipment()
            if equipment_response.get('success'):
                equipment_data = equipment_response['data'].get('equipment', {}) or {}
                self.equipment_items = equipment_data
                self.update_equipment_display()

        except Exception as e:
            print(f"加载装备和背包数据失败: {str(e)}")

        # 如果使用HTML版本，更新HTML显示
        if WEBENGINE_AVAILABLE and hasattr(self, 'backpack_display'):
            self.update_html_display()

    def setup_js_bridge(self):
        """设置JavaScript桥接"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'backpack_display'):
            return

        # 直接使用简单的桥接方案
        self.setup_simple_js_bridge()

    def setup_simple_js_bridge(self):
        """设置简单的JavaScript桥接（回退方案）"""
        def inject_simple_bridge():
            js_code = """
                window.pyBackpack = {
                    resizeWindow: function(width, height) {
                        console.log('请求调整窗口大小:', width, height);
                        // 通过修改页面标题来传递消息给Python
                        document.title = 'RESIZE:' + width + ',' + height;
                        // 延迟恢复标题，避免重复触发
                        setTimeout(function() {
                            document.title = '背包管理';
                        }, 100);
                    },
                    onEquipmentClick: function(slot) {
                        console.log('装备点击:', slot);
                        document.title = 'EQUIPMENT_CLICK:' + slot;
                        setTimeout(function() { document.title = '背包管理'; }, 100);
                    },
                    onItemClick: function(index) {
                        console.log('物品点击:', index);
                        document.title = 'ITEM_CLICK:' + index;
                        setTimeout(function() { document.title = '背包管理'; }, 100);
                    }
                };
                console.log('✅ 简单JavaScript桥接已建立');
            """
            self.backpack_display.page().runJavaScript(js_code, lambda result: None)

        QTimer.singleShot(500, inject_simple_bridge)  # 减少延迟，更快建立桥接

        # 监听标题变化
        self.backpack_display.titleChanged.connect(self.handle_title_message)

    def handle_title_message(self, title: str):
        """处理通过标题传递的消息"""
        try:
            if title.startswith('RESIZE:'):
                size_str = title[7:]  # 移除'RESIZE:'前缀
                width, height = map(int, size_str.split(','))
                print(f"📏 收到窗口大小调整请求: {width}x{height}")
                self.resize_window_from_js(width, height)
            elif title.startswith('EQUIPMENT_CLICK:'):
                slot = title[16:]  # 移除'EQUIPMENT_CLICK:'前缀
                print(f"⚔️ 装备点击: {slot}")
                # TODO: 处理装备点击
            elif title.startswith('ITEM_CLICK:'):
                index = int(title[11:])  # 移除'ITEM_CLICK:'前缀
                print(f"📦 物品点击: {index}")
                # TODO: 处理物品点击
        except Exception as e:
            print(f"❌ 处理标题消息失败: {e}")

    def resize_window_from_js(self, width: int, height: int):
        """从JavaScript调用的窗口大小调整方法"""
        try:
            # 先设置最小大小，然后调整到目标大小
            self.setMinimumSize(width, height)
            self.setMaximumSize(width, height)
            self.resize(width, height)
            print(f"✅ 窗口大小已调整为: {width}x{height}")
        except Exception as e:
            print(f"❌ 调整窗口大小失败: {e}")

    def update_inventory_display(self):
        """更新背包显示"""
        # 如果使用HTML版本
        if WEBENGINE_AVAILABLE and hasattr(self, 'backpack_display'):
            self.update_html_display()
            return

        # 传统PyQt版本的更新逻辑
        if not hasattr(self, 'inventory_slots'):
            return

        # 清空所有格子
        for slot in self.inventory_slots:
            slot.item_data = None
            slot.update_display()

        # 计算当前页面的物品范围
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page

        # 获取当前页面的物品
        current_page_items = self.inventory_items[start_index:end_index]

        # 填充物品到格子
        for i, item_data in enumerate(current_page_items):
            if i < len(self.inventory_slots):
                self.inventory_slots[i].item_data = item_data
                self.inventory_slots[i].update_display()

        # 更新翻页控件
        self.update_page_controls()

    def update_equipment_display(self):
        """更新装备显示"""
        # 如果使用HTML版本
        if WEBENGINE_AVAILABLE and hasattr(self, 'backpack_display'):
            self.update_html_display()
            return

        # 传统PyQt版本的更新逻辑
        if not hasattr(self, 'equipment_slots'):
            return

        # 清空所有装备槽
        for slot_widget in self.equipment_slots.values():
            slot_widget.set_equipment(None)

        # 填充装备数据
        for slot_key, equipment_data in self.equipment_items.items():
            if slot_key in self.equipment_slots:
                self.equipment_slots[slot_key].set_equipment(equipment_data)

    def update_page_indicators(self):
        """更新页面指示器"""
        # 清除现有指示器
        for i in reversed(range(self.page_indicator_layout.count())):
            child = self.page_indicator_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 创建页面指示器按钮
        for page in range(self.total_pages):
            page_btn = QPushButton(str(page + 1))
            page_btn.setFixedSize(30, 30)

            if page < self.max_unlocked_pages:
                # 已解锁页面
                if page == self.current_page:
                    page_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #007acc;
                            color: white;
                            border: 2px solid #005a9e;
                            border-radius: 15px;
                            font-weight: bold;
                        }
                    """)
                else:
                    page_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f0f0f0;
                            color: #333;
                            border: 1px solid #ccc;
                            border-radius: 15px;
                        }
                        QPushButton:hover {
                            background-color: #e0e0e0;
                        }
                    """)
                page_btn.clicked.connect(lambda checked, p=page: self.goto_page(p))
            else:
                # 未解锁页面
                page_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ccc;
                        color: #666;
                        border: 1px solid #999;
                        border-radius: 15px;
                    }
                """)
                page_btn.setEnabled(False)
                page_btn.setToolTip("需要道具解锁")

            self.page_indicator_layout.addWidget(page_btn)

    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_inventory_display()
            self.update_page_controls()

    def next_page(self):
        """下一页"""
        if self.current_page < self.max_unlocked_pages - 1:
            self.current_page += 1
            self.update_inventory_display()
            self.update_page_controls()

    def goto_page(self, page: int):
        """跳转到指定页面"""
        if 0 <= page < self.max_unlocked_pages:
            self.current_page = page
            self.update_inventory_display()
            self.update_page_controls()

    def update_page_controls(self):
        """更新翻页控件状态"""
        # 更新按钮状态
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < self.max_unlocked_pages - 1)

        # 更新页面信息
        self.page_info_label.setText(f"第 {self.current_page + 1} 页 / 共 {self.max_unlocked_pages} 页已解锁")

        # 更新页面指示器
        self.update_page_indicators()

    def on_item_selected(self, item_data: Dict, selected: bool):
        """物品选中状态改变事件"""
        if selected:
            # 添加到选中列表
            if item_data not in self.selected_slots:
                self.selected_slots.append(item_data)
        else:
            # 从选中列表移除
            if item_data in self.selected_slots:
                self.selected_slots.remove(item_data)

        # 更新状态显示（可以在这里添加选中数量显示等）
        print(f"当前选中物品数量: {len(self.selected_slots)}")

    def on_item_clicked(self, item_data: Dict):
        """物品双击事件 - 使用/装备物品"""
        item_info = item_data.get('item_info', {})
        item_type = item_info.get('item_type', '')

        if item_type == 'EQUIPMENT':
            # 装备类物品，尝试装备
            self.try_equip_item(item_data)
        elif item_type in ['CONSUMABLE', 'PILL']:
            # 消耗品，尝试使用
            self.try_use_item(item_data)
        else:
            # 其他物品，显示详细信息
            self.show_item_details(item_data)

    def on_item_right_clicked(self, item_data: Dict, pos: QPoint):
        """物品右键点击事件"""
        menu = QMenu(self)

        item_info = item_data.get('item_info', {})
        item_type = item_info.get('item_type', '')

        # 查看详情
        details_action = QAction("查看详情", self)
        details_action.triggered.connect(lambda: self.show_item_details(item_data))
        menu.addAction(details_action)

        # 根据物品类型添加不同操作
        if item_type == 'EQUIPMENT':
            equip_action = QAction("装备", self)
            equip_action.triggered.connect(lambda: self.try_equip_item(item_data))
            menu.addAction(equip_action)
        elif item_type in ['CONSUMABLE', 'PILL']:
            use_action = QAction("使用", self)
            use_action.triggered.connect(lambda: self.try_use_item(item_data))
            menu.addAction(use_action)

        menu.addSeparator()

        # 删除物品
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.try_delete_item(item_data))
        menu.addAction(delete_action)

        menu.exec(pos)

    def on_equipment_clicked(self, equipment_data: Dict, slot: str):
        """装备双击事件 - 卸下装备"""
        if equipment_data:
            # 获取装备名称
            item_info = equipment_data.get('item_info', {})
            equipment_name = item_info.get('name', '未知装备')
            # 卸下装备
            self.try_unequip_item(slot, equipment_name)

    def on_equipment_right_clicked(self, equipment_data: Dict, pos: QPoint, slot: str):
        """装备右键点击事件"""
        if not equipment_data:
            return

        menu = QMenu(self)

        # 获取装备名称
        item_info = equipment_data.get('item_info', {})
        equipment_name = item_info.get('name', '未知装备')

        # 查看详情
        details_action = QAction("查看详情", self)
        details_action.triggered.connect(lambda: self.show_equipment_details(equipment_data))
        menu.addAction(details_action)

        # 卸下装备
        unequip_action = QAction("卸下", self)
        unequip_action.triggered.connect(lambda: self.try_unequip_item(slot, equipment_name))
        menu.addAction(unequip_action)

        menu.exec(pos)

    def on_sort_changed(self, text: str):
        """排序方式改变"""
        sort_map = {
            "按类型排序": "type",
            "按品质排序": "quality",
            "按名称排序": "name"
        }

        sort_type = sort_map.get(text, "type")
        self.sort_inventory(sort_type)

    def try_equip_item(self, item_data: Dict):
        """尝试装备物品"""
        try:
            item_info = item_data.get('item_info', {})
            item_id = item_info.get('id')
            equipment_slot = item_info.get('equipment_slot')



            if not item_id:
                QMessageBox.warning(self, "错误", "无效的物品ID")
                return

            if not equipment_slot:
                QMessageBox.warning(self, "错误", "该装备没有指定装备部位")
                return

            response = self.api_client.inventory.equip_item(item_id, equipment_slot)
            if response.get('success'):
                # 如果使用传统UI，刷新属性显示
                if hasattr(self, 'attributes_widget'):
                    self.attributes_widget.refresh_attributes_only()
                # 刷新装备和背包数据
                self.load_equipment_and_inventory()
                QMessageBox.information(self, "成功", response.get('message', '装备成功'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '装备失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"装备物品失败: {str(e)}")

    def try_unequip_item(self, slot: str, equipment_name: str = "装备"):
        """尝试卸下装备"""
        try:
            response = self.api_client.inventory.unequip_item(slot)
            if response.get('success'):
                # 如果使用传统UI，刷新属性显示
                if hasattr(self, 'attributes_widget'):
                    self.attributes_widget.refresh_attributes_only()
                # 刷新装备和背包数据
                self.load_equipment_and_inventory()
                QMessageBox.information(self, "成功", f"成功卸下{equipment_name}")
            else:
                QMessageBox.warning(self, "失败", response.get('message', '卸下失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"卸下装备失败: {str(e)}")

    def try_use_item(self, item_data: Dict):
        """尝试使用物品"""
        try:
            item_info = item_data.get('item_info', {})
            item_id = item_info.get('id')
            quantity = item_data.get('quantity', 1)

            if not item_id:
                QMessageBox.warning(self, "错误", "无效的物品信息")
                return

            # 简单使用1个
            response = self.api_client.inventory.use_item(item_id, 1)
            if response.get('success'):
                QMessageBox.information(self, "成功", response.get('message', '使用成功'))
                self.load_data()  # 刷新数据
            else:
                QMessageBox.warning(self, "失败", response.get('message', '使用失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"使用物品失败: {str(e)}")

    def try_delete_item(self, item_data: Dict):
        """尝试删除物品"""
        try:
            item_info = item_data.get('item_info', {})
            item_name = item_info.get('name', '未知物品')

            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除 {item_name} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 这里需要inventory_item_id，暂时使用item_id（需要后续完善）
                item_id = item_data.get('item_id')
                response = self.api_client.inventory.delete_item(item_id)
                if response.get('success'):
                    QMessageBox.information(self, "成功", "物品删除成功")
                    self.load_data()  # 刷新数据
                else:
                    QMessageBox.warning(self, "失败", response.get('message', '删除失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除物品失败: {str(e)}")

    def sort_inventory(self, sort_type: str):
        """整理背包"""
        try:
            response = self.api_client.inventory.sort_inventory(sort_type)
            if response.get('success'):
                QMessageBox.information(self, "成功", response.get('message', '整理完成'))
                self.load_data()  # 刷新数据
            else:
                QMessageBox.warning(self, "失败", response.get('message', '整理失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"整理背包失败: {str(e)}")

    def show_item_details(self, item_data: Dict):
        """显示物品详情"""
        item_info = item_data.get('item_info', {})
        quantity = item_data.get('quantity', 1)

        name = item_info.get('name', '未知物品')
        description = item_info.get('description', '无描述')
        quality = item_info.get('quality', 'COMMON')
        item_type = item_info.get('item_type', 'MISC')

        quality_name = ITEM_QUALITY.get(quality, {}).get('name', '普通')
        type_name = ITEM_TYPES.get(item_type, '杂物')

        details = f"""
物品名称: {name}
品质: {quality_name}
类型: {type_name}
数量: {quantity}

描述:
{description}
        """.strip()

        QMessageBox.information(self, "物品详情", details)

    def show_equipment_details(self, equipment_data: Dict):
        """显示装备详情"""
        item_info = equipment_data.get('item_info', {})
        actual_attrs = equipment_data.get('actual_attributes', {})

        name = item_info.get('name', '未知装备')
        description = item_info.get('description', '无描述')
        quality = item_info.get('quality', 'COMMON')
        required_realm = item_info.get('required_realm', 0)

        quality_name = ITEM_QUALITY.get(quality, {}).get('name', '普通')

        details = f"""
装备名称: {name}
品质: {quality_name}
需求境界: {required_realm}

属性加成:"""

        if actual_attrs:
            for attr_name, value in actual_attrs.items():
                if value > 0:
                    attr_display = {
                        'hp': '生命值',
                        'physical_attack': '物理攻击',
                        'magic_attack': '法术攻击',
                        'physical_defense': '物理防御',
                        'magic_defense': '法术防御',
                        'critical_rate': '暴击率',
                        'critical_damage': '暴击伤害',
                        'cultivation_speed': '修炼速度',
                        'luck_bonus': '气运加成'
                    }.get(attr_name, attr_name)

                    if attr_name in ['critical_rate', 'critical_damage']:
                        details += f"\n  {attr_display}: +{value:.1f}%"
                    elif attr_name == 'cultivation_speed':
                        details += f"\n  {attr_display}: +{value:.2f}x"
                    else:
                        details += f"\n  {attr_display}: +{value}"
        else:
            details += "\n  无属性加成"

        details += f"""

描述:
{description}
        """.strip()

        QMessageBox.information(self, "装备详情", details)
