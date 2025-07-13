# 洞府窗口

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QMessageBox, QProgressBar, QTextEdit,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from typing import Dict, Any, Optional

from client.network.api_client import GameAPIClient


class CaveWindow(QDialog):
    """洞府窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 保存父窗口引用
        self.parent_window = parent

        # 使用父窗口的API客户端，确保token正确传递
        if hasattr(parent, 'api_client'):
            self.api_client = parent.api_client
        else:
            self.api_client = GameAPIClient()

        from client.state_manager import get_state_manager
        self.state_manager = get_state_manager()

        self.cave_data = {}
        self.setup_ui()
        self.load_cave_info()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("洞府")
        self.setFixedSize(800, 600)
        self.setModal(False)  # 非模态窗口

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("🏠 洞府管理")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：洞府信息和功能
        left_widget = self.create_left_panel()
        splitter.addWidget(left_widget)

        # 右侧：详细信息和日志
        right_widget = self.create_right_panel()
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # 底部按钮
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_cave_info)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 洞府基本信息
        self.cave_info_group = self.create_cave_info_group()
        layout.addWidget(self.cave_info_group)

        # 洞府升级
        self.cave_upgrade_group = self.create_cave_upgrade_group()
        layout.addWidget(self.cave_upgrade_group)

        # 聚灵阵管理
        self.spirit_array_group = self.create_spirit_array_group()
        layout.addWidget(self.spirit_array_group)

        # 洞府功能
        self.cave_features_group = self.create_cave_features_group()
        layout.addWidget(self.cave_features_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 修炼效果信息
        effect_group = QGroupBox("修炼效果")
        effect_layout = QVBoxLayout()

        self.cultivation_speed_label = QLabel("修炼速度加成: 计算中...")
        self.cultivation_speed_label.setStyleSheet("font-size: 14px; color: #2E8B57;")
        effect_layout.addWidget(self.cultivation_speed_label)

        self.spirit_density_label = QLabel("洞府灵气浓度: 计算中...")
        self.spirit_density_label.setStyleSheet("font-size: 14px; color: #4169E1;")
        effect_layout.addWidget(self.spirit_density_label)

        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)

        # 洞府说明
        description_group = QGroupBox("洞府说明")
        description_layout = QVBoxLayout()

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(200)
        self.description_text.setPlainText(
            "洞府是修仙者的重要居所，提供以下功能：\n\n"
            "• 境界突破：在洞府中可以安全地进行境界突破\n"
            "• 聚灵阵：提升修炼速度，加快修为增长\n"
            "• 洞府升级：解锁更多功能和更高的修炼效率\n\n"
            "洞府等级越高，可解锁的功能越多：\n"
            "1级：突破境界\n"
            "2级：聚灵阵\n"
            "3级：丹房\n"
            "4级：灵田\n"
            "5级及以上：更多高级功能..."
        )
        description_layout.addWidget(self.description_text)

        description_group.setLayout(description_layout)
        layout.addWidget(description_group)

        widget.setLayout(layout)
        return widget

    def create_cave_info_group(self) -> QGroupBox:
        """创建洞府信息组"""
        group = QGroupBox("洞府信息")
        layout = QGridLayout()

        # 洞府等级
        layout.addWidget(QLabel("洞府等级:"), 0, 0)
        self.cave_level_label = QLabel("1级")
        self.cave_level_label.setStyleSheet("font-weight: bold; color: #8B4513;")
        layout.addWidget(self.cave_level_label, 0, 1)

        # 聚灵阵等级
        layout.addWidget(QLabel("聚灵阵等级:"), 1, 0)
        self.spirit_array_level_label = QLabel("0级")
        self.spirit_array_level_label.setStyleSheet("font-weight: bold; color: #4169E1;")
        layout.addWidget(self.spirit_array_level_label, 1, 1)

        # 修炼速度加成
        layout.addWidget(QLabel("修炼速度:"), 2, 0)
        self.speed_bonus_label = QLabel("1.0x")
        self.speed_bonus_label.setStyleSheet("font-weight: bold; color: #2E8B57;")
        layout.addWidget(self.speed_bonus_label, 2, 1)

        group.setLayout(layout)
        return group

    def create_cave_upgrade_group(self) -> QGroupBox:
        """创建洞府升级组"""
        group = QGroupBox("洞府升级")
        layout = QVBoxLayout()

        # 升级信息
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("当前等级:"), 0, 0)
        self.current_cave_level_label = QLabel("1级")
        info_layout.addWidget(self.current_cave_level_label, 0, 1)

        info_layout.addWidget(QLabel("升级费用:"), 1, 0)
        self.cave_upgrade_cost_label = QLabel("1000 灵石")
        info_layout.addWidget(self.cave_upgrade_cost_label, 1, 1)

        layout.addLayout(info_layout)

        # 升级按钮
        self.cave_upgrade_btn = QPushButton("升级洞府")
        self.cave_upgrade_btn.clicked.connect(self.upgrade_cave)
        self.cave_upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B4513;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A0522D;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
            }
        """)
        layout.addWidget(self.cave_upgrade_btn)

        group.setLayout(layout)
        return group

    def create_spirit_array_group(self) -> QGroupBox:
        """创建聚灵阵组"""
        group = QGroupBox("聚灵阵")
        layout = QVBoxLayout()

        # 聚灵阵信息
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("当前等级:"), 0, 0)
        self.current_spirit_level_label = QLabel("0级")
        info_layout.addWidget(self.current_spirit_level_label, 0, 1)

        info_layout.addWidget(QLabel("升级费用:"), 1, 0)
        self.spirit_upgrade_cost_label = QLabel("500 灵石")
        info_layout.addWidget(self.spirit_upgrade_cost_label, 1, 1)

        info_layout.addWidget(QLabel("速度加成:"), 2, 0)
        self.spirit_bonus_label = QLabel("+20%")
        info_layout.addWidget(self.spirit_bonus_label, 2, 1)

        layout.addLayout(info_layout)

        # 升级按钮
        self.spirit_upgrade_btn = QPushButton("升级聚灵阵")
        self.spirit_upgrade_btn.clicked.connect(self.upgrade_spirit_array)
        self.spirit_upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6495ED;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
            }
        """)
        layout.addWidget(self.spirit_upgrade_btn)

        group.setLayout(layout)
        return group

    def create_cave_features_group(self) -> QGroupBox:
        """创建洞府功能组"""
        group = QGroupBox("洞府功能")
        layout = QVBoxLayout()

        # 突破功能
        breakthrough_btn = QPushButton("🌟 境界突破")
        breakthrough_btn.clicked.connect(self.show_breakthrough)
        breakthrough_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: #8B4513;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFA500;
            }
        """)
        layout.addWidget(breakthrough_btn)

        # 可用功能列表
        self.features_label = QLabel("可用功能: 境界突破")
        self.features_label.setWordWrap(True)
        self.features_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.features_label)

        group.setLayout(layout)
        return group

    def load_cave_info(self):
        """加载洞府信息"""
        try:
            response = self.api_client.game.get_cave_info()
            if response.get('success'):
                self.cave_data = response['data']
                self.update_ui()
            else:
                QMessageBox.warning(self, "错误", f"获取洞府信息失败: {response.get('message', '未知错误')}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载洞府信息失败: {str(e)}")

    def update_ui(self):
        """更新界面显示"""
        if not self.cave_data:
            return

        cave_level = self.cave_data.get('cave_level', 1)
        spirit_level = self.cave_data.get('spirit_gathering_array_level', 0)
        speed_bonus = self.cave_data.get('cultivation_speed_bonus', 1.0)
        max_cave_level = self.cave_data.get('max_cave_level', 10)
        max_spirit_level = self.cave_data.get('max_spirit_array_level', 5)
        available_features = self.cave_data.get('available_features', [])
        cave_upgrade_cost = self.cave_data.get('cave_upgrade_cost', {})
        spirit_upgrade_cost = self.cave_data.get('spirit_array_upgrade_cost', {})

        # 更新基本信息
        self.cave_level_label.setText(f"{cave_level}级")
        self.spirit_array_level_label.setText(f"{spirit_level}级")
        self.speed_bonus_label.setText(f"{speed_bonus:.1f}x")

        # 更新洞府升级信息
        self.current_cave_level_label.setText(f"{cave_level}级")
        if cave_level >= max_cave_level:
            self.cave_upgrade_cost_label.setText("已达最高等级")
            self.cave_upgrade_btn.setEnabled(False)
            self.cave_upgrade_btn.setText("已满级")
        else:
            cost_spirit = cave_upgrade_cost.get('spirit_stone', 0)
            self.cave_upgrade_cost_label.setText(f"{cost_spirit} 灵石")
            self.cave_upgrade_btn.setEnabled(True)
            self.cave_upgrade_btn.setText(f"升级到{cave_level + 1}级")

        # 更新聚灵阵信息
        self.current_spirit_level_label.setText(f"{spirit_level}级")
        if cave_level < 2:
            self.spirit_upgrade_cost_label.setText("需要2级洞府")
            self.spirit_upgrade_btn.setEnabled(False)
            self.spirit_upgrade_btn.setText("洞府等级不足")
            self.spirit_bonus_label.setText("未解锁")
        elif spirit_level >= max_spirit_level:
            self.spirit_upgrade_cost_label.setText("已达最高等级")
            self.spirit_upgrade_btn.setEnabled(False)
            self.spirit_upgrade_btn.setText("已满级")
            self.spirit_bonus_label.setText(f"{(speed_bonus - 1) * 100:.0f}%")
        else:
            cost_spirit = spirit_upgrade_cost.get('spirit_stone', 0)
            self.spirit_upgrade_cost_label.setText(f"{cost_spirit} 灵石")
            self.spirit_upgrade_btn.setEnabled(True)
            self.spirit_upgrade_btn.setText(f"升级到{spirit_level + 1}级")
            next_bonus = self.get_next_spirit_bonus(spirit_level + 1)
            self.spirit_bonus_label.setText(f"+{(next_bonus - 1) * 100:.0f}%")

        # 更新功能列表
        features_text = "可用功能: " + ", ".join(available_features) if available_features else "可用功能: 无"
        self.features_label.setText(features_text)

        # 更新右侧效果信息
        self.cultivation_speed_label.setText(f"修炼速度加成: {speed_bonus:.1f}x ({(speed_bonus - 1) * 100:.0f}%)")
        density_level = self.get_spirit_density_description(spirit_level)
        self.spirit_density_label.setText(f"洞府灵气浓度: {density_level}")

    def get_next_spirit_bonus(self, level: int) -> float:
        """获取下一级聚灵阵的速度加成"""
        bonus_map = {0: 1.0, 1: 1.2, 2: 1.5, 3: 1.8, 4: 2.2, 5: 2.5}
        return bonus_map.get(level, 1.0)

    def get_spirit_density_description(self, level: int) -> str:
        """获取灵气浓度描述"""
        descriptions = {
            0: "普通",
            1: "微弱",
            2: "一般",
            3: "浓郁",
            4: "极浓",
            5: "仙境"
        }
        return descriptions.get(level, "普通")

    def upgrade_cave(self):
        """升级洞府"""
        try:
            # 确认升级
            cave_level = self.cave_data.get('cave_level', 1)
            cost = self.cave_data.get('cave_upgrade_cost', {}).get('spirit_stone', 0)

            reply = QMessageBox.question(
                self, "确认升级",
                f"确定要将洞府升级到{cave_level + 1}级吗？\n"
                f"需要消耗: {cost} 灵石",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                response = self.api_client.game.upgrade_cave("cave")
                if response.get('success'):
                    QMessageBox.information(self, "升级成功", response.get('message', '洞府升级成功！'))
                    self.load_cave_info()  # 重新加载信息
                else:
                    QMessageBox.warning(self, "升级失败", response.get('message', '升级失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"升级洞府失败: {str(e)}")

    def upgrade_spirit_array(self):
        """升级聚灵阵"""
        try:
            # 确认升级
            spirit_level = self.cave_data.get('spirit_gathering_array_level', 0)
            cost = self.cave_data.get('spirit_array_upgrade_cost', {}).get('spirit_stone', 0)
            next_bonus = self.get_next_spirit_bonus(spirit_level + 1)

            reply = QMessageBox.question(
                self, "确认升级",
                f"确定要将聚灵阵升级到{spirit_level + 1}级吗？\n"
                f"需要消耗: {cost} 灵石\n"
                f"升级后修炼速度: {next_bonus:.1f}x",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                response = self.api_client.game.upgrade_cave("spirit_array")
                if response.get('success'):
                    QMessageBox.information(self, "升级成功", response.get('message', '聚灵阵升级成功！'))
                    self.load_cave_info()  # 重新加载信息
                else:
                    QMessageBox.warning(self, "升级失败", response.get('message', '升级失败'))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"升级聚灵阵失败: {str(e)}")

    def show_breakthrough(self):
        """显示突破功能"""
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
                        # 添加突破日志到主窗口
                        if hasattr(self.parent_window, 'lower_area_widget') and self.parent_window.lower_area_widget:
                            cultivation_log_widget = self.parent_window.lower_area_widget.get_cultivation_log_widget()
                            if cultivation_log_widget:
                                cultivation_log_widget.add_breakthrough_log(
                                    cultivation_data.get('current_realm', 0),
                                    cultivation_data.get('current_realm', 0) + 1,
                                    True
                                )
                    else:
                        QMessageBox.warning(self, "突破失败", f"💥 {message}")
                        # 添加失败日志到主窗口
                        if hasattr(self.parent_window, 'lower_area_widget') and self.parent_window.lower_area_widget:
                            cultivation_log_widget = self.parent_window.lower_area_widget.get_cultivation_log_widget()
                            if cultivation_log_widget:
                                cultivation_log_widget.add_breakthrough_log(
                                    cultivation_data.get('current_realm', 0),
                                    cultivation_data.get('current_realm', 0),
                                    False
                                )

                    # 刷新洞府信息和主窗口数据
                    self.load_cave_info()
                    if hasattr(self.parent_window, 'load_initial_data'):
                        self.parent_window.load_initial_data()
                else:
                    error_msg = breakthrough_response.get('message', '突破失败')
                    QMessageBox.warning(self, "突破失败", error_msg)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"突破时发生错误: {str(e)}")
