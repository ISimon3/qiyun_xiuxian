"""
每日签到组件
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import calendar

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None


class DailySignWidget(QWidget):
    """每日签到组件"""

    # 信号定义
    sign_in_requested = pyqtSignal()  # 签到请求信号
    close_requested = pyqtSignal()    # 关闭请求信号

    def __init__(self):
        super().__init__()

        # 签到数据
        self.sign_data: Optional[Dict[str, Any]] = None
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("每日签到")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 日历显示区域（移除标题栏）
        if WEBENGINE_AVAILABLE:
            self.create_html_calendar(main_layout)
        else:
            self.create_fallback_calendar(main_layout)

        # 底部按钮区域
        self.create_button_area(main_layout)

        self.setLayout(main_layout)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
        """)

        # 延迟初始化HTML内容
        if WEBENGINE_AVAILABLE:
            QTimer.singleShot(100, self.init_calendar_html)

    def create_title_bar(self, parent_layout: QVBoxLayout):
        """创建标题栏"""
        title_layout = QHBoxLayout()

        # 标题
        title_label = QLabel("📅 每日签到")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
                border: 1px solid #e1e5e9;
            }
        """)

        title_layout.addWidget(title_label)
        parent_layout.addLayout(title_layout)

    def create_html_calendar(self, parent_layout: QVBoxLayout):
        """创建HTML版本的日历"""
        self.calendar_display = QWebEngineView()
        self.calendar_display.setMinimumHeight(400)

        # 禁用右键上下文菜单
        self.calendar_display.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 设置样式
        self.calendar_display.setStyleSheet("""
            QWebEngineView {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)

        parent_layout.addWidget(self.calendar_display)

    def create_fallback_calendar(self, parent_layout: QVBoxLayout):
        """创建备用日历（WebEngine不可用时）"""
        fallback_label = QLabel("日历功能需要WebEngine支持")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 14px;
                padding: 50px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        parent_layout.addWidget(fallback_label)

    def create_button_area(self, parent_layout: QVBoxLayout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 签到按钮
        self.sign_button = QPushButton("🎁 立即签到")
        self.sign_button.setMinimumHeight(45)
        self.sign_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #20c997);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #20c997, stop:1 #17a2b8);
            }
            QPushButton:pressed {
                background: #17a2b8;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
        """)
        self.sign_button.clicked.connect(self.on_sign_in_clicked)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setMinimumHeight(45)
        close_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #495057);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #495057, stop:1 #343a40);
            }
            QPushButton:pressed {
                background: #343a40;
            }
        """)
        close_button.clicked.connect(self.close)

        button_layout.addWidget(self.sign_button)
        button_layout.addWidget(close_button)
        parent_layout.addLayout(button_layout)

    def init_calendar_html(self):
        """初始化日历HTML页面"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>每日签到日历</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
                    color: #333;
                    padding: 15px;
                    overflow: hidden;
                }

                .calendar-container {
                    max-width: 100%;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                }

                .calendar-header {
                    text-align: center;
                    margin-bottom: 20px;
                    padding: 15px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: bold;
                }

                .calendar-grid {
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    gap: 8px;
                    margin-bottom: 20px;
                }

                .calendar-day-header {
                    text-align: center;
                    padding: 10px 5px;
                    font-weight: bold;
                    color: #495057;
                    background: #e9ecef;
                    border-radius: 6px;
                    font-size: 12px;
                }

                .calendar-day {
                    aspect-ratio: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    position: relative;
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                }

                .calendar-day:hover {
                    background: #e3f2fd;
                    transform: scale(1.05);
                }

                .calendar-day.today {
                    background: linear-gradient(135deg, #ffd54f 0%, #ffb300 100%);
                    color: white;
                    font-weight: bold;
                    box-shadow: 0 2px 8px rgba(255, 193, 7, 0.4);
                }

                .calendar-day.signed {
                    background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
                    color: white;
                    font-weight: bold;
                }

                .calendar-day.signed::after {
                    content: "✓";
                    position: absolute;
                    top: 2px;
                    right: 4px;
                    font-size: 12px;
                    color: white;
                    font-weight: bold;
                }

                .calendar-day.other-month {
                    color: #adb5bd;
                    background: #f1f3f4;
                }

                .reward-info {
                    text-align: center;
                    padding: 15px;
                    background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
                    border-radius: 8px;
                    border: 1px solid #4caf50;
                    margin-top: 10px;
                }

                .reward-text {
                    color: #2e7d32;
                    font-weight: bold;
                    font-size: 14px;
                }

                .sign-status {
                    text-align: center;
                    padding: 10px;
                    margin-top: 10px;
                    border-radius: 6px;
                    font-weight: bold;
                }

                .sign-status.can-sign {
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                    color: #1976d2;
                    border: 1px solid #2196f3;
                }

                .sign-status.already-signed {
                    background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
                    color: #2e7d32;
                    border: 1px solid #4caf50;
                }
            </style>
        </head>
        <body>
            <div class="calendar-container">
                <div class="calendar-header" id="calendarHeader">
                    {current_month_year}
                </div>
                
                <div class="calendar-grid" id="calendarGrid">
                    <!-- 日历网格将通过JavaScript动态生成 -->
                </div>
                
                <div class="reward-info">
                    <div class="reward-text">💎 每日签到奖励：随机获得 50-200 灵石</div>
                </div>
                
                <div class="sign-status" id="signStatus">
                    <div>📅 点击上方按钮进行签到</div>
                </div>
            </div>

            <script>
                // 生成日历
                function generateCalendar(year, month, signedDates = []) {
                    const grid = document.getElementById('calendarGrid');
                    const header = document.getElementById('calendarHeader');

                    // 更新标题
                    const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月',
                                      '七月', '八月', '九月', '十月', '十一月', '十二月'];
                    header.textContent = `${year}年 ${monthNames[month - 1]}`;

                    // 清空网格
                    grid.innerHTML = '';

                    // 添加星期标题
                    const dayHeaders = ['日', '一', '二', '三', '四', '五', '六'];
                    dayHeaders.forEach(day => {
                        const dayHeader = document.createElement('div');
                        dayHeader.className = 'calendar-day-header';
                        dayHeader.textContent = day;
                        grid.appendChild(dayHeader);
                    });

                    // 获取当月第一天和最后一天
                    const firstDay = new Date(year, month - 1, 1);
                    const lastDay = new Date(year, month, 0);
                    const daysInMonth = lastDay.getDate();
                    const startDayOfWeek = firstDay.getDay();

                    // 获取今天的日期
                    const today = new Date();
                    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month - 1;
                    const todayDate = today.getDate();

                    // 添加上个月的日期（填充）
                    const prevMonth = month === 1 ? 12 : month - 1;
                    const prevYear = month === 1 ? year - 1 : year;
                    const prevMonthLastDay = new Date(prevYear, prevMonth, 0).getDate();

                    for (let i = startDayOfWeek - 1; i >= 0; i--) {
                        const dayElement = document.createElement('div');
                        dayElement.className = 'calendar-day other-month';
                        dayElement.textContent = prevMonthLastDay - i;
                        grid.appendChild(dayElement);
                    }

                    // 添加当月的日期
                    for (let day = 1; day <= daysInMonth; day++) {
                        const dayElement = document.createElement('div');
                        dayElement.className = 'calendar-day';
                        dayElement.textContent = day;

                        // 检查是否是今天
                        if (isCurrentMonth && day === todayDate) {
                            dayElement.classList.add('today');
                        }

                        // 检查是否已签到
                        const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
                        if (signedDates.includes(dateStr)) {
                            dayElement.classList.add('signed');
                        }

                        grid.appendChild(dayElement);
                    }

                    // 填充下个月的日期
                    const totalCells = grid.children.length;
                    const remainingCells = 42 - totalCells + 7; // 6行 * 7列 - 已有单元格 + 星期标题

                    for (let day = 1; day <= remainingCells; day++) {
                        const dayElement = document.createElement('div');
                        dayElement.className = 'calendar-day other-month';
                        dayElement.textContent = day;
                        grid.appendChild(dayElement);
                    }
                }

                // 更新签到状态
                function updateSignStatus(canSign, alreadySigned) {
                    const statusElement = document.getElementById('signStatus');

                    if (alreadySigned) {
                        statusElement.className = 'sign-status already-signed';
                        statusElement.innerHTML = '<div>✅ 今日已签到，明天再来吧！</div>';
                    } else if (canSign) {
                        statusElement.className = 'sign-status can-sign';
                        statusElement.innerHTML = '<div>🎁 今日尚未签到，快来领取奖励吧！</div>';
                    } else {
                        statusElement.className = 'sign-status';
                        statusElement.innerHTML = '<div>📅 点击上方按钮进行签到</div>';
                    }
                }

                // 页面加载完成后初始化
                document.addEventListener('DOMContentLoaded', function() {
                    var currentDate = new Date();
                    generateCalendar(currentDate.getFullYear(), currentDate.getMonth() + 1, []);
                    updateSignStatus(true, false);
                });
            </script>
        </body>
        </html>
        """

        # 格式化当前月份年份
        current_date = datetime.now()
        month_year = f"{current_date.year}年 {current_date.month}月"

        # 使用字符串替换而不是format()方法，避免大括号冲突
        formatted_html = html_template.replace("{current_month_year}", month_year)

        if hasattr(self.calendar_display, 'setHtml'):
            self.calendar_display.setHtml(formatted_html)

    def on_sign_in_clicked(self):
        """签到按钮点击处理"""
        self.sign_in_requested.emit()

    def update_sign_data(self, sign_data: Dict[str, Any]):
        """更新签到数据"""
        self.sign_data = sign_data
        
        # 更新按钮状态
        can_sign = sign_data.get('can_sign', True)
        already_signed = sign_data.get('already_signed', False)
        
        self.sign_button.setEnabled(can_sign and not already_signed)
        
        if already_signed:
            self.sign_button.setText("✅ 今日已签到")
        else:
            self.sign_button.setText("🎁 立即签到")
        
        # 更新HTML显示
        if WEBENGINE_AVAILABLE and hasattr(self, 'calendar_display'):
            self.update_calendar_display(sign_data)

    def update_calendar_display(self, sign_data: Dict[str, Any]):
        """更新日历显示"""
        signed_dates = sign_data.get('signed_dates', [])
        can_sign = sign_data.get('can_sign', True)
        already_signed = sign_data.get('already_signed', False)
        
        # 更新日历
        js_code = f"""
        var updateDate = new Date();
        generateCalendar(updateDate.getFullYear(), updateDate.getMonth() + 1, {signed_dates});
        updateSignStatus({str(can_sign).lower()}, {str(already_signed).lower()});
        """
        
        self.calendar_display.page().runJavaScript(js_code)

    def show_sign_result(self, result: Dict[str, Any]):
        """显示签到结果"""
        if result.get('success'):
            print(f"🔍 签到结果调试: {result}")
            reward = result.get('reward', {})
            print(f"🔍 奖励数据: {reward}")
            spirit_stone = reward.get('spirit_stone', 0)
            print(f"🔍 灵石数量: {spirit_stone}")

            QMessageBox.information(
                self,
                "签到成功",
                f"🎉 签到成功！\n💎 获得灵石：{spirit_stone}"
            )
            
            # 更新显示
            if self.sign_data:
                self.sign_data['already_signed'] = True
                self.sign_data['can_sign'] = False
                # 添加今天的日期到已签到列表
                today_str = datetime.now().strftime("%Y-%m-%d")
                if 'signed_dates' not in self.sign_data:
                    self.sign_data['signed_dates'] = []
                if today_str not in self.sign_data['signed_dates']:
                    self.sign_data['signed_dates'].append(today_str)
                
                self.update_sign_data(self.sign_data)
        else:
            error_msg = result.get('message', '签到失败')
            QMessageBox.warning(self, "签到失败", error_msg)
