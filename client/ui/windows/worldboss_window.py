# 世界boss窗口

import random
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from client.network.api_client import GameAPIClient, APIException
from client.state_manager import get_state_manager


class WorldBossWindow(QDialog):
    """世界boss窗口"""
    
    # 信号定义
    boss_defeated = pyqtSignal(dict)  # boss被击败信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.state_manager = get_state_manager()
        
        # 获取API客户端
        if hasattr(parent, 'api_client'):
            self.api_client = parent.api_client
        else:
            # 如果父窗口没有api_client，创建一个新的
            server_url = self.state_manager.get_state('server_url', 'http://localhost:8000')
            self.api_client = GameAPIClient(server_url)
            if self.state_manager.access_token:
                self.api_client.set_token(self.state_manager.access_token)
        
        self.init_ui()
        self.load_boss_data()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("👹 世界boss")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("👹 世界boss - 魔龙王")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #8b0000; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Boss信息区域
        self.create_boss_info_section(layout)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ccc; margin: 10px 0;")
        layout.addWidget(line)
        
        # 战斗记录区域
        self.create_battle_log_section(layout)
        
        # 奖励信息区域
        self.create_reward_section(layout)
        
        # 按钮区域
        self.create_button_section(layout)
        
        self.setLayout(layout)
    
    def create_boss_info_section(self, layout):
        """创建Boss信息区域"""
        boss_info_layout = QVBoxLayout()
        
        # Boss血量
        hp_layout = QHBoxLayout()
        hp_label = QLabel("血量:")
        hp_label.setStyleSheet("font-weight: bold; color: #333;")
        hp_layout.addWidget(hp_label)
        
        self.hp_progress = QProgressBar()
        self.hp_progress.setMinimum(0)
        self.hp_progress.setMaximum(1000000)
        self.hp_progress.setValue(750000)  # 75%血量
        self.hp_progress.setMinimumHeight(25)
        self.hp_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #8b0000;
                border-radius: 12px;
                text-align: center;
                background-color: #f0f0f0;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:1 #cc0000);
                border-radius: 10px;
            }
        """)
        self.hp_progress.setFormat("750000 / 1000000 (75%)")
        hp_layout.addWidget(self.hp_progress)
        
        boss_info_layout.addLayout(hp_layout)
        
        # Boss属性
        attrs_layout = QHBoxLayout()
        
        left_attrs = QVBoxLayout()
        left_attrs.addWidget(QLabel("等级: 50"))
        left_attrs.addWidget(QLabel("物理攻击: 8500"))
        left_attrs.addWidget(QLabel("法术攻击: 9200"))
        
        right_attrs = QVBoxLayout()
        right_attrs.addWidget(QLabel("物理防御: 6800"))
        right_attrs.addWidget(QLabel("法术防御: 7100"))
        right_attrs.addWidget(QLabel("暴击率: 25%"))
        
        attrs_layout.addLayout(left_attrs)
        attrs_layout.addLayout(right_attrs)
        boss_info_layout.addLayout(attrs_layout)
        
        layout.addLayout(boss_info_layout)
    
    def create_battle_log_section(self, layout):
        """创建战斗记录区域"""
        battle_label = QLabel("⚔️ 最近战斗记录:")
        battle_label.setStyleSheet("font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(battle_label)
        
        self.battle_log = QTextEdit()
        self.battle_log.setMaximumHeight(150)
        self.battle_log.setReadOnly(True)
        self.battle_log.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        
        # 设置初始战斗记录
        self.update_battle_log()
        
        layout.addWidget(self.battle_log)
    
    def create_reward_section(self, layout):
        """创建奖励信息区域"""
        reward_label = QLabel("🎁 击败奖励:")
        reward_label.setStyleSheet("font-weight: bold; color: #333; margin-top: 10px;")
        layout.addWidget(reward_label)
        
        reward_text = QLabel("• 经验值: 50000\n• 金币: 10000\n• 灵石: 500\n• 龙鳞护甲 (传说级)\n• 龙血丹 x3")
        reward_text.setStyleSheet("color: #666; margin-left: 10px; line-height: 1.4;")
        layout.addWidget(reward_text)
    
    def create_button_section(self, layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 挑战按钮
        challenge_button = QPushButton("⚔️ 挑战Boss")
        challenge_button.setMinimumHeight(40)
        challenge_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
        """)
        challenge_button.clicked.connect(self.challenge_worldboss)
        button_layout.addWidget(challenge_button)
        
        # 组队按钮
        team_button = QPushButton("👥 组队挑战")
        team_button.setMinimumHeight(40)
        team_button.setStyleSheet("""
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
        """)
        team_button.clicked.connect(lambda: QMessageBox.information(self, "提示", "组队功能正在开发中..."))
        button_layout.addWidget(team_button)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setMinimumHeight(40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_boss_data(self):
        """加载Boss数据"""
        # TODO: 从服务器获取真实的Boss数据
        # 目前使用模拟数据
        pass
    
    def update_battle_log(self):
        """更新战斗记录"""
        battle_html = """
        <div style="color: #28a745;">[15:30] 玩家"剑仙"对魔龙王造成了12500点伤害！</div>
        <div style="color: #dc3545;">[15:31] 魔龙王使用"龙息"，对玩家"剑仙"造成了8200点伤害！</div>
        <div style="color: #28a745;">[15:32] 玩家"法神"对魔龙王造成了15800点法术伤害！</div>
        <div style="color: #ffc107;">[15:33] 玩家"盾卫"使用"护盾术"，为团队提供了防护！</div>
        <div style="color: #dc3545;">[15:34] 魔龙王进入狂暴状态，攻击力提升50%！</div>
        <div style="color: #28a745;">[15:35] 玩家"治愈者"为团队恢复了20000点生命值！</div>
        """
        self.battle_log.setHtml(battle_html)
    
    def challenge_worldboss(self):
        """挑战世界boss"""
        try:
            # 确认挑战
            reply = QMessageBox.question(
                self, "确认挑战",
                "确定要挑战魔龙王吗？\n\n"
                "⚠️ 注意：\n"
                "• 挑战需要消耗100点体力\n"
                "• 失败可能会损失部分修为\n"
                "• 建议组队挑战以提高成功率",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 模拟战斗结果
                success = random.random() < 0.3  # 30%成功率
                
                if success:
                    QMessageBox.information(
                        self, "挑战成功！",
                        "🎉 恭喜！您成功击败了魔龙王！\n\n"
                        "获得奖励：\n"
                        "• 经验值: +50000\n"
                        "• 金币: +10000\n"
                        "• 灵石: +500\n"
                        "• 龙鳞护甲 (传说级)\n"
                        "• 龙血丹 x3"
                    )
                    
                    # 发送boss被击败信号
                    reward_data = {
                        'success': True,
                        'exp': 50000,
                        'gold': 10000,
                        'spirit_stone': 500,
                        'items': ['龙鳞护甲', '龙血丹 x3']
                    }
                    self.boss_defeated.emit(reward_data)
                    
                    # 添加战斗日志到父窗口
                    if hasattr(self.parent_window, 'cultivation_log_widget') and self.parent_window.cultivation_log_widget:
                        self.parent_window.cultivation_log_widget.add_special_event_log("成功击败世界boss魔龙王，获得丰厚奖励！")
                else:
                    QMessageBox.warning(
                        self, "挑战失败",
                        "💥 很遗憾，您被魔龙王击败了！\n\n"
                        "损失：\n"
                        "• 体力: -100\n"
                        "• 修为: -5000\n\n"
                        "建议提升实力后再来挑战，或寻找队友组队！"
                    )
                    
                    # 添加战斗日志到父窗口
                    if hasattr(self.parent_window, 'cultivation_log_widget') and self.parent_window.cultivation_log_widget:
                        self.parent_window.cultivation_log_widget.add_special_event_log("挑战世界boss魔龙王失败，损失了一些修为")
                
                self.close()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"挑战世界boss时发生错误: {str(e)}")
