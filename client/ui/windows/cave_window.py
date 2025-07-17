# 洞府窗口

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from typing import Dict, Any, Optional

from client.network.api_client import GameAPIClient

# 检查WebEngine可用性
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("⚠️ PyQt6-WebEngine不可用，洞府界面将使用备用方案")


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

        # 连接状态管理器的信号，实时同步数据
        self.state_manager.user_data_updated.connect(self.on_user_data_updated)

        self.cave_data = {}
        self.html_loaded = False
        self.setup_ui()
        self.load_cave_info()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("洞府")
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
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        if WEBENGINE_AVAILABLE:
            self.create_html_cave_display(main_layout)
        else:
            self.create_fallback_display(main_layout)

        self.setLayout(main_layout)

    def create_html_cave_display(self, layout):
        """创建基于HTML的洞府显示区域"""
        # 洞府显示区域 - 使用HTML渲染
        self.cave_display = QWebEngineView()

        # 禁用右键上下文菜单
        self.cave_display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 为洞府区域添加边框样式
        self.cave_display.setStyleSheet("""
            QWebEngineView {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)

        # 设置初始HTML内容
        self.init_cave_html()

        # 监听页面加载完成事件
        self.cave_display.loadFinished.connect(self.on_html_load_finished)

        layout.addWidget(self.cave_display)

    def create_fallback_display(self, layout):
        """创建备用的简单显示区域"""
        from PyQt6.QtWidgets import QLabel

        fallback_label = QLabel("WebEngine不可用，请安装PyQt6-WebEngine")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        layout.addWidget(fallback_label)

    def get_breakthrough_image_base64(self):
        """获取突破图片的base64数据"""
        try:
            import os
            import base64

            # 获取图片路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            image_path = os.path.join(project_root, "client", "assets", "images", "cave", "Breakthrough.png")

            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    return encoded_string
            else:
                print(f"⚠️ 突破图片不存在: {image_path}")
                return ""
        except Exception as e:
            print(f"❌ 获取突破图片失败: {e}")
            return ""

    def init_cave_html(self):
        """初始化洞府HTML页面"""
        # 获取图片的base64数据
        breakthrough_image_data = self.get_breakthrough_image_base64()

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>洞府管理</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    font-size: 14px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                    line-height: 1.4;
                    overflow: hidden;
                    height: 100vh;
                    margin: 0;
                    padding: 0;
                }}

                .cave-container {{
                    width: 100%;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    box-sizing: border-box;
                }}

                .cave-header {{
                    text-align: center;
                    padding: 20px 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }}

                .cave-title-row {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%;
                    position: relative;
                }}

                .cave-title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #ffffff;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                    letter-spacing: 2px;
                }}

                .character-info {{
                    position: absolute;
                    right: 20px;
                    display: flex;
                    gap: 15px;
                    font-size: 12px;
                    color: #ffffff;
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
                }}

                .character-info span {{
                    font-size: 12px;
                    font-weight: bold;
                }}

                .cave-main {{
                    flex: 1;
                    display: flex;
                    position: relative;
                    padding: 20px;
                    gap: 20px;
                }}

                .cave-left {{
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    backdrop-filter: blur(10px);
                }}

                .cave-right {{
                    width: 320px;
                    min-width: 320px;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 20px;
                    padding: 25px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    backdrop-filter: blur(10px);
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }}

                .breakthrough-image {{
                    width: 400px;
                    height: 500px;
                    max-width: 100%;
                    max-height: 50vh;
                    object-fit: contain;
                    margin-bottom: 30px;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    transition: transform 0.3s ease;
                }}

                .breakthrough-image:hover {{
                    transform: scale(1.02);
                }}

                .progress-container {{
                    width: 100%;
                    max-width: 500px;
                    margin-bottom: 30px;
                }}

                .progress-label {{
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: bold;
                    color: #4a5568;
                }}

                .progress-bar {{
                    width: 100%;
                    height: 35px;
                    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
                    position: relative;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }}

                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
                    border-radius: 18px;
                    position: relative;
                    overflow: hidden;
                }}

                .progress-fill::after {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
                    animation: shimmer 2s infinite;
                }}

                @keyframes shimmer {{
                    0% {{ transform: translateX(-100%); }}
                    100% {{ transform: translateX(100%); }}
                }}

                .progress-text {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #2d3748;
                    font-weight: bold;
                    font-size: 14px;
                    text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
                    z-index: 10;
                }}

                .breakthrough-button {{
                    padding: 15px 40px;
                    font-size: 18px;
                    font-weight: bold;
                    color: #ffffff;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    border-radius: 25px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}

                .breakthrough-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
                    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                }}

                .breakthrough-button:active {{
                    transform: translateY(0);
                }}

                .breakthrough-button:disabled {{
                    background: linear-gradient(135deg, #a0a0a0 0%, #808080 100%);
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }}

                .function-card {{
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    backdrop-filter: blur(10px);
                    transition: all 0.3s ease;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}

                .function-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
                }}

                .function-header {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    min-height: 32px;
                }}

                .function-label {{
                    font-size: 15px;
                    font-weight: bold;
                    color: #2d3748;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex: 1;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}

                .function-icon {{
                    font-size: 20px;
                }}

                .function-button {{
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: bold;
                    color: #ffffff;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    border-radius: 16px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                    min-width: 60px;
                    white-space: nowrap;
                    flex-shrink: 0;
                }}

                .function-button:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                }}

                .function-button:disabled {{
                    background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }}

                .function-status {{
                    font-size: 13px;
                    margin-top: 8px;
                    padding: 5px 10px;
                    border-radius: 10px;
                    text-align: center;
                    font-weight: 500;
                }}

                .status-available {{
                    background: rgba(72, 187, 120, 0.1);
                    color: #38a169;
                    border: 1px solid rgba(72, 187, 120, 0.2);
                }}

                .status-locked {{
                    background: rgba(245, 101, 101, 0.1);
                    color: #e53e3e;
                    border: 1px solid rgba(245, 101, 101, 0.2);
                }}

                .status-max-level {{
                    background: rgba(237, 137, 54, 0.1);
                    color: #dd6b20;
                    border: 1px solid rgba(237, 137, 54, 0.2);
                }}

                .function-benefit {{
                    font-size: 12px;
                    margin-top: 8px;
                    padding: 5px 10px;
                    border-radius: 10px;
                    text-align: center;
                    font-weight: 500;
                    background: rgba(59, 130, 246, 0.1);
                    color: #3b82f6;
                    border: 1px solid rgba(59, 130, 246, 0.2);
                }}
            </style>
        </head>
        <body>
            <div class="cave-container">
                <div class="cave-header">
                    <div class="cave-title-row">
                        <div class="cave-title">洞府</div>
                        <div class="character-info">
                            <span id="characterRealm">境界：练气初期</span>
                            <span id="characterSpiritualRoot">灵根：单灵根</span>
                        </div>
                    </div>
                </div>

                <div class="cave-main">
                    <div class="cave-left">
                        <img src="data:image/png;base64,{breakthrough_image_data}"
                             alt="突破修炼"
                             class="breakthrough-image"
                             id="breakthroughImage">

                        <div class="progress-container">
                            <div class="progress-label">修为进度</div>
                            <div class="progress-bar">
                                <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                                <div class="progress-text" id="progressText">0/0</div>
                            </div>
                        </div>

                        <button class="breakthrough-button" id="breakthroughBtn" onclick="performBreakthrough()">
                            🌟 境界突破
                        </button>
                    </div>

                    <div class="cave-right">
                        <div class="function-card">
                            <div class="function-header">
                                <div class="function-label">
                                    <span class="function-icon">🏗️</span>
                                    <span id="caveLevelLabel">洞府: 1级</span>
                                </div>
                                <button class="function-button" id="caveUpgradeBtn" onclick="upgradeCave()">升级</button>
                            </div>
                            <div class="function-status status-available" id="caveUpgradeStatus">升级费用: 1000灵石</div>
                            <div class="function-benefit" id="caveUpgradeBenefit">下一级效益: 减少突破失败修为损失5%</div>
                        </div>

                        <div class="function-card">
                            <div class="function-header">
                                <div class="function-label">
                                    <span class="function-icon">⚡</span>
                                    <span id="spiritArrayLabel">聚灵阵: 0级</span>
                                </div>
                                <button class="function-button" id="spiritArrayBtn" onclick="upgradeSpiritArray()">未解锁</button>
                            </div>
                            <div class="function-status status-locked" id="spiritArrayStatus">需要2级洞府解锁</div>
                            <div class="function-benefit" id="spiritArrayBenefit">下一级效益: 修炼速度+20%</div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // 全局变量
                let caveData = {{}};

                // 更新洞府信息显示
                function updateCaveInfo(data) {{
                    caveData = data;

                    // 更新角色信息
                    updateCharacterInfo();

                    // 更新洞府等级显示
                    updateCaveLevel();

                    // 更新聚灵阵显示
                    updateSpiritArray();

                    // 更新修为进度条
                    updateCultivationProgress();
                }}

                function updateCharacterInfo() {{
                    // 更新境界信息
                    const realmElement = document.getElementById('characterRealm');
                    if (realmElement) {{
                        const realmNames = [
                            '凡人', '练气初期', '练气中期', '练气后期', '练气大圆满',
                            '筑基初期', '筑基中期', '筑基后期', '筑基大圆满',
                            '金丹初期', '金丹中期', '金丹后期', '金丹大圆满',
                            '元婴初期', '元婴中期', '元婴后期', '元婴大圆满'
                        ];
                        const realmLevel = caveData.cultivation_realm || 0;
                        const realmName = realmNames[realmLevel] || `未知境界(${{realmLevel}})`;
                        realmElement.textContent = `境界：${{realmName}}`;
                    }}

                    // 更新灵根信息
                    const spiritualRootElement = document.getElementById('characterSpiritualRoot');
                    if (spiritualRootElement) {{
                        const spiritualRoot = caveData.spiritual_root || '单灵根';
                        // 根据灵根类型设置颜色
                        const rootColors = {{
                            '天灵根': '#FFD700',
                            '变异灵根': '#8A2BE2',
                            '单灵根': '#32CD32',
                            '双灵根': '#4169E1',
                            '三灵根': '#C0C0C0',
                            '四灵根': '#A0522D',
                            '五灵根': '#696969',
                            '废灵根': '#8B4513'
                        }};
                        const rootColor = rootColors[spiritualRoot] || '#FFFFFF';
                        spiritualRootElement.innerHTML = `灵根：<span style="color: ${{rootColor}}; font-weight: bold;">${{spiritualRoot}}</span>`;
                    }}
                }}

                function updateCaveLevel() {{
                    const caveLevel = caveData.cave_level || 1;
                    const maxLevel = caveData.max_cave_level || 10;
                    const upgradeCost = caveData.cave_upgrade_cost || {{}};

                    document.getElementById('caveLevelLabel').textContent = `洞府: ${{caveLevel}}级`;

                    const statusEl = document.getElementById('caveUpgradeStatus');
                    const btnEl = document.getElementById('caveUpgradeBtn');
                    const benefitEl = document.getElementById('caveUpgradeBenefit');

                    if (caveLevel >= maxLevel) {{
                        statusEl.textContent = '已达最高等级';
                        statusEl.className = 'function-status status-max-level';
                        btnEl.disabled = true;
                        btnEl.textContent = '已满级';
                        benefitEl.textContent = '已达最高等级';
                    }} else {{
                        const cost = upgradeCost.spirit_stone || (caveLevel * 1000);
                        statusEl.textContent = `升级费用: ${{cost}}灵石`;
                        statusEl.className = 'function-status status-available';
                        btnEl.disabled = false;
                        btnEl.textContent = '升级';

                        // 显示下一级效益
                        const nextLevel = caveLevel + 1;
                        const reductionPercent = nextLevel * 1; // 每级减少1%修为损失
                        const goldMin = nextLevel * 2;
                        const goldMax = nextLevel * 6;
                        benefitEl.textContent = `下一级效益: 减少修为损失${{reductionPercent}}%, ${{goldMin}}-${{goldMax}}金币/周期`;
                    }}
                }}

                function updateSpiritArray() {{
                    const spiritLevel = caveData.spirit_gathering_array_level || 0;
                    const maxLevel = caveData.max_spirit_array_level || 5;
                    const caveLevel = caveData.cave_level || 1;
                    const upgradeCost = caveData.spirit_array_upgrade_cost || {{}};

                    document.getElementById('spiritArrayLabel').textContent = `聚灵阵: ${{spiritLevel}}级`;

                    const statusEl = document.getElementById('spiritArrayStatus');
                    const btnEl = document.getElementById('spiritArrayBtn');
                    const benefitEl = document.getElementById('spiritArrayBenefit');

                    if (caveLevel < 2) {{
                        statusEl.textContent = '需要2级洞府解锁';
                        statusEl.className = 'function-status status-locked';
                        btnEl.disabled = true;
                        btnEl.textContent = '未解锁';
                        benefitEl.textContent = '下一级效益: 减少修炼间隔5%, 1-3灵石/周期';
                    }} else if (spiritLevel >= maxLevel) {{
                        statusEl.textContent = '已达最高等级';
                        statusEl.className = 'function-status status-max-level';
                        btnEl.disabled = true;
                        btnEl.textContent = '已满级';
                        benefitEl.textContent = '已达最高等级';
                    }} else {{
                        const cost = upgradeCost.spirit_stone || ((spiritLevel + 1) * 500);
                        statusEl.textContent = `升级费用: ${{cost}}灵石`;
                        statusEl.className = 'function-status status-available';
                        btnEl.disabled = false;
                        btnEl.textContent = '升级';

                        // 显示下一级效益
                        const nextLevel = spiritLevel + 1;
                        const speedReduction = nextLevel * 5; // 每级减少5%修炼间隔
                        const stoneMin = nextLevel * 1;
                        const stoneMax = nextLevel * 3;
                        benefitEl.textContent = `下一级效益: 减少修炼间隔${{speedReduction}}%, ${{stoneMin}}-${{stoneMax}}灵石/周期`;
                    }}
                }}

                function updateCultivationProgress() {{
                    // 使用与主界面相同的修为进度计算方式
                    const currentExp = caveData.cultivation_exp || 0;
                    const currentRealm = caveData.cultivation_realm || 0;

                    // 修为需求表（与主界面保持一致）
                    const expRequirements = {{
                        0: 0, 1: 100, 2: 250, 3: 450, 4: 700,
                        5: 1000, 6: 1400, 7: 1900, 8: 2500,
                        9: 3200, 10: 4000, 11: 4900, 12: 5900,
                        13: 7000, 14: 8200, 15: 9500, 16: 10900,
                        17: 12400, 18: 14000, 19: 15700, 20: 17500,
                        21: 19400, 22: 21400, 23: 23500, 24: 25700,
                        25: 28000, 26: 30400, 27: 32900, 28: 35500,
                        29: 38200, 30: 41000, 31: 43900, 32: 46900,
                        33: 50000
                    }};

                    // 获取下一境界的突破需求
                    const nextRealmExp = expRequirements[currentRealm + 1] || 50000;

                    // 计算进度百分比
                    const progressPercent = nextRealmExp > 0 ? (currentExp / nextRealmExp) * 100 : 100;

                    // 更新进度条
                    document.getElementById('progressFill').style.width = Math.max(0, Math.min(100, progressPercent)) + '%';
                    document.getElementById('progressText').textContent = `${{currentExp}}/${{nextRealmExp}}`;

                    // 根据进度更新突破按钮状态
                    const breakthroughBtn = document.getElementById('breakthroughBtn');
                    const canBreakthrough = currentExp >= nextRealmExp;

                    if (canBreakthrough) {{
                        breakthroughBtn.disabled = false;
                        breakthroughBtn.textContent = '🌟 境界突破';
                        breakthroughBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    }} else {{
                        breakthroughBtn.disabled = false; // 始终可点击查看状态
                        breakthroughBtn.textContent = '🌟 境界突破';
                        breakthroughBtn.style.background = 'linear-gradient(135deg, #a0a0a0 0%, #808080 100%)';
                    }}
                }}

                // 功能按钮点击事件
                function performBreakthrough() {{
                    if (window.pyqtSignal) {{
                        window.pyqtSignal('breakthrough_requested');
                    }}
                }}

                function upgradeCave() {{
                    if (window.pyqtSignal) {{
                        window.pyqtSignal('cave_upgrade_requested');
                    }}
                }}

                function upgradeSpiritArray() {{
                    if (window.pyqtSignal) {{
                        window.pyqtSignal('spirit_array_upgrade_requested');
                    }}
                }}

                // 页面加载完成后的初始化
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('洞府页面加载完成');

                    // 等待Python端传入真实数据，不使用模拟数据
                }});
            </script>
        </body>
        </html>
        """

        if hasattr(self, 'cave_display'):
            self.cave_display.setHtml(html_template)

    def on_html_load_finished(self, success):
        """HTML页面加载完成回调"""
        if success:
            self.html_loaded = True
            print("✅ 洞府HTML页面加载成功")

            # 设置JavaScript桥接
            self.setup_javascript_bridge()

            # 延迟更新数据，确保JavaScript已准备好
            QTimer.singleShot(200, self.update_html_display)
        else:
            print("❌ 洞府HTML页面加载失败")

    def setup_javascript_bridge(self):
        """设置JavaScript桥接"""
        try:
            # 注入JavaScript桥接函数
            js_code = """
            window.pyqtSignal = function(signal, data) {
                if (signal === 'breakthrough_requested') {
                    document.title = 'SIGNAL:breakthrough_requested';
                } else if (signal === 'spirit_array_upgrade_requested') {
                    document.title = 'SIGNAL:spirit_array_upgrade_requested';
                } else if (signal === 'cave_upgrade_requested') {
                    document.title = 'SIGNAL:cave_upgrade_requested';
                }
            };
            console.log('✅ 洞府JavaScript桥接已建立');
            """
            self.cave_display.page().runJavaScript(js_code)

            # 监听页面标题变化
            self.cave_display.page().titleChanged.connect(self.handle_title_change)

        except Exception as e:
            print(f"❌ 设置洞府JavaScript桥接失败: {e}")

    def handle_title_change(self, title):
        """处理页面标题变化（用于JavaScript信号）"""
        if title.startswith('SIGNAL:'):
            signal = title.replace('SIGNAL:', '')
            if signal == 'breakthrough_requested':
                self.show_breakthrough()
            elif signal == 'spirit_array_upgrade_requested':
                self.upgrade_spirit_array()
            elif signal == 'cave_upgrade_requested':
                self.upgrade_cave()

    def update_html_display(self):
        """更新HTML显示"""
        if not hasattr(self, 'cave_display') or not self.html_loaded:
            return

        if not self.cave_data:
            return

        try:
            # 获取修炼状态数据
            cultivation_data = self.get_cultivation_data()

            # 合并洞府数据和修炼数据
            combined_data = {**self.cave_data, **cultivation_data}

            # 通过JavaScript更新洞府信息
            js_code = f"""
                if (typeof updateCaveInfo === 'function') {{
                    updateCaveInfo({self.cave_data_to_js(combined_data)});
                }}
            """

            self.cave_display.page().runJavaScript(js_code, lambda result: None)

        except Exception as e:
            print(f"❌ 更新洞府HTML显示失败: {e}")

    def get_cultivation_data(self):
        """获取修炼状态数据"""
        try:
            # 优先从状态管理器获取用户数据（与主界面保持同步）
            if hasattr(self, 'state_manager') and self.state_manager:
                user_data = self.state_manager.user_data
                if user_data:
                    return {
                        'cultivation_exp': user_data.get('cultivation_exp', 0),
                        'cultivation_realm': user_data.get('cultivation_realm', 0),
                        'current_realm_name': user_data.get('current_realm_name', '凡人'),
                    }

            # 备用方案：从API获取
            response = self.api_client.game.get_cultivation_status()
            if response.get('success'):
                data = response['data']
                return {
                    'cultivation_exp': data.get('current_exp', 0),
                    'cultivation_realm': data.get('current_realm', 0),
                    'current_realm_name': data.get('current_realm_name', '凡人'),
                }
            else:
                print(f"⚠️ 获取修炼状态失败: {response.get('message', '未知错误')}")
                return {}
        except Exception as e:
            print(f"❌ 获取修炼状态异常: {e}")
            return {}

    def cave_data_to_js(self, data=None):
        """将洞府数据转换为JavaScript格式"""
        import json
        if data is None:
            data = self.cave_data
        return json.dumps(data)








    def load_cave_info(self):
        """加载洞府信息"""
        try:
            response = self.api_client.game.get_cave_info()
            if response.get('success'):
                self.cave_data = response['data']
                if WEBENGINE_AVAILABLE:
                    self.update_html_display()
            else:
                QMessageBox.warning(self, "错误", f"获取洞府信息失败: {response.get('message', '未知错误')}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载洞府信息失败: {str(e)}")

    def on_user_data_updated(self, user_data):
        """当用户数据更新时，同步更新洞府界面的修为进度"""
        try:
            if WEBENGINE_AVAILABLE and hasattr(self, 'cave_display') and self.html_loaded:
                # 延迟一点更新，确保数据已经完全更新
                QTimer.singleShot(100, self.update_html_display)
        except Exception as e:
            print(f"❌ 洞府界面同步用户数据失败: {e}")

    def get_next_spirit_bonus(self, level: int) -> float:
        """获取下一级聚灵阵的速度加成"""
        bonus_map = {0: 1.0, 1: 1.2, 2: 1.5, 3: 1.8, 4: 2.2, 5: 2.5}
        return bonus_map.get(level, 1.0)

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
                f"突破成功率: {breakthrough_rate * 100:.1f}%\n\n"
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
