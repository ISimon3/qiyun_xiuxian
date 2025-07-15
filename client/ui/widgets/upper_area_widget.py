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
    cave_window_requested = pyqtSignal()  # 洞府窗口请求信号

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

        # 延迟初始化数据 - 只在没有真实数据时显示默认数据
        if WEBENGINE_AVAILABLE:
            # 检查是否有预加载的数据
            QTimer.singleShot(100, self.check_and_init_data)

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

                /* 头像和基本信息区域 */
                .header-section {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 8px;
                    border: 1px solid #e1e5e9;
                    min-height: 120px;
                }

                .header-top {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .avatar-container {
                    position: relative;
                    width: 60px;
                    height: 60px;
                }

                .avatar {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    border: 3px solid #28a745;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    color: white;
                    font-weight: bold;
                }

                .character-basic-info {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .character-name-line {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .character-name {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                }

                .character-id {
                    font-size: 11px;
                    color: #666;
                    background: #f8f9fa;
                    padding: 2px 6px;
                    border-radius: 4px;
                }

                .character-realm {
                    font-size: 14px;
                    font-weight: bold;
                    color: #e74c3c;
                }

                .sign-icon {
                    font-size: 24px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    padding: 4px;
                    border-radius: 50%;
                }

                .sign-icon:hover {
                    transform: scale(1.1);
                    background: rgba(255, 255, 255, 0.2);
                }

                /* 修为进度条区域 */
                .cultivation-progress {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-top: 4px;
                    position: relative;
                }

                .cultivation-progress-bar {
                    position: relative;
                    width: 70%;
                    height: 18px;
                    background: #f0f0f0;
                    border-radius: 9px;
                    overflow: hidden;
                    border: 1px solid #ddd;
                }

                .cultivation-progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
                    border-radius: 9px;
                    transition: width 0.3s ease;
                    position: relative;
                }

                .cultivation-progress-text {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-size: 10px;
                    font-weight: bold;
                    color: #333;
                    text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
                    z-index: 1;
                }

                /* 突破提示气泡 */
                .breakthrough-tip {
                    background: #FFD700;
                    color: #8B4513;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: bold;
                    border: 1px solid #FFA500;
                    animation: pulse 2s infinite;
                    cursor: pointer;
                }

                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }

                /* 五边形属性图表区域 */
                .pentagon-section {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 16px;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 8px;
                    border: 1px solid #e1e5e9;
                    min-height: 200px;
                }

                .pentagon-container {
                    position: relative;
                    width: 180px;
                    height: 180px;
                }

                #pentagonCanvas {
                    width: 100%;
                    height: 100%;
                }

                .attribute-labels {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    pointer-events: none;
                }

                .attribute-label {
                    position: absolute;
                    font-size: 18px;
                    color: #2c3e50;
                    text-align: center;
                    cursor: pointer;
                    pointer-events: auto;
                    padding: 4px;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.9);
                    border: 2px solid #ddd;
                    transition: all 0.3s ease;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .attribute-label:hover {
                    background: #3498db;
                    color: white;
                    transform: scale(1.2);
                    border-color: #3498db;
                    box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
                }

                .attribute-label.active {
                    background: #e74c3c;
                    color: white;
                    border-color: #e74c3c;
                    box-shadow: 0 4px 8px rgba(231, 76, 60, 0.3);
                    transform: scale(1.1);
                }

                /* 修炼状态气泡 */
                .cultivation-bubble {
                    position: absolute;
                    background: #2c3e50;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: bold;
                    white-space: nowrap;
                    z-index: 1000;
                    opacity: 0;
                    transform: translateY(-5px);
                    transition: all 0.3s ease;
                    pointer-events: none;
                }

                .cultivation-bubble.show {
                    opacity: 1;
                    transform: translateY(-10px);
                }

                .cultivation-bubble::after {
                    content: '';
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    margin-left: -4px;
                    border: 4px solid transparent;
                    border-top-color: #2c3e50;
                }

                .attribute-value {
                    position: absolute;
                    top: -8px;
                    right: -8px;
                    background: #f39c12;
                    color: white;
                    font-size: 8px;
                    font-weight: bold;
                    padding: 1px 4px;
                    border-radius: 8px;
                    min-width: 16px;
                    text-align: center;
                }

                /* 资源信息区域 */
                .resources-section {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 8px;
                    border: 1px solid #e1e5e9;
                }

                .resource-item {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 11px;
                }

                .resource-icon {
                    font-size: 14px;
                }

                .resource-value {
                    font-weight: bold;
                    color: #f39c12;
                }



                /* 功能按钮区域 */
                .function-buttons {
                    display: flex;
                    justify-content: space-between;
                    gap: 4px;
                    padding: 6px;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 8px;
                    border: 1px solid #e1e5e9;
                }

                .function-btn {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 6px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    color: #495057;
                    height: 36px;
                    width: 36px;
                }

                .function-btn:hover {
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
                }

                .function-btn-icon {
                    font-size: 16px;
                }

                /* 进度条样式 */
                .progress-section {
                    margin: 8px 0;
                }

                .progress-bar {
                    width: 100%;
                    height: 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-bottom: 4px;
                }

                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
                    border-radius: 4px;
                    transition: width 0.5s ease;
                }

                .progress-text {
                    font-size: 10px;
                    color: #666;
                    text-align: center;
                }

                /* 响应式设计 */
                @media (max-width: 400px) {
                    .function-buttons {
                        grid-template-columns: repeat(3, 1fr);
                    }

                    .pentagon-container {
                        width: 150px;
                        height: 150px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <!-- 头像和基本信息区域 -->
                <div class="header-section">
                    <div class="header-top">
                        <div class="avatar-container">
                            <div class="avatar" id="characterAvatar">头</div>
                        </div>
                        <div class="character-basic-info">
                            <div class="character-name-line">
                                <span class="character-name" id="characterName">道友名称</span>
                                <span class="character-id" id="characterId">(ID: xxxxxxx)</span>
                            </div>
                            <div>
                                <span class="character-realm" id="characterRealm">境界：筑基期</span>
                            </div>
                        </div>
                        <div class="sign-icon" id="signIcon" onclick="handleDailySign()" title="每日签到">📅</div>
                    </div>

                    <!-- 修为进度条 -->
                    <div class="cultivation-progress">
                        <div class="cultivation-progress-bar">
                            <div class="cultivation-progress-fill" id="cultivationProgressFill" style="width: 50%"></div>
                            <div class="cultivation-progress-text" id="cultivationProgressText">500/1000</div>
                        </div>
                        <div id="breakthroughTip" class="breakthrough-tip" style="display: none;" onclick="openCaveWindow()" title="点击进入洞府进行突破">
                            可尝试突破
                        </div>
                    </div>
                </div>

                <!-- 五边形属性图表区域 -->
                <div class="pentagon-section">
                    <div class="pentagon-container">
                        <canvas id="pentagonCanvas" width="180" height="180"></canvas>
                        <div class="attribute-labels">
                            <div class="attribute-label" id="label-hp" onclick="setCultivationFocus('HP')" title="体修">
                                💪
                                <span class="attribute-value" id="hp-value">100</span>
                            </div>
                            <div class="attribute-label" id="label-physical-attack" onclick="setCultivationFocus('PHYSICAL_ATTACK')" title="力修">
                                ⚔️
                                <span class="attribute-value" id="physical-attack-value">20</span>
                            </div>
                            <div class="attribute-label" id="label-magic-attack" onclick="setCultivationFocus('MAGIC_ATTACK')" title="法修">
                                🔮
                                <span class="attribute-value" id="magic-attack-value">20</span>
                            </div>
                            <div class="attribute-label" id="label-physical-defense" onclick="setCultivationFocus('PHYSICAL_DEFENSE')" title="护体">
                                🛡️
                                <span class="attribute-value" id="physical-defense-value">15</span>
                            </div>
                            <div class="attribute-label" id="label-magic-defense" onclick="setCultivationFocus('MAGIC_DEFENSE')" title="抗法">
                                🌟
                                <span class="attribute-value" id="magic-defense-value">15</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 资源信息区域 -->
                <div class="resources-section">
                    <div class="resource-item">
                        <span class="resource-icon">💰</span>
                        <span>金币: </span>
                        <span class="resource-value" id="goldValue">xxx</span>
                    </div>
                    <div class="resource-item">
                        <span class="resource-icon">💎</span>
                        <span>灵石: </span>
                        <span class="resource-value" id="spiritStoneValue">xxx</span>
                    </div>
                    <div class="resource-item">
                        <span class="resource-icon">🍀</span>
                        <span>今日气运: </span>
                        <span class="resource-value" id="luckValue">xxx</span>
                    </div>
                </div>



                <!-- 功能按钮区域 -->
                <div class="function-buttons">
                    <div class="function-btn" onclick="selectFunction('backpack')" title="背包">
                        <div class="function-btn-icon">🎒</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('cave')" title="洞府">
                        <div class="function-btn-icon">🏠</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('farm')" title="农场">
                        <div class="function-btn-icon">🌱</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('alchemy')" title="炼丹">
                        <div class="function-btn-icon">⚗️</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('dungeon')" title="副本">
                        <div class="function-btn-icon">⚔️</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('worldboss')" title="魔君">
                        <div class="function-btn-icon">👹</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('shop')" title="商场">
                        <div class="function-btn-icon">🏪</div>
                    </div>
                    <div class="function-btn" onclick="selectFunction('channel')" title="频道">
                        <div class="function-btn-icon">💬</div>
                    </div>
                </div>
            </div>

            <script>
                // 全局变量
                let characterData = null;
                let cultivationStatus = null;
                let currentAttributes = {
                    hp: 100,
                    physical_attack: 20,
                    magic_attack: 20,
                    physical_defense: 15,
                    magic_defense: 15
                };
                // 修炼获得的训练属性（用于五边形显示）
                let trainingAttributes = {
                    hp_training: 0,
                    physical_attack_training: 0,
                    magic_attack_training: 0,
                    physical_defense_training: 0,
                    magic_defense_training: 0
                };

                // 五边形顶点位置计算
                function getPentagonPoints(centerX, centerY, radius) {
                    const points = [];
                    const angleStep = (2 * Math.PI) / 5;
                    const startAngle = -Math.PI / 2; // 从顶部开始

                    for (let i = 0; i < 5; i++) {
                        const angle = startAngle + i * angleStep;
                        const x = centerX + radius * Math.cos(angle);
                        const y = centerY + radius * Math.sin(angle);
                        points.push({ x, y });
                    }
                    return points;
                }

                // 绘制五边形图表
                function drawPentagon() {
                    const canvas = document.getElementById('pentagonCanvas');
                    if (!canvas) return;

                    const ctx = canvas.getContext('2d');
                    const centerX = canvas.width / 2;
                    const centerY = canvas.height / 2;
                    const maxRadius = 70;

                    // 清空画布
                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    // 绘制背景网格（多层五边形）
                    ctx.strokeStyle = '#e9ecef';
                    ctx.lineWidth = 1;
                    for (let i = 1; i <= 5; i++) {
                        const radius = (maxRadius / 5) * i;
                        const points = getPentagonPoints(centerX, centerY, radius);

                        ctx.beginPath();
                        ctx.moveTo(points[0].x, points[0].y);
                        for (let j = 1; j < points.length; j++) {
                            ctx.lineTo(points[j].x, points[j].y);
                        }
                        ctx.closePath();
                        ctx.stroke();
                    }

                    // 绘制从中心到顶点的线
                    ctx.strokeStyle = '#dee2e6';
                    ctx.lineWidth = 1;
                    const outerPoints = getPentagonPoints(centerX, centerY, maxRadius);
                    for (const point of outerPoints) {
                        ctx.beginPath();
                        ctx.moveTo(centerX, centerY);
                        ctx.lineTo(point.x, point.y);
                        ctx.stroke();
                    }

                    // 计算修炼训练属性值对应的半径（显示修炼获得的数据）
                    const maxTrainingValue = Math.max(
                        trainingAttributes.hp_training,
                        trainingAttributes.physical_attack_training,
                        trainingAttributes.magic_attack_training,
                        trainingAttributes.physical_defense_training,
                        trainingAttributes.magic_defense_training,
                        10  // 最小值，避免除零
                    );

                    const trainingValues = [
                        trainingAttributes.hp_training,              // 体修训练值
                        trainingAttributes.physical_attack_training, // 物修训练值
                        trainingAttributes.magic_attack_training,    // 法修训练值
                        trainingAttributes.physical_defense_training,// 护体训练值
                        trainingAttributes.magic_defense_training    // 抗法训练值
                    ];

                    // 绘制修炼训练数据多边形
                    const dataPoints = [];
                    for (let i = 0; i < 5; i++) {
                        const ratio = Math.min(trainingValues[i] / Math.max(maxTrainingValue, 10), 1);
                        const radius = maxRadius * ratio;
                        const angle = -Math.PI / 2 + i * (2 * Math.PI) / 5;
                        const x = centerX + radius * Math.cos(angle);
                        const y = centerY + radius * Math.sin(angle);
                        dataPoints.push({ x, y });
                    }

                    // 填充属性区域
                    ctx.fillStyle = 'rgba(52, 152, 219, 0.3)';
                    ctx.strokeStyle = '#3498db';
                    ctx.lineWidth = 2;

                    ctx.beginPath();
                    ctx.moveTo(dataPoints[0].x, dataPoints[0].y);
                    for (let i = 1; i < dataPoints.length; i++) {
                        ctx.lineTo(dataPoints[i].x, dataPoints[i].y);
                    }
                    ctx.closePath();
                    ctx.fill();
                    ctx.stroke();

                    // 绘制属性点
                    ctx.fillStyle = '#e74c3c';
                    for (const point of dataPoints) {
                        ctx.beginPath();
                        ctx.arc(point.x, point.y, 3, 0, 2 * Math.PI);
                        ctx.fill();
                    }

                    // 更新标签位置
                    updateAttributeLabels();
                }

                // 更新属性标签位置
                function updateAttributeLabels() {
                    const canvas = document.getElementById('pentagonCanvas');
                    if (!canvas) return;

                    const centerX = canvas.width / 2;
                    const centerY = canvas.height / 2;
                    const labelRadius = 80; // 图标距离中心的距离

                    const labels = [
                        { id: 'label-hp', valueId: 'hp-value', value: trainingAttributes.hp_training },
                        { id: 'label-physical-attack', valueId: 'physical-attack-value', value: trainingAttributes.physical_attack_training },
                        { id: 'label-magic-attack', valueId: 'magic-attack-value', value: trainingAttributes.magic_attack_training },
                        { id: 'label-physical-defense', valueId: 'physical-defense-value', value: trainingAttributes.physical_defense_training },
                        { id: 'label-magic-defense', valueId: 'magic-defense-value', value: trainingAttributes.magic_defense_training }
                    ];

                    for (let i = 0; i < labels.length; i++) {
                        const label = document.getElementById(labels[i].id);
                        const valueSpan = document.getElementById(labels[i].valueId);
                        if (label && valueSpan) {
                            // 计算每个图标的角度，确保与五边形顶点对齐
                            const angle = -Math.PI / 2 + i * (2 * Math.PI) / 5;

                            // 计算图标位置，添加微调偏移量让图标更好地对齐五边形顶点
                            const offsetX = -15; // 向左偏移15像素
                            const offsetY = -15; // 向上偏移15像素
                            const labelX = centerX + labelRadius * Math.cos(angle) - 16 + offsetX; // 16是图标宽度的一半
                            const labelY = centerY + labelRadius * Math.sin(angle) - 16 + offsetY; // 16是图标高度的一半

                            label.style.left = labelX + 'px';
                            label.style.top = labelY + 'px';

                            // 更新数值显示
                            valueSpan.textContent = labels[i].value;
                        }
                    }
                }

                // 气运等级配置
                const LUCK_LEVELS = {
                    "大凶": {"min": 0, "max": 10, "color": "#8B0000"},
                    "凶": {"min": 11, "max": 25, "color": "#DC143C"},
                    "小凶": {"min": 26, "max": 40, "color": "#FF6347"},
                    "平": {"min": 41, "max": 60, "color": "#808080"},
                    "小吉": {"min": 61, "max": 75, "color": "#32CD32"},
                    "吉": {"min": 76, "max": 90, "color": "#00CED1"},
                    "大吉": {"min": 91, "max": 100, "color": "#FFD700"}
                };

                // 获取气运等级名称
                function getLuckLevelName(luckValue) {
                    for (const [levelName, levelInfo] of Object.entries(LUCK_LEVELS)) {
                        if (luckValue >= levelInfo.min && luckValue <= levelInfo.max) {
                            return levelName;
                        }
                    }
                    return "平";
                }

                // 获取气运颜色
                function getLuckColor(luckValue) {
                    for (const [levelName, levelInfo] of Object.entries(LUCK_LEVELS)) {
                        if (luckValue >= levelInfo.min && luckValue <= levelInfo.max) {
                            return levelInfo.color;
                        }
                    }
                    return "#808080";
                }

                // 更新角色信息显示
                function updateCharacterInfo(data) {
                    characterData = data;

                    // 更新头像（显示角色名称首字）
                    const avatar = document.getElementById('characterAvatar');
                    if (avatar && data.name) {
                        avatar.textContent = data.name.charAt(0);
                    }

                    // 更新角色名称和ID
                    const nameElement = document.getElementById('characterName');
                    if (nameElement) {
                        nameElement.textContent = data.name || '道友名称';
                    }

                    const idElement = document.getElementById('characterId');
                    if (idElement) {
                        // 优先显示用户ID，如果没有则显示角色ID
                        const displayId = data.user_id || data.id || 'xxxxxxx';
                        idElement.textContent = `(ID: ${displayId})`;
                    }

                    // 更新境界
                    const realmElement = document.getElementById('characterRealm');
                    if (realmElement) {
                        const realmNames = [
                            '凡人', '练气初期', '练气中期', '练气后期', '练气大圆满',
                            '筑基初期', '筑基中期', '筑基后期', '筑基大圆满',
                            '金丹初期', '金丹中期', '金丹后期', '金丹大圆满',
                            '元婴初期', '元婴中期', '元婴后期', '元婴大圆满'
                        ];
                        const realmLevel = data.cultivation_realm || 0;
                        const realmName = realmNames[realmLevel] || `未知境界(${realmLevel})`;
                        realmElement.textContent = `境界：${realmName}`;
                    }

                    // 更新资源信息
                    const goldElement = document.getElementById('goldValue');
                    if (goldElement) {
                        goldElement.textContent = (data.gold || 0).toString();
                    }

                    const spiritStoneElement = document.getElementById('spiritStoneValue');
                    if (spiritStoneElement) {
                        spiritStoneElement.textContent = (data.spirit_stone || 0).toString();
                    }

                    const luckElement = document.getElementById('luckValue');
                    if (luckElement) {
                        const luckValue = data.luck_value || 50;
                        const luckLevel = getLuckLevelName(luckValue);
                        const luckColor = getLuckColor(luckValue);
                        luckElement.innerHTML = `<span style="color: ${luckColor}; font-weight: bold;">${luckLevel}</span>`;
                    }

                    // 更新修为进度条
                    updateCultivationProgress(data);

                    // 更新属性数据
                    if (data.attributes) {
                        currentAttributes = {
                            hp: data.attributes.hp || 100,
                            physical_attack: data.attributes.physical_attack || 20,
                            magic_attack: data.attributes.magic_attack || 20,
                            physical_defense: data.attributes.physical_defense || 15,
                            magic_defense: data.attributes.magic_defense || 15
                        };
                    }

                    // 更新修炼训练属性数据（用于五边形显示）
                    if (data.training_attributes) {
                        trainingAttributes = {
                            hp_training: data.training_attributes.hp_training || 0,
                            physical_attack_training: data.training_attributes.physical_attack_training || 0,
                            magic_attack_training: data.training_attributes.magic_attack_training || 0,
                            physical_defense_training: data.training_attributes.physical_defense_training || 0,
                            magic_defense_training: data.training_attributes.magic_defense_training || 0
                        };
                    }

                    // 重新绘制五边形图表
                    drawPentagon();

                    // 更新修炼方向显示
                    updateCultivationFocus(data.cultivation_focus || 'HP');
                }

                // 更新修为进度条
                function updateCultivationProgress(data) {
                    const currentExp = data.cultivation_exp || 0;
                    const currentRealm = data.cultivation_realm || 0;

                    // 修为需求表（与服务器端保持一致）
                    const expRequirements = {
                        0: 0, 1: 100, 2: 250, 3: 450, 4: 700,
                        5: 1000, 6: 1400, 7: 1900, 8: 2500,
                        9: 3200, 10: 4000, 11: 4900, 12: 5900,
                        13: 7000, 14: 8200, 15: 9500, 16: 10900,
                        17: 12400, 18: 14000, 19: 15700, 20: 17500,
                        21: 19400, 22: 21400, 23: 23500, 24: 25700,
                        25: 28000, 26: 30400, 27: 32900, 28: 35500,
                        29: 38200, 30: 41000, 31: 43900, 32: 46900,
                        33: 50000
                    };

                    // 获取下一境界的突破需求（这是玩家需要达到的总修为）
                    const nextRealmExp = expRequirements[currentRealm + 1] || 50000;

                    // 计算进度百分比（当前修为/突破需求）
                    const progressPercent = nextRealmExp > 0 ? (currentExp / nextRealmExp) * 100 : 100;

                    // 更新进度条
                    const progressFill = document.getElementById('cultivationProgressFill');
                    const progressText = document.getElementById('cultivationProgressText');
                    const breakthroughTip = document.getElementById('breakthroughTip');

                    if (progressFill) {
                        progressFill.style.width = Math.max(0, Math.min(100, progressPercent)) + '%';
                    }

                    if (progressText) {
                        // 显示格式：当前修为/突破需求
                        progressText.textContent = `${currentExp}/${nextRealmExp}`;
                    }

                    // 显示或隐藏突破提示
                    if (breakthroughTip) {
                        if (currentExp >= nextRealmExp && currentRealm < 33) {
                            breakthroughTip.style.display = 'block';
                        } else {
                            breakthroughTip.style.display = 'none';
                        }
                    }
                }

                // 打开洞府窗口（突破功能）
                function openCaveWindow() {
                    // 通过Qt信号通知主窗口打开洞府
                    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
                        window.pyqtSignal('cave_window_requested');
                    } else {
                        // 如果webChannel不可用，使用标题变化方式
                        document.title = 'cave_window_requested:' + Date.now();
                    }
                }

                // 更新修炼状态
                function updateCultivationStatus(data) {
                    cultivationStatus = data;
                    // 修炼状态显示已移除，只保存数据
                }

                // 更新修炼方向显示
                function updateCultivationFocus(focusType) {
                    // 移除所有气泡
                    const existingBubbles = document.querySelectorAll('.cultivation-bubble');
                    existingBubbles.forEach(bubble => bubble.remove());

                    // 移除所有active状态
                    const labels = document.querySelectorAll('.attribute-label');
                    labels.forEach(label => {
                        label.classList.remove('active');
                    });

                    const labelId = `label-${focusType.toLowerCase().replace('_', '-')}`;
                    const activeLabel = document.getElementById(labelId);

                    if (activeLabel) {
                        // 添加active类（背景色变化）
                        activeLabel.classList.add('active');

                        // 创建修炼状态气泡
                        const bubble = document.createElement('div');
                        bubble.className = 'cultivation-bubble';
                        bubble.textContent = '正在修炼';

                        // 获取图标位置
                        const rect = activeLabel.getBoundingClientRect();
                        const containerRect = activeLabel.offsetParent.getBoundingClientRect();

                        // 设置气泡位置（相对于容器）
                        bubble.style.left = (rect.left - containerRect.left + rect.width / 2 - 25) + 'px';
                        bubble.style.top = (rect.top - containerRect.top - 35) + 'px';

                        // 添加到容器中
                        activeLabel.offsetParent.appendChild(bubble);

                        // 显示气泡动画
                        setTimeout(() => {
                            bubble.classList.add('show');
                        }, 10);
                    }
                }

                // 设置修炼方向
                function setCultivationFocus(focusType) {
                    // 立即更新显示（实时背景变化）
                    updateCultivationFocus(focusType);

                    // 通过Qt信号发送到Python
                    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
                        // 使用webChannel发送信号
                        window.pyqtSignal('cultivation_focus_changed', focusType);
                    } else {
                        // 如果webChannel不可用，使用标题变化方式
                        document.title = 'cultivation:' + focusType + ':' + Date.now();
                    }
                }

                // 每日签到
                function handleDailySign() {
                    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
                        window.pyqtSignal('daily_sign_requested');
                    }
                }

                // 功能选择
                function selectFunction(functionKey) {
                    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
                        window.pyqtSignal('function_selected', functionKey);
                    }
                }

                // 页面加载完成后初始化
                document.addEventListener('DOMContentLoaded', function() {
                    // 初始绘制五边形
                    drawPentagon();

                    // 设置默认修炼方向
                    updateCultivationFocus('HP');
                });

                // 窗口大小改变时重新绘制
                window.addEventListener('resize', function() {
                    setTimeout(drawPentagon, 100);
                });
            </script>
        </body>
        </html>
        """

        self.html_display.setHtml(html_template)

        # 连接页面加载完成信号
        self.html_display.loadFinished.connect(self.on_page_loaded)

    def on_page_loaded(self, success: bool):
        """页面加载完成回调"""
        if success:
            print("✅ HTML页面加载完成")
            # 如果有待更新的数据，现在更新
            if hasattr(self, 'character_data') and self.character_data:
                print("🔄 页面加载完成，立即更新角色数据")
                QTimer.singleShot(100, lambda: self.update_character_info(self.character_data))

            if hasattr(self, 'cultivation_status') and self.cultivation_status:
                print("🔄 页面加载完成，立即更新修炼状态")
                QTimer.singleShot(150, lambda: self.update_cultivation_status(self.cultivation_status))

            if hasattr(self, 'luck_info') and self.luck_info:
                print("🔄 页面加载完成，立即更新气运信息")
                QTimer.singleShot(200, lambda: self.update_luck_info(self.luck_info))
        else:
            print("❌ HTML页面加载失败")

    def setup_javascript_events(self):
        """设置JavaScript事件监听"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        # 延迟设置事件监听，确保页面加载完成
        QTimer.singleShot(500, self._setup_events)

    def _setup_events(self):
        """实际设置事件监听"""
        try:
            # 注入事件监听器和全局函数
            js_code = """
            // 全局函数，供HTML中的onclick调用
            window.pyqtSignal = function(eventType, data) {
                console.log('PyQt Signal:', eventType, data);
                if (eventType === 'daily_sign_requested') {
                    document.title = 'dailySign:' + Date.now();
                } else if (eventType === 'function_selected') {
                    document.title = 'function:' + data + ':' + Date.now();
                } else if (eventType === 'cultivation_focus_changed') {
                    document.title = 'cultivation:' + data + ':' + Date.now();
                } else if (eventType === 'cave_window_requested') {
                    document.title = 'caveWindow:' + Date.now();
                }
            };

            // 确保函数在全局作用域中可用
            window.handleDailySign = function() {
                window.pyqtSignal('daily_sign_requested');
            };

            window.selectFunction = function(functionKey) {
                window.pyqtSignal('function_selected', functionKey);
            };

            window.setCultivationFocus = function(focusType) {
                window.pyqtSignal('cultivation_focus_changed', focusType);
            };

            window.openCaveWindow = function() {
                window.pyqtSignal('cave_window_requested');
            };
            """

            self.html_display.page().runJavaScript(js_code)

            # 监听页面标题变化
            self.html_display.page().titleChanged.connect(self.handle_title_change)

        except Exception as e:
            pass  # 设置JavaScript事件失败

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
            elif title.startswith('cultivation:'):
                parts = title.split(':')
                if len(parts) >= 2:
                    focus_type = parts[1]
                    self.cultivation_focus_changed.emit(focus_type)
            elif title.startswith('caveWindow:'):
                self.cave_window_requested.emit()
        except Exception as e:
            pass  # 处理标题变化失败

    def check_and_init_data(self):
        """检查是否有预加载数据，如果没有则显示默认数据"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        # 检查状态管理器是否有用户数据
        try:
            from client.state_manager import get_state_manager
            state_manager = get_state_manager()
            if state_manager.user_data:
                # 保存数据，等待页面加载完成后更新
                self.character_data = state_manager.user_data

                # 如果还有其他预加载数据，也保存
                if state_manager.cultivation_status:
                    self.cultivation_status = state_manager.cultivation_status
                if state_manager.luck_info:
                    self.luck_info = state_manager.luck_info

                return
        except Exception as e:
            pass  # 检查预加载数据失败

        # 没有预加载数据，显示默认数据
        QTimer.singleShot(500, self._init_default_data)

    def init_default_data(self):
        """初始化默认数据"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        # 延迟初始化，确保页面完全加载
        QTimer.singleShot(200, self._init_default_data)

    def _init_default_data(self):
        """实际初始化默认数据"""
        default_character_data = {
            'name': '道友名称',
            'id': '????????',
            'cultivation_realm': 0,
            'gold': 0,
            'spirit_stone': 0,
            'luck_value': 50,
            'cultivation_focus': 'HP',
            'attributes': {
                'hp': 100,
                'physical_attack': 20,
                'magic_attack': 20,
                'physical_defense': 15,
                'magic_defense': 15
            }
        }

        default_cultivation_status = {
            'is_active': False
        }

        self.update_character_info(default_character_data)
        self.update_cultivation_status(default_cultivation_status)
    def update_character_info(self, character_data: Dict[str, Any]):
        """更新角色信息"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        self.character_data = character_data

        try:
            # 将Python字典转换为JavaScript对象字符串
            import json
            js_data = json.dumps(character_data, ensure_ascii=False)

            # 检查JavaScript函数是否准备好，如果没有则等待
            check_and_update_js = f"""
            function tryUpdateCharacterInfo() {{
                if (typeof updateCharacterInfo === 'function') {{
                    console.log('✅ updateCharacterInfo函数已准备好，开始更新数据');
                    updateCharacterInfo({js_data});
                    return true;
                }} else {{
                    console.log('⏳ updateCharacterInfo函数还未准备好，等待中...');
                    return false;
                }}
            }}

            // 立即尝试更新
            if (!tryUpdateCharacterInfo()) {{
                // 如果失败，每100ms重试一次，最多重试50次（5秒）
                let retryCount = 0;
                const maxRetries = 50;
                const retryInterval = setInterval(() => {{
                    retryCount++;
                    if (tryUpdateCharacterInfo() || retryCount >= maxRetries) {{
                        clearInterval(retryInterval);
                        if (retryCount >= maxRetries) {{
                            console.error('❌ 超时：updateCharacterInfo函数始终未准备好');
                        }}
                    }}
                }}, 100);
            }}
            """

            self.html_display.page().runJavaScript(check_and_update_js)

        except Exception as e:
            print(f"❌ 更新角色信息失败: {e}")
            import traceback
            traceback.print_exc()

    def update_cultivation_status(self, cultivation_data: Dict[str, Any]):
        """更新修炼状态"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        self.cultivation_status = cultivation_data

        try:
            # 构建JavaScript调用来更新修炼状态
            import json
            js_data = json.dumps(cultivation_data, ensure_ascii=False)
            js_code = f"""
            if (typeof updateCultivationStatus === 'function') {{
                updateCultivationStatus({js_data});
            }} else {{
                console.log('updateCultivationStatus function not ready yet');
            }}
            """

            self.html_display.page().runJavaScript(js_code)

        except Exception as e:
            print(f"❌ 更新修炼状态失败: {e}")
    def update_luck_info(self, luck_data: Dict[str, Any]):
        """更新气运信息"""
        self.luck_info = luck_data

        # 如果有角色数据，重新更新显示
        if self.character_data:
            self.update_character_info(self.character_data)
    def update_channel_button(self, icon: str, tooltip: str):
        """更新频道按钮"""
        if not WEBENGINE_AVAILABLE or not hasattr(self, 'html_display'):
            return

        try:
            # 通过JavaScript更新频道按钮的图标和提示
            js_code = f"""
            (function() {{
                const channelButton = document.querySelector('[onclick*="channel"]');
                if (channelButton) {{
                    const iconElement = channelButton.querySelector('.function-btn-icon');
                    if (iconElement) {{
                        iconElement.textContent = '{icon}';
                    }}
                    channelButton.title = '{tooltip}';
                }}
            }})();
            """
            self.html_display.page().runJavaScript(js_code)
        except Exception as e:
            print(f"❌ 更新频道按钮失败: {e}")

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
