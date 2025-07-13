# 聊天频道组件

from typing import Optional, Dict, Any, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from client.network.websocket_client import websocket_manager
from client.state_manager import get_state_manager


class ChatChannelWidget(QWidget):
    """聊天频道组件"""
    
    # 信号定义
    new_message_received = pyqtSignal()  # 新消息接收信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.state_manager = get_state_manager()
        
        # 聊天相关属性
        self.chat_display = None
        self.chat_input = None
        self.chat_messages = []
        self.recent_sent_messages = []  # 存储最近发送的消息，用于去重
        
        # WebSocket客户端引用
        self.websocket_client = None
        if hasattr(parent, 'websocket_client'):
            self.websocket_client = parent.websocket_client
        
        try:
            self.init_ui()
            self.setup_websocket_callbacks()
            print("✅ 聊天组件初始化成功")
        except Exception as e:
            print(f"❌ 聊天组件初始化失败: {e}")
            import traceback
            traceback.print_exc()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setSpacing(0)  # 完全移除组件间距
        layout.setContentsMargins(5, 0, 5, 3)  # 移除上边距
        
        # 标题栏 - 极度紧凑
        self.create_title_bar(layout)
        
        # 聊天显示区域
        self.create_chat_display_area(layout)
        
        # 输入区域
        self.create_input_area(layout)
        
        self.setLayout(layout)

    def setVisible(self, visible):
        """重写setVisible方法，添加错误处理"""
        try:
            print(f"🔄 聊天组件设置可见性: {visible}")
            super().setVisible(visible)
        except Exception as e:
            print(f"❌ 聊天组件setVisible失败: {e}")
            import traceback
            traceback.print_exc()

    def create_title_bar(self, layout):
        """创建标题栏"""
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel("💬 聊天频道")
        title_font = QFont()
        title_font.setPointSize(10)  # 再次减小字体大小
        title_font.setBold(True)
        title_label.setFont(title_font)
        # 设置固定高度和移除所有内外边距
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
        layout.addLayout(title_layout)
    
    def create_chat_display_area(self, layout):
        """创建聊天显示区域"""
        # 检查WebEngine是否可用
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            self.create_html_chat_display(layout)
        except ImportError:
            print("⚠️ WebEngine不可用，使用QTextEdit聊天界面")
            self.create_textedit_chat_display(layout)
    
    def create_html_chat_display(self, layout):
        """创建基于HTML的聊天显示区域"""
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        
        # 聊天显示区域 - 使用HTML渲染，添加边框
        self.chat_display = QWebEngineView()
        self.chat_display.setMinimumHeight(380)
        
        # 禁用右键上下文菜单
        self.chat_display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        # 为聊天区域添加边框样式
        self.chat_display.setStyleSheet("""
            QWebEngineView {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        # 初始化聊天消息列表
        self.chat_messages = []
        
        # 设置初始HTML内容
        self.init_chat_html()
        
        # 延迟添加欢迎消息，等待HTML加载完成
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.add_welcome_message)
        
        layout.addWidget(self.chat_display)
    
    def create_textedit_chat_display(self, layout):
        """创建基于QTextEdit的聊天显示区域（WebEngine不可用时的回退方案）"""
        from PyQt6.QtWidgets import QTextEdit
        
        self.chat_display = QTextEdit()
        self.chat_display.setMinimumHeight(465)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
        """)
        
        # 添加欢迎消息
        self.chat_display.append("💬 欢迎进入聊天频道，祝您修炼愉快！")
        
        layout.addWidget(self.chat_display)
    
    def create_input_area(self, layout):
        """创建输入区域"""
        # 输入区域 - 更紧凑的布局
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)  # 减少输入框和按钮之间的间距
        input_layout.setContentsMargins(0, 2, 0, 0)  # 减少输入区域的边距
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("💬 输入聊天内容...")
        self.chat_input.setMinimumHeight(32)  # 减少输入框高度
        self.chat_input.setMaximumHeight(32)  # 限制最大高度
        self.chat_input.returnPressed.connect(self.send_chat_message)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e1e5e9;
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 12px;
                font-family: "Microsoft YaHei";
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background: white;
            }
            QLineEdit:hover {
                border: 2px solid #adb5bd;
            }
        """)
        input_layout.addWidget(self.chat_input)
        
        send_button = QPushButton("📤 发送")
        send_button.setMinimumHeight(32)  # 与输入框高度匹配
        send_button.setMaximumHeight(32)
        send_button.setMaximumWidth(75)  # 稍微减小宽度
        send_button.clicked.connect(self.send_chat_message)
        send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: "Microsoft YaHei";
                padding: 0 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
            QPushButton:pressed {
                background: #004085;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
        """)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
    
    def setup_websocket_callbacks(self):
        """设置WebSocket回调"""
        try:
            if self.websocket_client:
                # 注册消息回调
                self.websocket_client.register_message_callback("chat", self.on_chat_message)
                self.websocket_client.register_message_callback("system", self.on_system_message)
                self.websocket_client.register_message_callback("history", self.on_history_message)
                print("✅ WebSocket回调注册成功")
            else:
                print("⚠️ WebSocket客户端不存在，跳过回调注册")
        except Exception as e:
            print(f"❌ WebSocket回调注册失败: {e}")
            import traceback
            traceback.print_exc()
    
    def init_chat_html(self):
        """初始化聊天HTML页面"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>聊天频道</title>
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
                    line-height: 1.0;
                    overflow-x: hidden;
                }

                .chat-container {
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

                .welcome-message {
                    text-align: center;
                    margin: 0;
                    padding: 2px 4px;
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                    border-radius: 6px;
                    border: 1px solid #90caf9;
                    font-size: 10px;
                    color: #1565c0;
                    font-weight: normal;
                    display: none;
                }

                .message {
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    word-wrap: break-word;
                    clear: both;
                    line-height: 1.0;
                }

                .message-left {
                    text-align: left;
                    float: left;
                    clear: both;
                    margin: 0;
                }

                .message-right {
                    text-align: right;
                    float: right;
                    clear: both;
                    margin: 0;
                }

                .message-center {
                    text-align: center;
                    clear: both;
                    margin: 0;
                }

                .message-header {
                    font-size: 14px;
                    font-weight: 600;
                    margin: 0;
                    padding: 0;
                    line-height: 1.0;
                }

                .message-content {
                    font-size: 14px;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    line-height: 1.0;
                }

                .system-message {
                    color: #e65100;
                    font-weight: 600;
                    background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
                    padding: 2px 6px;
                    border-radius: 6px;
                    border: 1px solid #ffcc02;
                    display: inline-block;
                    margin: 0;
                    font-size: 12px;
                    line-height: 1.0;
                }

                .world-channel {
                    color: #007bff;
                }

                .clearfix::after {
                    content: "";
                    display: table;
                    clear: both;
                }
            </style>
        </head>
        <body>
            <div class="chat-container" id="chatContainer">
                <!-- 动态添加消息，不要硬编码 -->
            </div>

            <script>
                function addMessage(html) {
                    const container = document.getElementById('chatContainer');
                    container.insertAdjacentHTML('beforeend', html);
                    container.scrollTop = container.scrollHeight;
                }

                function clearMessages() {
                    const container = document.getElementById('chatContainer');
                    container.innerHTML = '';
                }
            </script>
        </body>
        </html>
        """
        
        if hasattr(self.chat_display, 'setHtml'):
            self.chat_display.setHtml(html_template)
    
    def add_welcome_message(self):
        """添加带当前时间的欢迎消息"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            welcome_msg = self.create_system_message_html("欢迎进入聊天频道，祝您修炼愉快！", current_time)
            self.add_message_to_chat_display(welcome_msg)
        except Exception as e:
            print(f"❌ 添加欢迎消息失败: {e}")
    
    def send_chat_message(self):
        """发送聊天消息"""
        if not hasattr(self, 'chat_input') or not self.chat_input:
            return
        
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # 清空输入框
        self.chat_input.clear()
        
        # 立即显示自己的消息（乐观更新）
        self.add_local_chat_message(message)
        
        # 通过WebSocket发送消息
        if self.websocket_client and self.websocket_client.is_connected:
            success = self.websocket_client.send_chat_message(message, "WORLD")
            if success:
                print(f"💬 通过WebSocket发送聊天消息: {message}")
            else:
                print("❌ WebSocket发送消息失败")
        else:
            print("⚠️ WebSocket未连接，消息仅本地显示")

    def add_local_chat_message(self, message: str):
        """添加本地聊天消息（用于WebSocket未连接时的回退）"""
        # 获取当前时间
        current_time = datetime.now().strftime("%H:%M")

        # 获取用户名
        username = "我"
        if self.state_manager.user_info:
            username = self.state_manager.user_info.get('username', '我')

        # 转义HTML特殊字符
        import html
        safe_message = html.escape(str(message))
        safe_username = html.escape(str(username))

        # 记录发送的消息用于去重
        message_key = f"{safe_message}_{current_time}"
        self.recent_sent_messages.append(message_key)

        # 只保留最近10条消息记录
        if len(self.recent_sent_messages) > 10:
            self.recent_sent_messages.pop(0)

        # 创建自己的消息（右对齐）
        new_message = self.create_chat_message_html(
            "WORLD", safe_username, safe_message, current_time, is_own_message=True
        )

        self.add_message_to_chat_display(new_message)

    def on_chat_message(self, message_data: dict):
        """处理聊天消息"""
        try:
            if not isinstance(message_data, dict):
                print(f"⚠️ 无效的消息数据类型: {type(message_data)}")
                return

            channel = message_data.get("channel", "WORLD")
            character_name = message_data.get("character_name", "Unknown")
            content = message_data.get("content", "")
            timestamp = message_data.get("timestamp", "")
            character_id = message_data.get("character_id", 0)

            # 验证必要字段
            if not content:
                print("⚠️ 消息内容为空，跳过处理")
                return

            # 格式化时间
            try:
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                else:
                    time_str = datetime.now().strftime("%H:%M")
            except Exception as time_error:
                print(f"⚠️ 时间格式化失败: {time_error}")
                time_str = datetime.now().strftime("%H:%M")

            # 判断是否是自己发送的消息
            is_own_message = False
            if hasattr(self, 'state_manager') and self.state_manager.current_character:
                current_character_id = self.state_manager.current_character.get('id', 0)
                is_own_message = (character_id == current_character_id)

            # 转义HTML特殊字符
            import html
            safe_content = html.escape(str(content))
            safe_character_name = html.escape(str(character_name))

            # 如果是自己的消息，检查是否已经显示过（去重）
            if is_own_message:
                message_key = f"{safe_content}_{time_str}"
                if hasattr(self, 'recent_sent_messages') and message_key in self.recent_sent_messages:
                    print(f"⚠️ 跳过重复消息: {content}")
                    return

            # 创建消息HTML
            new_message = self.create_chat_message_html(
                channel, safe_character_name, safe_content, time_str, is_own_message
            )

            self.add_message_to_chat_display(new_message)

            # 如果不是自己的消息，发送新消息信号
            if not is_own_message:
                self.new_message_received.emit()

        except Exception as e:
            print(f"❌ 处理聊天消息失败: {e}")
            import traceback
            traceback.print_exc()

    def on_system_message(self, message_data: dict):
        """处理系统消息"""
        try:
            if not isinstance(message_data, dict):
                print(f"⚠️ 无效的系统消息数据类型: {type(message_data)}")
                return

            content = message_data.get("content", "")
            timestamp = message_data.get("timestamp", "")

            # 验证必要字段
            if not content:
                print("⚠️ 系统消息内容为空，跳过处理")
                return

            # 格式化时间
            try:
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                else:
                    time_str = datetime.now().strftime("%H:%M")
            except Exception as time_error:
                print(f"⚠️ 时间格式化失败: {time_error}")
                time_str = datetime.now().strftime("%H:%M")

            # 转义HTML特殊字符
            import html
            safe_content = html.escape(str(content))

            # 创建系统消息HTML（居中显示）
            new_message = self.create_system_message_html(safe_content, time_str)

            self.add_message_to_chat_display(new_message)

        except Exception as e:
            print(f"❌ 处理系统消息失败: {e}")
            import traceback
            traceback.print_exc()

    def on_history_message(self, message_data: dict):
        """处理历史消息"""
        try:
            messages = message_data.get("messages", [])
            channel = message_data.get("channel", "WORLD")

            print(f"📜 收到历史消息: {len(messages)} 条")

            # 清空当前聊天显示
            if hasattr(self, 'chat_display') and hasattr(self.chat_display, 'clear'):
                self.chat_display.clear()
                # 重新初始化HTML
                self.init_chat_html()

            # 按时间顺序显示历史消息
            for msg in messages:
                try:
                    message_type = msg.get("type", "CHAT")
                    content = msg.get("content", "")
                    character_name = msg.get("character_name", "Unknown")
                    timestamp = msg.get("timestamp", "")
                    character_id = msg.get("character_id", 0)

                    # 格式化时间
                    try:
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime("%H:%M")
                        else:
                            time_str = datetime.now().strftime("%H:%M")
                    except Exception:
                        time_str = datetime.now().strftime("%H:%M")

                    # 转义HTML特殊字符
                    import html
                    safe_content = html.escape(str(content))
                    safe_character_name = html.escape(str(character_name))

                    # 根据消息类型创建不同样式的消息
                    if message_type == "SYSTEM":
                        new_message = self.create_system_message_html(safe_content, time_str)
                    else:
                        # 判断是否是自己发送的消息
                        is_own_message = False
                        if hasattr(self, 'state_manager') and self.state_manager.current_character:
                            current_character_id = self.state_manager.current_character.get('id', 0)
                            is_own_message = (character_id == current_character_id)

                        new_message = self.create_chat_message_html(
                            channel, safe_character_name, safe_content, time_str, is_own_message
                        )

                    self.add_message_to_chat_display(new_message)

                except Exception as msg_error:
                    print(f"⚠️ 处理单条历史消息失败: {msg_error}")
                    continue

        except Exception as e:
            print(f"❌ 处理历史消息失败: {e}")

    def create_chat_message_html(self, channel: str, character_name: str, content: str, time_str: str, is_own_message: bool = False):
        """创建聊天消息HTML - 适用于WebEngine渲染"""
        try:
            # 根据频道设置颜色类
            channel_class = "world-channel" if channel == "WORLD" else "other-channel"

            # 根据是否是自己的消息设置对齐方式
            alignment_class = "message-right" if is_own_message else "message-left"

            # 创建消息HTML
            message_html = f"""
            <div class="message {alignment_class} clearfix" style="margin: 0 0 8px 0; padding: 0; line-height: 12px;">
                <div style="display: inline-block; margin: 0; padding: 0; line-height: 12px;">
                    <div class="message-header {channel_class}" style="font-size: 12px; font-weight: 600; margin: 0; padding: 0; line-height: 12px;">
                        <span style="color: #007bff; margin-right: 4px;">[{channel}]</span>
                        <span style="color: #2c3e50; margin-right: 4px;">{character_name}</span>
                        <span style="color: #8d6e63; font-size: 10px;">[{time_str}]</span>
                    </div>
                    <div class="message-content" style="font-size: 12px; margin: 0; padding: 0; color: #333; line-height: 12px;">{content}</div>
                </div>
            </div>
            """

            return message_html

        except Exception as e:
            print(f"❌ 创建聊天消息HTML失败: {e}")
            return ""

    def create_system_message_html(self, content: str, time_str: str):
        """创建系统消息HTML - 适用于WebEngine渲染"""
        try:
            # 系统消息：统一12px字体，固定行高，增加底部间距
            message_html = f"""
            <div style="text-align: center; margin: 0 0 8px 0; padding: 0; line-height: 12px;">
                <span style="
                    color: #e65100;
                    font-weight: 600;
                    background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
                    padding: 2px 6px;
                    border-radius: 6px;
                    border: 1px solid #ffcc02;
                    display: inline-block;
                    margin: 0;
                    font-size: 12px;
                    line-height: 12px;
                ">{content}</span>
                <span style="color: #8d6e63; margin: 0 6px; font-size: 10px;">[{time_str}]</span>
            </div>
            """

            return message_html

        except Exception as e:
            print(f"❌ 创建系统消息HTML失败: {e}")
            return ""

    def add_message_to_chat_display(self, message_html: str):
        """添加消息到HTML聊天显示区域"""
        try:
            # 检查聊天显示组件是否存在
            if not hasattr(self, 'chat_display') or self.chat_display is None:
                print("⚠️ 聊天显示组件不存在，跳过消息添加")
                return

            # 检查消息内容
            if not message_html or not isinstance(message_html, str):
                print("⚠️ 无效的消息HTML内容")
                return

            # 如果是HTML版本，使用JavaScript添加消息
            if hasattr(self.chat_display, 'page'):
                try:
                    page = self.chat_display.page()
                    if page is None:
                        print("⚠️ WebEngine页面不存在，跳过消息添加")
                        return

                    # 转义JavaScript字符串中的特殊字符
                    escaped_html = message_html.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')

                    # 执行JavaScript添加消息
                    js_code = f"addMessage('{escaped_html}');"
                    page.runJavaScript(js_code)
                except Exception as js_error:
                    print(f"❌ JavaScript执行失败: {js_error}")
                    # 回退到简单的文本显示
                    import re
                    text_content = re.sub('<[^<]+?>', '', message_html)
                    print(f"📝 回退显示文本: {text_content}")
            else:
                # QTextEdit版本的回退处理
                if hasattr(self.chat_display, 'append'):
                    # 简单的文本版本，去除HTML标签
                    import re
                    text_content = re.sub('<[^<]+?>', '', message_html)
                    self.chat_display.append(text_content)

        except Exception as e:
            print(f"❌ 添加消息到聊天显示失败: {e}")
            import traceback
            traceback.print_exc()

    def clear_messages(self):
        """清空聊天消息"""
        try:
            if hasattr(self.chat_display, 'page'):
                # HTML版本
                self.chat_display.page().runJavaScript("clearMessages();")
            elif hasattr(self.chat_display, 'clear'):
                # QTextEdit版本
                self.chat_display.clear()
        except Exception as e:
            print(f"❌ 清空聊天消息失败: {e}")

    def show_new_message_indicator(self):
        """显示新消息提示"""
        try:
            # 发送新消息信号
            self.new_message_received.emit()
            print("🔔 新消息提示：有新的聊天消息，请点击'频道'按钮查看")
        except Exception as e:
            print(f"❌ 显示新消息提示失败: {e}")

    def clear_new_message_indicator(self):
        """清除新消息提示"""
        try:
            print("🔔 新消息提示已清除")
        except Exception as e:
            print(f"❌ 清除新消息提示失败: {e}")
