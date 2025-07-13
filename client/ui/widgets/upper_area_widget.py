# 上半区域HTML组件 - 整合角色信息和功能菜单

from datetime import datetime
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from shared.constants import CULTIVATION_FOCUS_TYPES, LUCK_LEVELS
from shared.utils import get_realm_name, get_luck_level_name

# 尝试导入WebEngine，如果失败则使用备用方案
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class UpperAreaWidget(QWidget):
    """上半区域HTML组件 - 整合角色信息和功能菜单"""

    # 信号定义
    daily_sign_requested = pyqtSignal()  # 每日签到请求信号
    cultivation_focus_changed = pyqtSignal(str)  # 修炼方向变更信号
    function_selected = pyqtSignal(str)  # 功能选择信号

    def __init__(self):
        super().__init__()

        # 数据缓存
        self.character_data: Optional[Dict[str, Any]] = None
        self.cultivation_status: Optional[Dict[str, Any]] = None
        self.luck_info: Optional[Dict[str, Any]] = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        if WEBENGINE_AVAILABLE:
            self.create_html_area(main_layout)
        else:
            # 备用方案：创建简单的文本显示
            self.create_fallback_area(main_layout)

        self.setLayout(main_layout)

        # 延迟初始化数据
        if WEBENGINE_AVAILABLE:
            QTimer.singleShot(1000, self.init_default_data)  # 增加延迟时间

    def create_html_area(self, parent_layout: QVBoxLayout):
        """创建HTML版本的上半区域"""
        # 创建WebEngineView
        self.html_display = QWebEngineView()
        # 移除固定高度限制，让内容自适应

        # 禁用右键上下文菜单
        self.html_display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 设置样式
        self.html_display.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #f8f9fa;
            }
        """)

        # 设置初始HTML内容
        self.init_html()

        # 设置JavaScript事件监听
        self.setup_javascript_events()

        parent_layout.addWidget(self.html_display)

    def create_fallback_area(self, parent_layout: QVBoxLayout):
        """创建备用的简单显示区域"""
        from PyQt6.QtWidgets import QLabel
        
        fallback_label = QLabel("WebEngine不可用，请安装PyQt6-WebEngine")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        parent_layout.addWidget(fallback_label)

    def init_html(self):
        """初始化HTML页面"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>角色信息</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    font-size: 12px;
                    background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
                    color: #333;
                    line-height: 1.4;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }

                .container {
                    width: 100%;
                    min-height: 100%;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    padding: 8px;
                    box-sizing: border-box;
                }

                /* 角色信息区域 */
                .character-info {
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 12px;
                    flex: 1;
                }

                .character-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }

                .character-name {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                }

                .character-realm {
                    font-size: 14px;
                    font-weight: bold;
                    color: #27ae60;
                }

                .progress-section {
                    margin-bottom: 8px;
                }

                .progress-bar {
                    width: 100%;
                    height: 8px;
                    background-color: #e9ecef;
                    border-radius: 4px;
                    overflow: hidden;
                    margin: 4px 0;
                }

                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
                    transition: width 0.3s ease;
                }

                .progress-text {
                    font-size: 10px;
                    color: #6c757d;
                    text-align: center;
                }

                .cultivation-status {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                    font-size: 11px;
                }

                .cultivation-focus {
                    color: #495057;
                    font-weight: 600;
                }

                .cultivation-state {
                    color: #28a745;
                    font-weight: 600;
                }

                .resources-section {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 8px;
                    align-items: center;
                    margin-bottom: 8px;
                }

                .resource-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    font-size: 11px;
                }

                .resource-label {
                    color: #6c757d;
                    margin-bottom: 2px;
                }

                .resource-value {
                    color: #27ae60;
                    font-weight: bold;
                }

                .luck-display {
                    text-align: center;
                    font-size: 11px;
                    margin-bottom: 8px;
                }

                .daily-sign-btn {
                    width: 100%;
                    height: 28px;
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .daily-sign-btn:hover {
                    background: linear-gradient(135deg, #2980b9 0%, #21618c 100%);
                    transform: translateY(-1px);
                }

                .daily-sign-btn:disabled {
                    background: #bdc3c7;
                    color: #7f8c8d;
                    cursor: not-allowed;
                    transform: none;
                }

                /* 功能菜单区域 */
                .function-menu {
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 8px;
                    height: 60px;
                }

                .menu-buttons {
                    display: flex;
                    gap: 6px;
                    height: 100%;
                    align-items: center;
                }

                .menu-btn {
                    width: 44px;
                    height: 44px;
                    background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .menu-btn:hover {
                    background: linear-gradient(135deg, #e0e0e0 0%, #d0d0d0 100%);
                    border: 2px solid #007acc;
                    transform: translateY(-1px);
                }

                .menu-btn:active {
                    background: linear-gradient(135deg, #d0d0d0 0%, #c0c0c0 100%);
                    transform: translateY(0);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <!-- 角色信息区域 -->
                <div class="character-info">
                    <div class="character-header">
                        <span class="character-name" id="characterName">角色名称</span>
                        <span class="character-realm" id="characterRealm">凡人</span>
                    </div>
                    
                    <div class="progress-section">
                        <div class="progress-bar">
                            <div class="progress-fill" id="expProgressFill" style="width: 0%"></div>
                        </div>
                        <div class="progress-text" id="expProgressText">修为: 0 / 100 (0.0%)</div>
                    </div>
                    
                    <div class="cultivation-status">
                        <span class="cultivation-focus" id="cultivationFocus">修炼方向: 体修</span>
                        <span class="cultivation-state" id="cultivationState">修炼状态: 挂机中</span>
                    </div>
                    
                    <div class="resources-section">
                        <div class="resource-item">
                            <span class="resource-label">金币:</span>
                            <span class="resource-value" id="goldValue">0</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">灵石:</span>
                            <span class="resource-value" id="spiritStoneValue">0</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">气运:</span>
                            <span class="resource-value" id="luckValue">平 (50)</span>
                        </div>
                    </div>
                    
                    <button class="daily-sign-btn" id="dailySignBtn" onclick="dailySign()">每日签到</button>
                </div>
                
                <!-- 功能菜单区域 -->
                <div class="function-menu">
                    <div class="menu-buttons">
                        <button class="menu-btn" onclick="selectFunction('backpack')" title="查看背包物品">🎒</button>
                        <button class="menu-btn" onclick="selectFunction('cave')" title="进入洞府，可进行突破">🏠</button>
                        <button class="menu-btn" onclick="selectFunction('farm')" title="管理农场种植">🌱</button>
                        <button class="menu-btn" onclick="selectFunction('alchemy')" title="炼制丹药">⚗️</button>
                        <button class="menu-btn" onclick="selectFunction('dungeon')" title="挑战副本">⚔️</button>
                        <button class="menu-btn" onclick="selectFunction('worldboss')" title="挑战世界boss">👹</button>
                        <button class="menu-btn" onclick="selectFunction('shop')" title="购买物品">🏪</button>
                        <button class="menu-btn" id="channelBtn" onclick="selectFunction('channel')" title="聊天频道">💬</button>
                    </div>
                </div>
            </div>

            <script>
                function updateCharacterInfo(data) {
                    document.getElementById('characterName').textContent = data.name || '角色名称';
                    document.getElementById('characterRealm').textContent = data.realm || '凡人';
                    
                    // 更新修为进度
                    const progressPercent = data.expProgress || 0;
                    document.getElementById('expProgressFill').style.width = progressPercent + '%';
                    document.getElementById('expProgressText').textContent = data.expText || '修为: 0 / 100 (0.0%)';
                    
                    // 更新修炼状态
                    document.getElementById('cultivationFocus').textContent = '修炼方向: ' + (data.focusName || '体修');
                    document.getElementById('cultivationState').textContent = '修炼状态: ' + (data.cultivationState || '未修炼');
                    
                    // 更新资源
                    document.getElementById('goldValue').textContent = data.gold || '0';
                    document.getElementById('spiritStoneValue').textContent = data.spiritStone || '0';
                    document.getElementById('luckValue').textContent = data.luckDisplay || '平 (50)';
                    
                    // 更新签到按钮
                    const signBtn = document.getElementById('dailySignBtn');
                    if (data.canSignToday === false) {
                        signBtn.textContent = '已签到';
                        signBtn.disabled = true;
                    } else {
                        signBtn.textContent = '每日签到';
                        signBtn.disabled = false;
                    }
                }
                
                function dailySign() {
                    console.log('Daily sign button clicked');
                    // 使用自定义事件通知Python
                    document.dispatchEvent(new CustomEvent('dailySignRequested'));
                }

                function selectFunction(functionKey) {
                    console.log('Function selected:', functionKey);
                    // 使用自定义事件通知Python
                    document.dispatchEvent(new CustomEvent('functionSelected', {detail: functionKey}));
                }
                
                function updateChannelButton(icon, tooltip) {
                    const channelBtn = document.getElementById('channelBtn');
                    channelBtn.textContent = icon;
                    channelBtn.title = tooltip;
                }
            </script>
        </body>
        </html>
        """

        self.html_display.setHtml(html_template)

    def setup_javascript_events(self):
        """设置JavaScript事件监听"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        # 延迟设置事件监听，确保页面加载完成
        QTimer.singleShot(1500, self._setup_events)

    def _setup_events(self):
        """实际设置事件监听"""
        try:
            # 注入事件监听器
            js_code = """
            document.addEventListener('dailySignRequested', function() {
                console.log('Daily sign event received');
                // 这里需要通过其他方式通知Python，比如修改页面元素
                document.title = 'dailySign:' + Date.now();
            });

            document.addEventListener('functionSelected', function(event) {
                console.log('Function selected event received:', event.detail);
                // 通过修改页面标题来传递信息
                document.title = 'function:' + event.detail + ':' + Date.now();
            });
            """

            self.html_display.page().runJavaScript(js_code)

            # 监听页面标题变化
            self.html_display.page().titleChanged.connect(self.handle_title_change)

        except Exception as e:
            print(f"❌ 设置JavaScript事件失败: {e}")

    def handle_title_change(self, title: str):
        """处理页面标题变化（用于接收JavaScript事件）"""
        try:
            if title.startswith('dailySign:'):
                self.daily_sign_requested.emit()
            elif title.startswith('function:'):
                parts = title.split(':')
                if len(parts) >= 2:
                    function_key = parts[1]
                    self.function_selected.emit(function_key)
        except Exception as e:
            print(f"❌ 处理标题变化失败: {e}")

    def init_default_data(self):
        """初始化默认数据"""
        default_data = {
            'name': '角色名称',
            'realm': '凡人',
            'expProgress': 0,
            'expText': '修为: 0 / 100 (0.0%)',
            'focusName': '体修',
            'cultivationState': '未修炼',
            'gold': '0',
            'spiritStone': '0',
            'luckDisplay': '平 (50)',
            'canSignToday': True
        }
        self.update_character_display(default_data)

    def update_character_display(self, data: Dict[str, Any]):
        """更新角色信息显示"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        try:
            # 构建JavaScript调用
            js_data = {
                'name': str(data.get('name', '角色名称')),
                'realm': str(data.get('realm', '凡人')),
                'expProgress': float(data.get('expProgress', 0)),
                'expText': str(data.get('expText', '修为: 0 / 100 (0.0%)')),
                'focusName': str(data.get('focusName', '体修')),
                'cultivationState': str(data.get('cultivationState', '未修炼')),
                'gold': str(data.get('gold', '0')),
                'spiritStone': str(data.get('spiritStone', '0')),
                'luckDisplay': str(data.get('luckDisplay', '平 (50)')),
                'canSignToday': bool(data.get('canSignToday', True))
            }

            # 转换为JavaScript对象字符串
            js_object = "{"
            for key, value in js_data.items():
                if isinstance(value, str):
                    escaped_value = value.replace("'", "\\'")
                    js_object += f"'{key}': '{escaped_value}', "
                elif isinstance(value, bool):
                    js_object += f"'{key}': {'true' if value else 'false'}, "
                else:
                    js_object += f"'{key}': {value}, "
            js_object = js_object.rstrip(', ') + "}"

            # 执行JavaScript更新，先检查函数是否存在
            js_code = f"""
            if (typeof updateCharacterInfo === 'function') {{
                updateCharacterInfo({js_object});
            }} else {{
                console.log('updateCharacterInfo function not ready yet');
            }}
            """
            self.html_display.page().runJavaScript(js_code)

        except Exception as e:
            print(f"❌ 更新角色信息显示失败: {e}")

    def update_character_info(self, character_data: Dict[str, Any]):
        """更新角色信息"""
        self.character_data = character_data

        # 处理角色基本信息
        name = character_data.get('name', '未知角色')
        realm_level = character_data.get('cultivation_realm', 0)
        realm_name = get_realm_name(realm_level)

        # 处理修为进度
        current_exp = character_data.get('cultivation_exp', 0)
        exp_progress, exp_text = self.calculate_exp_progress(current_exp, realm_level)

        # 处理修炼方向
        focus_type = character_data.get('cultivation_focus', 'HP')
        focus_info = CULTIVATION_FOCUS_TYPES.get(focus_type, {})
        focus_name = focus_info.get('name', '体修')

        # 处理资源
        gold = character_data.get('gold', 0)
        spirit_stone = character_data.get('spirit_stone', 0)

        # 处理气运
        luck_value = character_data.get('luck_value', 50)
        luck_display = self.format_luck_display(luck_value)

        # 更新显示
        display_data = {
            'name': name,
            'realm': realm_name,
            'expProgress': exp_progress,
            'expText': exp_text,
            'focusName': focus_name,
            'cultivationState': '挂机中' if self.cultivation_status and self.cultivation_status.get('is_cultivating') else '未修炼',
            'gold': f"{gold:,}",
            'spiritStone': f"{spirit_stone:,}",
            'luckDisplay': luck_display,
            'canSignToday': self.luck_info.get('can_sign_today', True) if self.luck_info else True
        }

        self.update_character_display(display_data)

    def update_cultivation_status(self, cultivation_data: Dict[str, Any]):
        """更新修炼状态"""
        self.cultivation_status = cultivation_data

        # 如果有角色数据，重新更新显示
        if self.character_data:
            self.update_character_info(self.character_data)

    def update_luck_info(self, luck_data: Dict[str, Any]):
        """更新气运信息"""
        self.luck_info = luck_data

        # 如果有角色数据，重新更新显示
        if self.character_data:
            self.update_character_info(self.character_data)

    def calculate_exp_progress(self, current_exp: int, realm_level: int) -> tuple:
        """计算修为进度"""
        from shared.constants import CULTIVATION_EXP_REQUIREMENTS

        # 获取当前境界和下一境界的修为需求
        current_realm_exp = CULTIVATION_EXP_REQUIREMENTS.get(realm_level, 0)
        next_realm_exp = CULTIVATION_EXP_REQUIREMENTS.get(realm_level + 1, current_realm_exp + 1000)

        # 计算当前境界内的进度
        if next_realm_exp > current_realm_exp:
            progress_exp = current_exp - current_realm_exp
            required_exp = next_realm_exp - current_realm_exp
            progress_percent = (progress_exp / required_exp) * 100 if required_exp > 0 else 0
        else:
            progress_exp = 0
            required_exp = 1
            progress_percent = 100

        # 格式化进度文本
        exp_text = f"修为: {progress_exp:,} / {required_exp:,} ({progress_percent:.1f}%)"

        return progress_percent, exp_text

    def format_luck_display(self, luck_value: int) -> str:
        """格式化气运显示"""
        luck_level_name = get_luck_level_name(luck_value)
        return f"{luck_level_name} ({luck_value})"

    def update_channel_button(self, icon: str, tooltip: str):
        """更新频道按钮"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        try:
            js_code = f"updateChannelButton('{icon}', '{tooltip}');"
            self.html_display.page().runJavaScript(js_code)
        except Exception as e:
            print(f"❌ 更新频道按钮失败: {e}")

    def setup_javascript_bridge(self):
        """设置JavaScript桥接"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        # 注入JavaScript函数到页面
        js_bridge = """
        window.dailySignRequested = function() {
            console.log('Daily sign requested');
            // 这里会通过Qt的机制触发Python信号
        };

        window.functionSelected = function(functionKey) {
            console.log('Function selected:', functionKey);
            // 这里会通过Qt的机制触发Python信号
        };
        """

        try:
            self.html_display.page().runJavaScript(js_bridge)
        except Exception as e:
            print(f"❌ 设置JavaScript桥接失败: {e}")

    def handle_daily_sign_click(self):
        """处理每日签到点击"""
        self.daily_sign_requested.emit()

    def handle_function_click(self, function_key: str):
        """处理功能按钮点击"""
        self.function_selected.emit(function_key)

    def get_character_summary(self) -> Dict[str, Any]:
        """获取角色信息摘要"""
        if not self.character_data:
            return {}

        return {
            'name': self.character_data.get('name', ''),
            'realm': get_realm_name(self.character_data.get('cultivation_realm', 0)),
            'cultivation_exp': self.character_data.get('cultivation_exp', 0),
            'luck_value': self.character_data.get('luck_value', 50),
            'gold': self.character_data.get('gold', 0),
            'spirit_stone': self.character_data.get('spirit_stone', 0),
            'cultivation_focus': self.character_data.get('cultivation_focus', 'HP')
        }
