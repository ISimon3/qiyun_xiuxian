# 修炼设置对话框

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup,
    QMessageBox, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from client.network.api_client import GameAPIClient, APIException
from shared.constants import CULTIVATION_FOCUS_TYPES


class CultivationActionWorker(QThread):
    """修炼操作工作线程"""
    
    # 信号定义
    action_success = pyqtSignal(dict)  # 操作成功信号
    action_failed = pyqtSignal(str)    # 操作失败信号
    
    def __init__(self, api_client: GameAPIClient):
        super().__init__()
        self.api_client = api_client
        self.action = None
        self.params = {}
    
    def start_cultivation(self, focus_type: str):
        """开始修炼"""
        self.action = 'start_cultivation'
        self.params = {'focus_type': focus_type}
        self.start()
    
    def manual_breakthrough(self):
        """手动突破"""
        self.action = 'manual_breakthrough'
        self.params = {}
        self.start()
    
    def daily_sign_in(self):
        """每日签到"""
        self.action = 'daily_sign_in'
        self.params = {}
        self.start()
    
    def run(self):
        """执行操作"""
        try:
            if self.action == 'start_cultivation':
                response = self.api_client.game.start_cultivation(
                    self.params['focus_type']
                )
                if response.get('success'):
                    self.action_success.emit(response['data'])
                else:
                    self.action_failed.emit(response.get('message', '操作失败'))
            
            elif self.action == 'manual_breakthrough':
                response = self.api_client.game.manual_breakthrough()
                if response.get('success'):
                    self.action_success.emit(response['data'])
                else:
                    self.action_failed.emit(response.get('message', '突破失败'))
            
            elif self.action == 'daily_sign_in':
                response = self.api_client.game.daily_sign_in()
                if response.get('success'):
                    self.action_success.emit(response['data'])
                else:
                    self.action_failed.emit(response.get('message', '签到失败'))
                    
        except APIException as e:
            self.action_failed.emit(str(e))
        except Exception as e:
            self.action_failed.emit(f"未知错误: {str(e)}")


