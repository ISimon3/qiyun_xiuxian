# 灵田窗口

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QMessageBox, QProgressBar, QTextEdit,
    QGroupBox, QSplitter, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QIcon
from typing import Dict, Any, Optional, List

from client.network.api_client import GameAPIClient


class FarmPlotWidget(QFrame):
    """灵田地块控件"""
    
    plot_clicked = pyqtSignal(int)  # 地块被点击信号
    
    def __init__(self, plot_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.plot_info = plot_info
        self.plot_index = plot_info.get('plot_index', 0)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setFixedSize(120, 100)
        self.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 地块标题
        title_label = QLabel(f"地块 {self.plot_index + 1}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        layout.addWidget(title_label)
        
        # 地块状态
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 进度条（种植时显示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(10)
        layout.addWidget(self.progress_bar)
        
        # 操作按钮
        self.action_btn = QPushButton()
        self.action_btn.setMaximumHeight(25)
        self.action_btn.clicked.connect(self.on_action_clicked)
        layout.addWidget(self.action_btn)
        
        self.setLayout(layout)
        self.update_display()
        
    def update_display(self):
        """更新显示"""
        if not self.plot_info.get('is_unlocked', False):
            # 未解锁
            self.setStyleSheet("background-color: #D3D3D3; border: 2px solid #A0A0A0;")
            self.status_label.setText("未解锁")
            self.action_btn.setText("解锁")
            self.action_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
        elif self.plot_info.get('seed_item_id') is None:
            # 空地
            self.setStyleSheet("background-color: #8B4513; border: 2px solid #A0522D;")
            self.status_label.setText("空地\n可种植")
            self.action_btn.setText("种植")
            self.action_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
        elif self.plot_info.get('is_ready', False):
            # 可收获
            self.setStyleSheet("background-color: #32CD32; border: 2px solid #228B22;")
            seed_name = self.plot_info.get('seed_name', '作物')
            self.status_label.setText(f"{seed_name}\n可收获!")
            self.action_btn.setText("收获")
            self.action_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
        elif self.plot_info.get('is_withered', False):
            # 枯萎
            self.setStyleSheet("background-color: #8B4513; border: 2px solid #654321;")
            self.status_label.setText("作物枯萎")
            self.action_btn.setText("清理")
            self.action_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
        else:
            # 成长中
            self.setStyleSheet("background-color: #90EE90; border: 2px solid #32CD32;")
            seed_name = self.plot_info.get('seed_name', '作物')
            stage_name = self.plot_info.get('growth_stage_name', '成长中')
            remaining_seconds = self.plot_info.get('remaining_time_seconds', 0)
            
            if remaining_seconds > 0:
                hours = remaining_seconds // 3600
                minutes = (remaining_seconds % 3600) // 60
                time_str = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"
                self.status_label.setText(f"{seed_name}\n{stage_name}\n{time_str}")
            else:
                self.status_label.setText(f"{seed_name}\n{stage_name}")
            
            self.action_btn.setText("等待")
            self.action_btn.setEnabled(False)
            
            # 显示进度条
            progress = self.plot_info.get('growth_progress', 0.0)
            self.progress_bar.setValue(int(progress * 100))
            self.progress_bar.setVisible(True)
    
    def on_action_clicked(self):
        """操作按钮点击"""
        self.plot_clicked.emit(self.plot_index)
    
    def update_plot_info(self, plot_info: Dict[str, Any]):
        """更新地块信息"""
        self.plot_info = plot_info
        self.update_display()


class FarmWindow(QDialog):
    """灵田窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用父窗口的API客户端，确保token正确传递
        if hasattr(parent, 'api_client'):
            self.api_client = parent.api_client
        else:
            self.api_client = GameAPIClient()

        from client.state_manager import get_state_manager
        self.state_manager = get_state_manager()
        
        self.farm_data = {}
        self.plot_widgets = []
        self.setup_ui()
        self.load_farm_info()
        
        # 定时器更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_farm_info)
        self.update_timer.start(30000)  # 30秒更新一次

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("灵田")
        self.setFixedSize(900, 700)
        self.setModal(False)  # 非模态窗口

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

        # 标题
        title_label = QLabel("🌱 灵田管理")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：地块网格
        left_widget = self.create_plots_panel()
        splitter.addWidget(left_widget)

        # 右侧：操作面板
        right_widget = self.create_control_panel()
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # 底部按钮
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.load_farm_info)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def create_plots_panel(self) -> QWidget:
        """创建地块面板"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 灵田信息
        info_group = QGroupBox("灵田信息")
        info_layout = QHBoxLayout()
        
        self.total_plots_label = QLabel("总地块: 12")
        self.unlocked_plots_label = QLabel("已解锁: 4")
        self.planted_plots_label = QLabel("已种植: 0")
        self.ready_plots_label = QLabel("可收获: 0")
        
        info_layout.addWidget(self.total_plots_label)
        info_layout.addWidget(self.unlocked_plots_label)
        info_layout.addWidget(self.planted_plots_label)
        info_layout.addWidget(self.ready_plots_label)
        info_layout.addStretch()
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 地块网格
        plots_group = QGroupBox("地块")
        plots_layout = QGridLayout()
        plots_layout.setSpacing(10)
        
        # 创建3x4网格的地块
        for i in range(12):
            row = i // 4
            col = i % 4
            
            plot_widget = FarmPlotWidget({"plot_index": i, "is_unlocked": False})
            plot_widget.plot_clicked.connect(self.on_plot_clicked)
            self.plot_widgets.append(plot_widget)
            plots_layout.addWidget(plot_widget, row, col)
        
        plots_group.setLayout(plots_layout)
        layout.addWidget(plots_group)

        widget.setLayout(layout)
        return widget

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 种植操作
        plant_group = QGroupBox("种植操作")
        plant_layout = QVBoxLayout()
        
        # 种子选择
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(QLabel("选择种子:"))
        self.seed_combo = QComboBox()
        self.seed_combo.setMinimumWidth(150)
        seed_layout.addWidget(self.seed_combo)
        plant_layout.addLayout(seed_layout)
        
        # 地块选择
        plot_layout = QHBoxLayout()
        plot_layout.addWidget(QLabel("选择地块:"))
        self.plot_spin = QSpinBox()
        self.plot_spin.setRange(1, 12)
        plot_layout.addWidget(self.plot_spin)
        plant_layout.addLayout(plot_layout)
        
        # 种植按钮
        self.plant_btn = QPushButton("🌱 种植")
        self.plant_btn.clicked.connect(self.plant_selected_seed)
        self.plant_btn.setStyleSheet("""
            QPushButton {
                background-color: #32CD32;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #228B22;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #808080;
            }
        """)
        plant_layout.addWidget(self.plant_btn)
        
        plant_group.setLayout(plant_layout)
        layout.addWidget(plant_group)

        # 种子信息
        seed_info_group = QGroupBox("种子信息")
        seed_info_layout = QVBoxLayout()
        
        self.seed_info_text = QTextEdit()
        self.seed_info_text.setReadOnly(True)
        self.seed_info_text.setMaximumHeight(150)
        seed_info_layout.addWidget(self.seed_info_text)
        
        seed_info_group.setLayout(seed_info_layout)
        layout.addWidget(seed_info_group)

        # 灵田说明
        description_group = QGroupBox("灵田说明")
        description_layout = QVBoxLayout()
        
        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setMaximumHeight(200)
        description_text.setPlainText(
            "灵田系统说明：\n\n"
            "• 种植：选择种子和空地块进行种植\n"
            "• 成长：作物需要时间成长，受地块类型影响\n"
            "• 收获：作物成熟后可以收获获得材料\n"
            "• 变异：高气运值可能导致作物变异\n"
            "• 解锁：消耗金币解锁更多地块\n\n"
            "地块类型：\n"
            "• 普通土地：基础成长速度\n"
            "• 肥沃土地：+30%成长速度，+20%产量\n"
            "• 灵田：+50%成长速度，+50%产量\n\n"
            "聚灵阵会加速作物成长！"
        )
        description_layout.addWidget(description_text)
        
        description_group.setLayout(description_layout)
        layout.addWidget(description_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def load_farm_info(self):
        """加载灵田信息"""
        try:
            response = self.api_client.game.get_farm_info()
            if response.get('success'):
                self.farm_data = response['data']
                self.update_ui()
            else:
                QMessageBox.warning(self, "错误", f"获取灵田信息失败: {response.get('message', '未知错误')}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载灵田信息失败: {str(e)}")

    def update_ui(self):
        """更新界面显示"""
        if not self.farm_data:
            return

        total_plots = self.farm_data.get('total_plots', 12)
        unlocked_plots = self.farm_data.get('unlocked_plots', 0)
        plots = self.farm_data.get('plots', [])
        available_seeds = self.farm_data.get('available_seeds', [])

        # 更新统计信息
        planted_count = len([p for p in plots if p.get('seed_item_id')])
        ready_count = len([p for p in plots if p.get('is_ready', False)])

        self.total_plots_label.setText(f"总地块: {total_plots}")
        self.unlocked_plots_label.setText(f"已解锁: {unlocked_plots}")
        self.planted_plots_label.setText(f"已种植: {planted_count}")
        self.ready_plots_label.setText(f"可收获: {ready_count}")

        # 更新地块显示
        for i, plot_widget in enumerate(self.plot_widgets):
            if i < len(plots):
                plot_widget.update_plot_info(plots[i])
            else:
                # 默认未解锁状态
                plot_widget.update_plot_info({"plot_index": i, "is_unlocked": False})

        # 更新种子选择
        self.seed_combo.clear()
        self.seed_combo.addItem("请选择种子", None)

        for seed in available_seeds:
            display_text = f"{seed['name']} (x{seed['quantity']}) - {seed['growth_time_hours']}h"
            self.seed_combo.addItem(display_text, seed)

        # 更新种子信息
        self.update_seed_info()

    def update_seed_info(self):
        """更新种子信息显示"""
        current_data = self.seed_combo.currentData()
        if current_data:
            seed_info = (
                f"种子名称: {current_data['name']}\n"
                f"拥有数量: {current_data['quantity']}\n"
                f"成长时间: {current_data['growth_time_hours']}小时\n"
                f"收获物品: {current_data['result_item']}\n"
                f"产量范围: {current_data['yield_range']}\n\n"
                f"提示: 地块类型和聚灵阵会影响成长速度和产量"
            )
        else:
            seed_info = "请选择种子查看详细信息"

        self.seed_info_text.setPlainText(seed_info)

    def on_plot_clicked(self, plot_index: int):
        """地块点击处理"""
        if plot_index >= len(self.farm_data.get('plots', [])):
            return

        plot_info = self.farm_data['plots'][plot_index]

        if not plot_info.get('is_unlocked', False):
            # 解锁地块
            self.unlock_plot(plot_index)
        elif plot_info.get('seed_item_id') is None:
            # 种植
            self.plot_spin.setValue(plot_index + 1)
            if self.seed_combo.currentData():
                self.plant_selected_seed()
        elif plot_info.get('is_ready', False):
            # 收获
            self.harvest_plot(plot_index)
        elif plot_info.get('is_withered', False):
            # 清理枯萎作物
            self.harvest_plot(plot_index)

    def plant_selected_seed(self):
        """种植选中的种子"""
        seed_data = self.seed_combo.currentData()
        if not seed_data:
            QMessageBox.warning(self, "提示", "请选择要种植的种子")
            return

        plot_index = self.plot_spin.value() - 1

        try:
            response = self.api_client.game.plant_seed(plot_index, seed_data['item_id'])
            if response.get('success'):
                QMessageBox.information(self, "成功", response.get('message', '种植成功！'))
                self.load_farm_info()  # 重新加载信息
            else:
                QMessageBox.warning(self, "失败", response.get('message', '种植失败'))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"种植失败: {str(e)}")

    def harvest_plot(self, plot_index: int):
        """收获地块"""
        try:
            response = self.api_client.game.harvest_plot(plot_index)
            if response.get('success'):
                message = response.get('message', '收获成功！')
                if response.get('data', {}).get('is_mutation', False):
                    message += "\n🎉 发生了变异！"
                QMessageBox.information(self, "收获成功", message)
                self.load_farm_info()  # 重新加载信息
            else:
                QMessageBox.warning(self, "失败", response.get('message', '收获失败'))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"收获失败: {str(e)}")

    def unlock_plot(self, plot_index: int):
        """解锁地块"""
        reply = QMessageBox.question(
            self, "确认解锁",
            f"确定要解锁第{plot_index + 1}块灵田吗？\n"
            f"这将消耗一定的金币。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = self.api_client.game.unlock_plot(plot_index)
                if response.get('success'):
                    QMessageBox.information(self, "成功", response.get('message', '解锁成功！'))
                    self.load_farm_info()  # 重新加载信息
                else:
                    QMessageBox.warning(self, "失败", response.get('message', '解锁失败'))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"解锁失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        super().closeEvent(event)
