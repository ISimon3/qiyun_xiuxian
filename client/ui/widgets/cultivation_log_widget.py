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

# 尝试导入WebEngine，如果失败则使用QTextEdit
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class CultivationLogWidget(QWidget):
    """修炼日志组件"""

    # 信号定义
    clear_log_requested = pyqtSignal()  # 清空日志请求信号
    cultivation_completed = pyqtSignal()  # 修炼完成信号

    def __init__(self):
        super().__init__()

        # 日志数据
        self.log_entries: List[Dict[str, Any]] = []
        self.max_log_entries = 1000  # 最大日志条数

        # 修炼状态
        self.cultivation_status: Optional[Dict[str, Any]] = None
        self.last_exp = 0
        self.last_realm = 0

        # 修炼倒计时相关
        self.current_cultivation_focus = "HP"
        self.next_cultivation_time: Optional[datetime] = None
        self.countdown_entry_id: Optional[str] = None

        self.init_ui()

        # 倒计时更新定时器
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 每秒更新一次

    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(1)  # 减少间距
        main_layout.setContentsMargins(5, 0, 5, 3)  # 减少边距

        # 标题栏
        self.create_title_bar(main_layout)

        # 日志显示区域 - 根据WebEngine可用性选择实现
        if WEBENGINE_AVAILABLE:
            self.create_html_log_area(main_layout)
        else:
            self.create_log_area(main_layout)

        self.setLayout(main_layout)

        # 延迟添加初始欢迎消息
        if WEBENGINE_AVAILABLE:
            QTimer.singleShot(500, self.add_initial_messages)
        else:
            self.add_initial_messages()

    def create_title_bar(self, parent_layout: QVBoxLayout):
        """创建标题栏 - 与聊天界面保持一致的紧凑风格"""
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        # 标题
        title_label = QLabel("📜 修炼日志")
        title_font = QFont()
        title_font.setPointSize(10)  # 与聊天界面一致
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setFixedHeight(16)  # 设置固定高度
        title_label.setStyleSheet("""
            color: #2c3e50;
            margin: 0px;
            padding: 0px;
            line-height: 1.0;
            border: none;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # 清空日志按钮 - 更紧凑的样式
        self.clear_button = QPushButton("清空")
        self.clear_button.setMaximumWidth(50)
        self.clear_button.setMaximumHeight(16)
        self.clear_button.clicked.connect(self.clear_log)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: 600;
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

    def create_html_log_area(self, parent_layout: QVBoxLayout):
        """创建HTML版本的日志显示区域"""
        # 日志显示区域 - 使用HTML渲染
        self.log_display = QWebEngineView()
        self.log_display.setMinimumHeight(400)

        # 禁用右键上下文菜单
        self.log_display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 为日志区域添加边框样式
        self.log_display.setStyleSheet("""
            QWebEngineView {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)

        # 设置初始HTML内容
        self.init_log_html()

        parent_layout.addWidget(self.log_display)

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

    def init_log_html(self):
        """初始化日志HTML页面"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>修炼日志</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    font-size: 12px;
                    background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
                    color: #333;
                    line-height: 1.4;
                    overflow-x: hidden;
                }

                .log-container {
                    padding: 8px;
                    margin: 0;
                    width: 100%;
                    height: 100vh;
                    overflow-y: auto;
                    border: 1px solid #e1e5e9;
                    border-radius: 6px;
                    background-color: #fafbfc;
                    box-sizing: border-box;
                }

                .log-entry {
                    margin: 2px 0;
                    padding: 3px 6px;
                    border-radius: 4px;
                    word-wrap: break-word;
                    font-family: "Consolas", "Courier New", monospace;
                    font-size: 11px;
                    line-height: 1.3;
                    transition: background-color 0.2s ease;
                }

                .log-entry:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }

                .log-timestamp {
                    color: #6c757d;
                    font-weight: normal;
                    margin-right: 8px;
                }

                .log-content {
                    display: inline;
                }

                /* 不同类型日志的颜色 - 适配浅色背景 */
                .log-system {
                    color: #8e44ad;
                    background-color: rgba(142, 68, 173, 0.1);
                }

                .log-cultivation {
                    color: #2980b9;
                    background-color: rgba(41, 128, 185, 0.1);
                }

                .log-breakthrough {
                    color: #d68910;
                    background-color: rgba(214, 137, 16, 0.1);
                    font-weight: 600;
                }

                .log-luck {
                    color: #229954;
                    background-color: rgba(34, 153, 84, 0.1);
                }

                .log-luck.negative {
                    color: #cb4335;
                    background-color: rgba(203, 67, 53, 0.1);
                }

                /* 特殊事件样式 */
                .log-special_event_positive {
                    color: #27ae60;
                    background-color: rgba(39, 174, 96, 0.15);
                    font-weight: 600;
                    border-left: 3px solid #27ae60;
                    padding-left: 8px;
                }

                .log-special_event_negative {
                    color: #e74c3c;
                    background-color: rgba(231, 76, 60, 0.15);
                    font-weight: 600;
                    border-left: 3px solid #e74c3c;
                    padding-left: 8px;
                }

                .log-cultivation_result {
                    color: #3498db;
                    background-color: rgba(52, 152, 219, 0.1);
                }

                .log-special {
                    color: #d35400;
                    background-color: rgba(211, 84, 0, 0.1);
                    font-weight: 600;
                }

                .log-info {
                    color: #333;
                }

                /* 滚动条样式 - 适配浅色主题 */
                .log-container::-webkit-scrollbar {
                    width: 8px;
                }

                .log-container::-webkit-scrollbar-track {
                    background: #f1f3f4;
                    border-radius: 4px;
                }

                .log-container::-webkit-scrollbar-thumb {
                    background: #c1c8cd;
                    border-radius: 4px;
                }

                .log-container::-webkit-scrollbar-thumb:hover {
                    background: #a8b2ba;
                }
            </style>
        </head>
        <body>
            <div class="log-container" id="logContainer">
                <!-- 动态添加日志条目 -->
            </div>

            <script>
                function addLogEntry(timestamp, message, logType, color) {
                    const container = document.getElementById('logContainer');
                    const entry = document.createElement('div');
                    entry.className = 'log-entry log-' + logType;

                    if (color && logType === 'luck' && color === '#e74c3c') {
                        entry.classList.add('negative');
                    }

                    entry.innerHTML = '<span class="log-timestamp">[' + timestamp + ']</span><span class="log-content">' + message + '</span>';

                    container.appendChild(entry);
                    container.scrollTop = container.scrollHeight;
                }

                function clearLog() {
                    const container = document.getElementById('logContainer');
                    container.innerHTML = '';
                }

                function updateCountdownEntry(entryId, timestamp, message) {
                    const entry = document.getElementById(entryId);
                    if (entry) {
                        entry.innerHTML = '<span class="log-timestamp">[' + timestamp + ']</span><span class="log-content">' + message + '</span>';
                    }
                }

                function addCountdownEntry(entryId, timestamp, message) {
                    const container = document.getElementById('logContainer');
                    const entry = document.createElement('div');
                    entry.className = 'log-entry log-cultivation';
                    entry.id = entryId;
                    entry.innerHTML = '<span class="log-timestamp">[' + timestamp + ']</span><span class="log-content">' + message + '</span>';
                    container.appendChild(entry);
                    container.scrollTop = container.scrollHeight;
                }

                function removeCountdownEntry(entryId) {
                    const entry = document.getElementById(entryId);
                    if (entry) {
                        entry.remove();
                    }
                }
            </script>
        </body>
        </html>
        """

        self.log_display.setHtml(html_template)

    def add_initial_messages(self):
        """添加初始欢迎消息"""
        self.add_system_log("欢迎来到气运修仙世界！", "system")
        self.add_system_log("开始您的修仙之路吧！", "system")

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

        # 根据渲染方式更新显示
        if WEBENGINE_AVAILABLE and hasattr(self, 'log_display'):
            self.add_log_to_html(timestamp, message, log_type, color)
        else:
            self.update_log_display()

    def add_log_to_html(self, timestamp: str, message: str, log_type: str, color: str):
        """添加日志到HTML显示区域"""
        try:
            # 检查日志显示组件是否存在
            if not hasattr(self, 'log_display') or self.log_display is None:
                return

            # 转义HTML特殊字符
            import html
            safe_message = html.escape(str(message))

            # 执行JavaScript添加日志（异步调用）
            js_code = f"addLogEntry('{timestamp}', '{safe_message}', '{log_type}', '{color}');"
            # 使用异步JavaScript调用，避免阻塞UI线程
            self.log_display.page().runJavaScript(js_code, lambda result: None)

        except Exception as e:
            print(f"❌ 添加HTML日志失败: {e}")

    def add_cultivation_log(self, exp_gained: int, attribute_gained: int,
                          attribute_type: str, luck_effect: str):
        """添加修炼日志"""
        focus_info = CULTIVATION_FOCUS_TYPES.get(attribute_type, {})
        focus_name = focus_info.get('name', '未知')
        focus_icon = focus_info.get('icon', '❓')

        message = f"修炼{focus_name}{focus_icon} 获得修为+{exp_gained}, {focus_name}+{attribute_gained} [{luck_effect}]"
        self.add_log_entry(message, "cultivation", "#3498db")

    def add_cultivation_result_log(self, cultivation_result: Dict[str, Any]):
        """添加修炼结果日志（使用服务器返回的完整数据）"""
        if not cultivation_result.get('success'):
            return

        exp_gained = cultivation_result.get('exp_gained', 0)
        attribute_gained = cultivation_result.get('attribute_gained', 0)
        attribute_type = cultivation_result.get('attribute_type', 'HP')
        luck_effect = cultivation_result.get('luck_effect', '气运平')
        special_event_result = cultivation_result.get('special_event_result')

        focus_info = CULTIVATION_FOCUS_TYPES.get(attribute_type, {})
        focus_name = focus_info.get('name', '未知')
        focus_icon = focus_info.get('icon', '❓')

        # 检查是否有特殊事件
        if special_event_result and special_event_result.get('message'):
            # 有特殊事件，显示特殊事件信息
            event_message = special_event_result['message']
            is_positive = special_event_result.get('is_positive', True)

            if is_positive:
                # 正面事件，使用绿色
                self.add_log_entry(event_message, "special_event_positive", "#27ae60")
            else:
                # 负面事件，使用红色
                self.add_log_entry(event_message, "special_event_negative", "#e74c3c")

            # 如果还有基础修炼收益，也显示
            if exp_gained > 0 or attribute_gained > 0:
                base_message = f"基础修炼{focus_name}{focus_icon} 获得修为+{exp_gained}, {focus_name}+{attribute_gained} [{luck_effect}]"
                self.add_log_entry(base_message, "cultivation_result", "#3498db")
        else:
            # 没有特殊事件，显示正常修炼收益
            message = f"修炼{focus_name}{focus_icon} 获得修为+{exp_gained}, {focus_name}+{attribute_gained} [{luck_effect}]"
            self.add_log_entry(message, "cultivation_result", "#3498db")

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
        if log_type == "cultivation_switch":
            # 对于修炼方向切换日志，先移除之前的同类日志，然后添加新的
            self.remove_cultivation_switch_logs()

        self.add_log_entry(f"[系统] {message}", log_type, "#9b59b6")

    def remove_cultivation_switch_logs(self):
        """移除所有修炼方向切换日志"""
        if WEBENGINE_AVAILABLE and hasattr(self, 'log_display'):
            # 使用更具体的移除逻辑
            js_code = """
            // 查找所有包含"修炼方向已切换为"的日志条目
            const allEntries = document.querySelectorAll('.log-entry');
            const toRemove = [];

            allEntries.forEach(entry => {
                const content = entry.textContent || entry.innerText;
                if (content.includes('修炼方向已切换为')) {
                    toRemove.push(entry);
                }
            });

            console.log('找到', toRemove.length, '条修炼方向切换日志');
            toRemove.forEach(entry => {
                console.log('移除:', entry.textContent);
                entry.remove();
            });
            """
            # 使用异步JavaScript调用，避免阻塞UI线程
            self.log_display.page().runJavaScript(js_code, lambda result: None)



    def add_special_event_log(self, event_message: str):
        """添加特殊事件日志"""
        self.add_log_entry(f"✨ 特殊事件：{event_message}", "special", "#e67e22")

    def start_cultivation_countdown(self, cultivation_focus: str, next_cultivation_time: datetime):
        """开始修炼倒计时"""
        self.current_cultivation_focus = cultivation_focus
        self.next_cultivation_time = next_cultivation_time

        # 生成唯一的倒计时条目ID
        self.countdown_entry_id = f"countdown_{int(datetime.now().timestamp())}"

        # 添加初始倒计时条目
        self.update_countdown()

    def update_countdown(self):
        """更新倒计时显示"""
        print("🧪 DEBUG: update_countdown 方法开始执行")
        if not self.next_cultivation_time:
            print("🧪 DEBUG: next_cultivation_time 为空，返回")
            return

        current_time = datetime.now()
        time_diff = (self.next_cultivation_time - current_time).total_seconds()

        # 获取修炼方向信息
        focus_info = CULTIVATION_FOCUS_TYPES.get(self.current_cultivation_focus, {})
        focus_name = focus_info.get('name', '未知')

        if time_diff > 0:
            # 计算剩余时间
            minutes = int(time_diff // 60)
            seconds = int(time_diff % 60)

            message = f"正在进行[{focus_name}]，剩余时间{minutes}分{seconds:02d}秒..."
            timestamp = current_time.strftime("%H:%M:%S")

            # 在同一条记录上更新倒计时（异步JavaScript调用）
            if WEBENGINE_AVAILABLE and hasattr(self, 'log_display') and self.countdown_entry_id:
                # 检查条目是否存在，如果不存在则添加
                js_check = f"""
                if (document.getElementById('{self.countdown_entry_id}')) {{
                    updateCountdownEntry('{self.countdown_entry_id}', '{timestamp}', '{message}');
                }} else {{
                    addCountdownEntry('{self.countdown_entry_id}', '{timestamp}', '{message}');
                }}
                """
                # 使用异步JavaScript调用，避免阻塞UI线程
                self.log_display.page().runJavaScript(js_check, lambda result: None)
        else:
            # 倒计时结束，移除倒计时条目（异步JavaScript调用）
            if WEBENGINE_AVAILABLE and hasattr(self, 'log_display') and self.countdown_entry_id:
                js_remove = f"removeCountdownEntry('{self.countdown_entry_id}');"
                # 使用异步JavaScript调用，避免阻塞UI线程
                self.log_display.page().runJavaScript(js_remove, lambda result: None)

            self.countdown_entry_id = None
            self.next_cultivation_time = None

            # 触发修炼完成信号，让主窗口处理数据更新和下一轮修炼
            print("🧪 DEBUG: 修炼日志组件即将异步发送 cultivation_completed 信号")
            # 使用QTimer.singleShot确保信号在下一个事件循环中发送，避免同步阻塞
            QTimer.singleShot(0, lambda: self._emit_cultivation_completed())
            print("🧪 DEBUG: 修炼日志组件已安排异步发送 cultivation_completed 信号")

        print("🧪 DEBUG: update_countdown 方法执行完毕")

    def _emit_cultivation_completed(self):
        """异步发送修炼完成信号"""
        print("🧪 DEBUG: 真正发送 cultivation_completed 信号")
        self.cultivation_completed.emit()
        print("🧪 DEBUG: cultivation_completed 信号已发送")

    def stop_countdown(self):
        """停止当前倒计时"""
        if WEBENGINE_AVAILABLE and hasattr(self, 'log_display') and self.countdown_entry_id:
            js_remove = f"removeCountdownEntry('{self.countdown_entry_id}');"
            # 使用异步JavaScript调用，避免阻塞UI线程
            self.log_display.page().runJavaScript(js_remove, lambda result: None)

        self.countdown_entry_id = None
        self.next_cultivation_time = None

    def set_next_cultivation_time(self, next_time: datetime):
        """设置下次修炼时间"""
        self.next_cultivation_time = next_time

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

        # 根据渲染方式清空显示
        if WEBENGINE_AVAILABLE and hasattr(self, 'log_display'):
            # HTML版本清空（异步调用）
            # 使用异步JavaScript调用，避免阻塞UI线程
            self.log_display.page().runJavaScript("clearLog();", lambda result: None)
        else:
            # QTextEdit版本清空
            self.log_text_edit.clear()

        self.add_system_log("日志已清空")
        self.clear_log_requested.emit()

    def update_cultivation_status(self, cultivation_data: Dict[str, Any]):
        """更新修炼状态"""
        self.cultivation_status = cultivation_data

        # 检查修为变化
        current_exp = cultivation_data.get('current_exp', 0)
        current_realm = cultivation_data.get('current_realm', 0)

        # 检查修为变化（静默处理，不输出调试信息）
        if current_exp < self.last_exp and self.last_exp > 0:
            exp_lost = self.last_exp - current_exp
            print(f"⚠️ 修为减少: -{exp_lost} (从 {self.last_exp} 到 {current_exp}) - 可能触发了特殊事件或突破失败")

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
