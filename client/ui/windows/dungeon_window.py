# 副本界面

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QProgressBar,
    QGroupBox, QGridLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

from client.network.api_client import APIClient


class DungeonWindow(QDialog):
    """副本界面"""
    
    # 信号
    dungeon_completed = pyqtSignal(dict)  # 副本完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用父窗口的API客户端实例，确保认证状态一致
        if parent and hasattr(parent, 'api_client'):
            self.api_client = parent.api_client
        else:
            self.api_client = APIClient()
        self.current_dungeon_data = None
        self.combat_timer = QTimer()
        self.combat_timer.timeout.connect(self.update_dungeon_status)
        
        self.init_ui()
        self.load_dungeon_list()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("副本探索")
        self.setFixedSize(800, 600)

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
        main_layout = QHBoxLayout(self)
        
        # 左侧：副本列表
        left_panel = self.create_dungeon_list_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧：副本详情/战斗界面
        right_panel = self.create_dungeon_detail_panel()
        main_layout.addWidget(right_panel, 2)
    
    def create_dungeon_list_panel(self):
        """创建副本列表面板"""
        group = QGroupBox("可用副本")
        layout = QVBoxLayout(group)
        
        # 体力显示
        self.stamina_label = QLabel("体力: 100/100")
        self.stamina_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stamina_label)
        
        # 副本列表
        self.dungeon_list = QListWidget()
        self.dungeon_list.itemClicked.connect(self.on_dungeon_selected)
        layout.addWidget(self.dungeon_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self.load_dungeon_list)
        layout.addWidget(refresh_btn)
        
        return group
    
    def create_dungeon_detail_panel(self):
        """创建副本详情面板"""
        group = QGroupBox("副本详情")
        layout = QVBoxLayout(group)
        
        # 副本信息
        self.dungeon_info_label = QLabel("请选择一个副本")
        self.dungeon_info_label.setWordWrap(True)
        layout.addWidget(self.dungeon_info_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        # 战斗区域
        self.combat_area = self.create_combat_area()
        layout.addWidget(self.combat_area)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.enter_btn = QPushButton("进入副本")
        self.enter_btn.clicked.connect(self.enter_dungeon)
        self.enter_btn.setEnabled(False)
        button_layout.addWidget(self.enter_btn)
        
        self.exit_btn = QPushButton("退出副本")
        self.exit_btn.clicked.connect(self.exit_dungeon)
        self.exit_btn.setEnabled(False)
        button_layout.addWidget(self.exit_btn)
        
        layout.addLayout(button_layout)
        
        return group
    
    def create_combat_area(self):
        """创建战斗区域"""
        group = QGroupBox("战斗")
        layout = QVBoxLayout(group)
        
        # 状态显示
        status_layout = QGridLayout()
        
        # 玩家状态
        status_layout.addWidget(QLabel("玩家:"), 0, 0)
        self.player_hp_bar = QProgressBar()
        self.player_hp_bar.setFormat("生命值: %v/%m")
        status_layout.addWidget(self.player_hp_bar, 0, 1)
        
        # 怪物状态
        status_layout.addWidget(QLabel("怪物:"), 1, 0)
        self.monster_hp_bar = QProgressBar()
        self.monster_hp_bar.setFormat("生命值: %v/%m")
        status_layout.addWidget(self.monster_hp_bar, 1, 1)
        
        layout.addLayout(status_layout)
        
        # 怪物信息
        self.monster_info_label = QLabel("暂无怪物")
        self.monster_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.monster_info_label)
        
        # 战斗按钮
        combat_button_layout = QHBoxLayout()
        
        self.attack_btn = QPushButton("普通攻击")
        self.attack_btn.clicked.connect(lambda: self.execute_combat_action("NORMAL_ATTACK"))
        self.attack_btn.setEnabled(False)
        combat_button_layout.addWidget(self.attack_btn)
        
        self.heavy_attack_btn = QPushButton("重击")
        self.heavy_attack_btn.clicked.connect(lambda: self.execute_combat_action("HEAVY_ATTACK"))
        self.heavy_attack_btn.setEnabled(False)
        combat_button_layout.addWidget(self.heavy_attack_btn)
        
        self.magic_attack_btn = QPushButton("法术攻击")
        self.magic_attack_btn.clicked.connect(lambda: self.execute_combat_action("MAGIC_ATTACK"))
        self.magic_attack_btn.setEnabled(False)
        combat_button_layout.addWidget(self.magic_attack_btn)
        
        self.heal_btn = QPushButton("治疗")
        self.heal_btn.clicked.connect(lambda: self.execute_combat_action("HEAL"))
        self.heal_btn.setEnabled(False)
        combat_button_layout.addWidget(self.heal_btn)
        
        layout.addLayout(combat_button_layout)
        
        # 战斗日志
        self.combat_log = QTextEdit()
        self.combat_log.setMaximumHeight(150)
        self.combat_log.setReadOnly(True)
        layout.addWidget(self.combat_log)
        
        group.setEnabled(False)
        return group
    
    def load_dungeon_list(self):
        """加载副本列表"""
        try:
            response = self.api_client.get("/api/v1/game/dungeons")
            
            if response and response.get("success"):
                data = response["data"]
                
                # 更新体力显示
                self.stamina_label.setText(f"体力: {data['current_stamina']}/{data['max_stamina']}")
                
                # 清空列表
                self.dungeon_list.clear()
                
                # 添加副本
                for dungeon in data["dungeons"]:
                    item = QListWidgetItem()
                    
                    # 设置显示文本
                    text = f"{dungeon['name']} ({dungeon['difficulty']})\n"
                    text += f"需要境界: {dungeon['required_realm_name']}\n"
                    text += f"体力消耗: {dungeon['stamina_cost']}"
                    
                    item.setText(text)
                    item.setData(Qt.ItemDataRole.UserRole, dungeon)
                    
                    # 设置颜色
                    if dungeon["can_enter"]:
                        item.setForeground(QColor(0, 150, 0))  # 绿色
                    else:
                        item.setForeground(QColor(150, 0, 0))  # 红色
                    
                    self.dungeon_list.addItem(item)
                
                # 检查是否在副本中
                self.check_current_dungeon_status()
                
            else:
                QMessageBox.warning(self, "错误", "获取副本列表失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载副本列表时发生错误: {str(e)}")
    
    def on_dungeon_selected(self, item):
        """选择副本"""
        dungeon_data = item.data(Qt.ItemDataRole.UserRole)
        
        # 显示副本信息
        info_text = f"副本名称: {dungeon_data['name']}\n"
        info_text += f"难度: {dungeon_data['difficulty']}\n"
        info_text += f"描述: {dungeon_data['description']}\n"
        info_text += f"需要境界: {dungeon_data['required_realm_name']}\n"
        info_text += f"体力消耗: {dungeon_data['stamina_cost']}\n"
        info_text += f"层数: {dungeon_data['max_floors']}\n"
        info_text += f"基础奖励: {dungeon_data['base_exp_reward']}经验 + {dungeon_data['base_gold_reward']}金币"
        
        self.dungeon_info_label.setText(info_text)
        
        # 设置按钮状态
        self.enter_btn.setEnabled(dungeon_data["can_enter"])
        self.current_dungeon_data = dungeon_data
    
    def check_current_dungeon_status(self):
        """检查当前副本状态"""
        try:
            response = self.api_client.get("/api/v1/game/dungeon-status")
            
            if response and response.get("success"):
                # 在副本中
                self.enter_combat_mode(response["data"])
            else:
                # 不在副本中
                self.exit_combat_mode()
                
        except Exception as e:
            # 不在副本中或其他错误
            self.exit_combat_mode()
    
    def enter_dungeon(self):
        """进入副本"""
        if not self.current_dungeon_data:
            return
        
        try:
            data = {"dungeon_id": self.current_dungeon_data["dungeon_id"]}
            response = self.api_client.post("/api/v1/game/enter-dungeon", data)
            
            if response and response.get("success"):
                QMessageBox.information(self, "成功", response["message"])
                self.enter_combat_mode(response["data"])
                self.load_dungeon_list()  # 刷新体力显示
            else:
                QMessageBox.warning(self, "失败", response.get("message", "进入副本失败"))
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"进入副本时发生错误: {str(e)}")
    
    def enter_combat_mode(self, dungeon_data):
        """进入战斗模式"""
        self.combat_area.setEnabled(True)
        self.enter_btn.setEnabled(False)
        self.exit_btn.setEnabled(True)
        
        # 更新战斗界面
        self.update_combat_display(dungeon_data)
        
        # 开始定时更新
        self.combat_timer.start(2000)  # 每2秒更新一次
        
        # 添加战斗日志
        self.add_combat_log(f"进入副本: {dungeon_data.get('dungeon_name', '未知副本')}")
        self.add_combat_log(f"当前层数: {dungeon_data.get('current_floor', 1)}")
    
    def update_combat_display(self, dungeon_data):
        """更新战斗显示"""
        # 更新玩家血量
        player_hp = dungeon_data.get("player_hp", 100)
        player_max_hp = dungeon_data.get("player_max_hp", 100)
        self.player_hp_bar.setMaximum(player_max_hp)
        self.player_hp_bar.setValue(player_hp)
        
        # 更新怪物血量
        monster_hp = dungeon_data.get("monster_hp", 0)
        monster_max_hp = dungeon_data.get("monster_max_hp", 1)
        self.monster_hp_bar.setMaximum(monster_max_hp)
        self.monster_hp_bar.setValue(monster_hp)
        
        # 更新怪物信息
        monster_info = dungeon_data.get("monster_info", {})
        if monster_info:
            monster_text = f"{monster_info.get('name', '未知怪物')} (Lv.{monster_info.get('level', 1)})\n"
            monster_text += f"{monster_info.get('description', '')}"
            self.monster_info_label.setText(monster_text)
        
        # 设置战斗按钮状态
        can_fight = player_hp > 0 and monster_hp > 0
        self.attack_btn.setEnabled(can_fight)
        self.heavy_attack_btn.setEnabled(can_fight)
        self.magic_attack_btn.setEnabled(can_fight)
        self.heal_btn.setEnabled(player_hp > 0 and player_hp < player_max_hp)
    
    def execute_combat_action(self, action_type):
        """执行战斗行动"""
        try:
            data = {"action_type": action_type}
            response = self.api_client.post("/api/v1/game/combat-action", data)
            
            if response and response.get("success"):
                result_data = response["data"]
                
                # 显示战斗结果
                for combat_result in result_data.get("combat_results", []):
                    self.add_combat_log(combat_result["description"])
                
                # 更新显示
                self.update_dungeon_status()
                
                # 检查副本状态
                if result_data.get("dungeon_status") != "IN_PROGRESS":
                    self.handle_dungeon_end(result_data["dungeon_status"])
                
            else:
                QMessageBox.warning(self, "失败", response.get("message", "战斗行动失败"))
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行战斗行动时发生错误: {str(e)}")
    
    def update_dungeon_status(self):
        """更新副本状态"""
        try:
            response = self.api_client.get("/api/v1/game/dungeon-status")
            
            if response and response.get("success"):
                self.update_combat_display(response["data"])
            else:
                # 不在副本中了
                self.exit_combat_mode()
                
        except Exception as e:
            # 可能不在副本中
            self.exit_combat_mode()
    
    def handle_dungeon_end(self, status):
        """处理副本结束"""
        self.combat_timer.stop()
        
        if status == "COMPLETED":
            QMessageBox.information(self, "恭喜", "副本完成！获得丰厚奖励！")
            self.dungeon_completed.emit({"status": "completed"})
        elif status == "FAILED":
            QMessageBox.warning(self, "失败", "副本失败！你在战斗中死亡了。")
        
        self.exit_combat_mode()
        self.load_dungeon_list()
    
    def exit_dungeon(self):
        """退出副本"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出当前副本吗？\n退出后将失去当前进度。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = self.api_client.post("/api/v1/game/exit-dungeon", {})
                
                if response and response.get("success"):
                    QMessageBox.information(self, "成功", "已退出副本")
                    self.exit_combat_mode()
                    self.load_dungeon_list()
                else:
                    QMessageBox.warning(self, "失败", response.get("message", "退出副本失败"))
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"退出副本时发生错误: {str(e)}")
    
    def exit_combat_mode(self):
        """退出战斗模式"""
        self.combat_timer.stop()
        self.combat_area.setEnabled(False)
        self.enter_btn.setEnabled(True)
        self.exit_btn.setEnabled(False)
        
        # 清空战斗显示
        self.player_hp_bar.setValue(0)
        self.monster_hp_bar.setValue(0)
        self.monster_info_label.setText("暂无怪物")
        self.combat_log.clear()
    
    def add_combat_log(self, message):
        """添加战斗日志"""
        self.combat_log.append(f"[{self.get_current_time()}] {message}")
        
        # 滚动到底部
        scrollbar = self.combat_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