class CultivationDialog(QDialog):
    """修炼设置对话框"""
    
    def __init__(self, api_client: GameAPIClient, parent=None):
        super().__init__(parent)
        
        self.api_client = api_client
        self.worker = CultivationActionWorker(api_client)
        self.setup_worker_connections()
        
        # 当前修炼状态
        self.current_cultivation_status: Optional[Dict[str, Any]] = None
        
        self.init_ui()
        self.load_cultivation_status()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("修炼设置")
        self.setFixedSize(400, 500)
        self.setModal(True)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("修炼设置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # 当前状态区域
        self.create_status_section(main_layout)
        
        # 修炼方向选择区域
        self.create_focus_selection_section(main_layout)
        
        # 操作按钮区域
        self.create_action_buttons_section(main_layout)
        
        self.setLayout(main_layout)
    
    def create_status_section(self, parent_layout: QVBoxLayout):
        """创建状态显示区域"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)
        
        # 当前境界
        self.realm_label = QLabel("当前境界: 加载中...")
        self.realm_label.setStyleSheet("font-weight: bold; color: #495057;")
        status_layout.addWidget(self.realm_label)
        
        # 修为进度
        self.exp_progress_bar = QProgressBar()
        self.exp_progress_bar.setMinimumHeight(25)
        self.exp_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 12px;
                text-align: center;
                background-color: #e9ecef;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #28a745, stop:1 #20c997);
                border-radius: 11px;
            }
        """)
        status_layout.addWidget(self.exp_progress_bar)
        
        self.exp_label = QLabel("修为: 0 / 100 (0.0%)")
        self.exp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.exp_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        status_layout.addWidget(self.exp_label)
        
        # 修炼状态
        self.cultivation_status_label = QLabel("修炼状态: 加载中...")
        self.cultivation_status_label.setStyleSheet("font-weight: bold; color: #495057;")
        status_layout.addWidget(self.cultivation_status_label)
        
        status_frame.setLayout(status_layout)
        parent_layout.addWidget(status_frame)
    
    def create_focus_selection_section(self, parent_layout: QVBoxLayout):
        """创建修炼方向选择区域"""
        focus_label = QLabel("选择修炼方向:")
        focus_label.setStyleSheet("font-weight: bold; color: #495057; margin-top: 10px;")
        parent_layout.addWidget(focus_label)
        
        # 修炼方向选择
        self.focus_button_group = QButtonGroup()
        focus_layout = QGridLayout()
        focus_layout.setSpacing(10)
        
        row = 0
        col = 0
        for focus_key, focus_info in CULTIVATION_FOCUS_TYPES.items():
            name = focus_info['name']
            icon = focus_info['icon']
            description = focus_info['description']
            
            radio_button = QRadioButton(f"{icon} {name}")
            radio_button.setToolTip(description)
            radio_button.setStyleSheet("""
                QRadioButton {
                    font-size: 13px;
                    padding: 5px;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            
            self.focus_button_group.addButton(radio_button)
            radio_button.setProperty("focus_key", focus_key)
            
            focus_layout.addWidget(radio_button, row, col)
            
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # 默认选择第一个
        if self.focus_button_group.buttons():
            self.focus_button_group.buttons()[0].setChecked(True)
        
        parent_layout.addLayout(focus_layout)
    
    def create_action_buttons_section(self, parent_layout: QVBoxLayout):
        """创建操作按钮区域"""
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #dee2e6; margin: 10px 0;")
        parent_layout.addWidget(line)
        
        # 按钮布局
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # 开始修炼按钮
        self.start_cultivation_button = QPushButton("开始修炼")
        self.start_cultivation_button.setMinimumHeight(40)
        self.start_cultivation_button.clicked.connect(self.start_cultivation)
        self.start_cultivation_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.start_cultivation_button)
        
        # 手动突破按钮
        self.breakthrough_button = QPushButton("尝试突破")
        self.breakthrough_button.setMinimumHeight(40)
        self.breakthrough_button.clicked.connect(self.manual_breakthrough)
        self.breakthrough_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: white;
            }
        """)
        button_layout.addWidget(self.breakthrough_button)
        
        # 每日签到按钮
        self.daily_sign_button = QPushButton("每日签到")
        self.daily_sign_button.setMinimumHeight(40)
        self.daily_sign_button.clicked.connect(self.daily_sign_in)
        self.daily_sign_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.daily_sign_button)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setMinimumHeight(35)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        button_layout.addWidget(close_button)
        
        parent_layout.addLayout(button_layout)
    
    def setup_worker_connections(self):
        """设置工作线程信号连接"""
        self.worker.action_success.connect(self.on_action_success)
        self.worker.action_failed.connect(self.on_action_failed)
    
    def load_cultivation_status(self):
        """加载修炼状态"""
        try:
            response = self.api_client.game.get_cultivation_status()
            if response.get('success'):
                self.update_status_display(response['data'])
        except Exception as e:
            print(f"加载修炼状态失败: {e}")
    
    def update_status_display(self, status_data: Dict[str, Any]):
        """更新状态显示"""
        self.current_cultivation_status = status_data
        
        # 更新境界
        realm_name = status_data.get('current_realm_name', '未知')
        self.realm_label.setText(f"当前境界: {realm_name}")
        
        # 更新修为进度
        progress = status_data.get('exp_progress', 0)
        self.exp_progress_bar.setValue(int(progress))
        
        current_exp = status_data.get('current_exp', 0)
        required_exp = status_data.get('required_exp', 1)
        self.exp_label.setText(f"修为: {current_exp:,} / {required_exp:,} ({progress:.1f}%)")
        
        # 更新修炼状态
        is_cultivating = status_data.get('is_cultivating', False)
        if is_cultivating:
            self.cultivation_status_label.setText("修炼状态: 挂机修炼中")
            self.cultivation_status_label.setStyleSheet("font-weight: bold; color: #28a745;")
        else:
            self.cultivation_status_label.setText("修炼状态: 未在修炼")
            self.cultivation_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
        
        # 更新按钮状态
        can_breakthrough = status_data.get('can_breakthrough', False)
        self.breakthrough_button.setEnabled(can_breakthrough)
        if not can_breakthrough:
            self.breakthrough_button.setText("修为不足")
        else:
            breakthrough_rate = status_data.get('breakthrough_rate', 0)
            self.breakthrough_button.setText(f"尝试突破 ({breakthrough_rate:.1f}%)")
    
    def get_selected_focus(self) -> str:
        """获取选中的修炼方向"""
        for button in self.focus_button_group.buttons():
            if button.isChecked():
                return button.property("focus_key")
        return "HP"  # 默认返回体修
    
    def start_cultivation(self):
        """开始修炼"""
        focus_type = self.get_selected_focus()
        self.set_buttons_enabled(False)
        self.worker.start_cultivation(focus_type)
    
    def manual_breakthrough(self):
        """手动突破"""
        self.set_buttons_enabled(False)
        self.worker.manual_breakthrough()
    
    def daily_sign_in(self):
        """每日签到"""
        self.set_buttons_enabled(False)
        self.worker.daily_sign_in()
    
    def set_buttons_enabled(self, enabled: bool):
        """设置按钮启用状态"""
        self.start_cultivation_button.setEnabled(enabled)
        self.breakthrough_button.setEnabled(enabled)
        self.daily_sign_button.setEnabled(enabled)
    
    def on_action_success(self, result_data: Dict[str, Any]):
        """操作成功处理"""
        self.set_buttons_enabled(True)
        
        message = result_data.get('message', '操作成功')
        QMessageBox.information(self, "成功", message)
        
        # 重新加载状态
        self.load_cultivation_status()
    
    def on_action_failed(self, error_message: str):
        """操作失败处理"""
        self.set_buttons_enabled(True)
        QMessageBox.warning(self, "操作失败", error_message)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()
