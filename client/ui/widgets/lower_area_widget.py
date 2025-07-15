# 下半区域管理器 - 管理修炼日志和聊天频道的切换

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from client.ui.widgets.cultivation_log_widget import CultivationLogWidget
from client.ui.widgets.chat_channel_widget import ChatChannelWidget


class LowerAreaWidget(QWidget):
    """下半区域管理器 - 管理修炼日志和聊天频道的切换"""
    
    # 信号定义
    view_switched = pyqtSignal(str)  # 视图切换信号，参数为当前视图类型 ("log" 或 "chat")
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 当前视图状态
        self.current_view = "log"  # "log" 或 "chat"
        
        # 组件引用
        self.cultivation_log_widget = None
        self.chat_channel_widget = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setStyleSheet("background-color: #ffffff;")
        
        # 主布局
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建修炼日志组件
        self.cultivation_log_widget = CultivationLogWidget()
        self.layout.addWidget(self.cultivation_log_widget)
        
        # 创建聊天频道组件（初始隐藏）
        self.chat_channel_widget = ChatChannelWidget(self.parent_window)
        self.chat_channel_widget.setVisible(False)
        self.layout.addWidget(self.chat_channel_widget)
        
        self.setLayout(self.layout)
    
    def switch_to_chat_view(self):
        """切换到聊天界面"""
        if self.current_view == "chat":
            return

        self.current_view = "chat"

        # 隐藏修炼日志，显示聊天
        if self.cultivation_log_widget:
            self.cultivation_log_widget.setVisible(False)
        if self.chat_channel_widget:
            self.chat_channel_widget.setVisible(True)

        # 发送视图切换信号
        self.view_switched.emit("chat")
    
    def switch_to_log_view(self):
        """切换到修炼日志界面"""
        if self.current_view == "log":
            return

        self.current_view = "log"

        try:
            # 隐藏聊天，显示修炼日志
            if self.chat_channel_widget:
                self.chat_channel_widget.setVisible(False)
            if self.cultivation_log_widget:
                self.cultivation_log_widget.setVisible(True)

            # 发送视图切换信号
            self.view_switched.emit("log")
        except Exception as e:
            pass  # 切换到修炼日志界面失败
    
    def toggle_view(self):
        """切换视图"""
        try:
            if self.current_view == "log":
                self.switch_to_chat_view()
            else:
                self.switch_to_log_view()
        except Exception as e:
            pass  # 视图切换失败
    
    def get_current_view(self) -> str:
        """获取当前视图类型"""
        return self.current_view
    
    def get_cultivation_log_widget(self) -> Optional[CultivationLogWidget]:
        """获取修炼日志组件"""
        return self.cultivation_log_widget
    
    def get_chat_channel_widget(self) -> Optional[ChatChannelWidget]:
        """获取聊天频道组件"""
        return self.chat_channel_widget
