# 优化的修炼日志组件
from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from client.ui.performance.optimized_html_widget import OptimizedHTMLWidget, HTMLTemplateBuilder
from client.ui.performance.html_cache import html_cache_manager
from shared.constants import CULTIVATION_FOCUS_TYPES
from shared.utils import get_realm_name, get_luck_level_name


class OptimizedCultivationLogWidget(OptimizedHTMLWidget):
    """优化的修炼日志组件"""
    
    # 信号定义
    cultivation_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("cultivation_log", parent)
        
        # 修炼相关数据
        self.cultivation_logs: List[Dict[str, Any]] = []
        self.countdown_entry_id = None
        self.next_cultivation_time = None
        self.current_focus = "HP"
        
        # 优化配置
        self.max_log_entries = 100  # 最大日志条目数
        self.countdown_update_interval = 1000  # 倒计时更新间隔(ms)
        
        # 倒计时定时器
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown_display)
        
        # 连接信号
        self.html_ready.connect(self.on_html_ready)
        
    def generate_html_template(self) -> str:
        """生成HTML模板"""
        # 使用缓存的CSS和JavaScript
        css = html_cache_manager.get_css("cultivation_log_css", self._generate_css)
        js = html_cache_manager.get_javascript("cultivation_log_js", self._generate_javascript)
        
        builder = HTMLTemplateBuilder()
        template = (builder
                   .add_head("修炼日志", css)
                   .add_body_start("cultivation-log-body")
                   .add_content(self._generate_html_content())
                   .add_script(js)
                   .add_body_end()
                   .build())
        
        return template
        
    def _generate_css(self) -> str:
        """生成CSS样式"""
        return """
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                margin: 0;
                padding: 10px;
                background-color: #f8f9fa;
                font-size: 13px;
            }
            
            .log-container {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e1e5e9;
                padding: 15px;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .log-header {
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 2px solid #3498db;
            }
            
            .log-entry {
                margin-bottom: 8px;
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid #3498db;
                background-color: #f8f9fa;
                transition: background-color 0.2s ease;
            }
            
            .log-entry:hover {
                background-color: #e9ecef;
            }
            
            .log-timestamp {
                color: #6c757d;
                font-size: 11px;
                margin-right: 8px;
            }
            
            .log-message {
                color: #2c3e50;
            }
            
            .log-success {
                border-left-color: #27ae60;
                background-color: #d5f4e6;
            }
            
            .log-warning {
                border-left-color: #f39c12;
                background-color: #fef9e7;
            }
            
            .log-error {
                border-left-color: #e74c3c;
                background-color: #fadbd8;
            }
            
            .log-info {
                border-left-color: #3498db;
                background-color: #ebf3fd;
            }
            
            .countdown-entry {
                border-left-color: #9b59b6;
                background-color: #f4ecf7;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .cultivation-status {
                background-color: #e8f5e8;
                border: 1px solid #c3e6c3;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 10px;
                text-align: center;
            }
            
            .focus-indicator {
                display: inline-block;
                padding: 4px 8px;
                background-color: #3498db;
                color: white;
                border-radius: 12px;
                font-size: 11px;
                margin-left: 5px;
            }
        """
        
    def _generate_javascript(self) -> str:
        """生成JavaScript代码"""
        return """
            let logEntries = [];
            let maxEntries = 100;
            
            function addLogEntry(timestamp, message, type, color) {
                const container = document.getElementById('logContainer');
                if (!container) return;
                
                // 创建日志条目
                const entry = {
                    id: 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                    timestamp: timestamp,
                    message: message,
                    type: type,
                    color: color
                };
                
                logEntries.push(entry);
                
                // 限制日志条目数量
                if (logEntries.length > maxEntries) {
                    const removedEntry = logEntries.shift();
                    const removedElement = document.getElementById(removedEntry.id);
                    if (removedElement) {
                        removedElement.remove();
                    }
                }
                
                // 添加到DOM
                const entryElement = createLogEntryElement(entry);
                container.appendChild(entryElement);
                
                // 滚动到底部
                container.scrollTop = container.scrollHeight;
            }
            
            function createLogEntryElement(entry) {
                const div = document.createElement('div');
                div.id = entry.id;
                div.className = `log-entry log-${entry.type}`;
                
                div.innerHTML = `
                    <span class="log-timestamp">${entry.timestamp}</span>
                    <span class="log-message">${entry.message}</span>
                `;
                
                return div;
            }
            
            function addCountdownEntry(entryId, timestamp, message) {
                const container = document.getElementById('logContainer');
                if (!container) return;
                
                const div = document.createElement('div');
                div.id = entryId;
                div.className = 'log-entry countdown-entry';
                
                div.innerHTML = `
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="log-message">${message}</span>
                `;
                
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }
            
            function updateCountdownEntry(entryId, timestamp, message) {
                const entry = document.getElementById(entryId);
                if (entry) {
                    entry.innerHTML = `
                        <span class="log-timestamp">${timestamp}</span>
                        <span class="log-message">${message}</span>
                    `;
                }
            }
            
            function removeCountdownEntry(entryId) {
                const entry = document.getElementById(entryId);
                if (entry) {
                    entry.remove();
                }
            }
            
            function updateCultivationStatus(focusType, focusName) {
                const statusElement = document.getElementById('cultivationStatus');
                if (statusElement) {
                    statusElement.innerHTML = `
                        当前修炼方向: ${focusName}
                        <span class="focus-indicator">${focusType}</span>
                    `;
                }
            }
            
            function clearLogs() {
                const container = document.getElementById('logContainer');
                if (container) {
                    container.innerHTML = '';
                }
                logEntries = [];
            }
            
            // 批量添加日志条目（性能优化）
            function addLogEntriesBatch(entries) {
                const container = document.getElementById('logContainer');
                if (!container) return;
                
                const fragment = document.createDocumentFragment();
                
                entries.forEach(entry => {
                    const entryElement = createLogEntryElement(entry);
                    fragment.appendChild(entryElement);
                    logEntries.push(entry);
                });
                
                // 限制日志条目数量
                while (logEntries.length > maxEntries) {
                    const removedEntry = logEntries.shift();
                    const removedElement = document.getElementById(removedEntry.id);
                    if (removedElement) {
                        removedElement.remove();
                    }
                }
                
                container.appendChild(fragment);
                container.scrollTop = container.scrollHeight;
            }
        """
        
    def _generate_html_content(self) -> str:
        """生成HTML内容"""
        return """
            <div class="cultivation-status" id="cultivationStatus">
                当前修炼方向: 体修 <span class="focus-indicator">HP</span>
            </div>
            
            <div class="log-container">
                <div class="log-header">修炼日志</div>
                <div id="logContainer"></div>
            </div>
        """
        
    def on_html_ready(self):
        """HTML准备完成"""
        # 更新修炼状态显示
        self.update_cultivation_status()
        
        # 如果有历史日志，批量添加
        if self.cultivation_logs:
            self.add_logs_batch(self.cultivation_logs[-50:])  # 只显示最近50条
            
    def _apply_data_update(self, data: dict):
        """应用数据更新"""
        if 'focus' in data:
            self.current_focus = data['focus']
            self.update_cultivation_status()
            
        if 'next_cultivation_time' in data:
            self.next_cultivation_time = data['next_cultivation_time']
            self.start_countdown_timer()
            
        if 'logs' in data:
            self.add_logs_batch(data['logs'])
            
    def update_cultivation_status(self):
        """更新修炼状态显示"""
        focus_name = CULTIVATION_FOCUS_TYPES.get(self.current_focus, "未知")
        
        js_code = f"""
            updateCultivationStatus('{self.current_focus}', '{focus_name}');
        """
        
        self.execute_javascript(js_code)
        
    def add_log(self, message: str, log_type: str = "info", color: str = "#3498db"):
        """添加单条日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'id': f'log_{datetime.now().timestamp()}_{len(self.cultivation_logs)}',
            'timestamp': timestamp,
            'message': message,
            'type': log_type,
            'color': color
        }
        
        self.cultivation_logs.append(log_entry)
        
        # 限制内存中的日志数量
        if len(self.cultivation_logs) > self.max_log_entries:
            self.cultivation_logs.pop(0)
            
        # 添加到HTML显示
        js_code = f"addLogEntry('{timestamp}', '{message}', '{log_type}', '{color}');"
        self.execute_javascript(js_code)
        
    def add_logs_batch(self, logs: List[Dict[str, Any]]):
        """批量添加日志"""
        if not logs:
            return
            
        # 转换为JavaScript数组格式
        js_entries = []
        for log in logs:
            js_entry = f"""{{
                id: '{log.get('id', 'log_' + Date.now())}',
                timestamp: '{log.get('timestamp', '')}',
                message: '{log.get('message', '')}',
                type: '{log.get('type', 'info')}',
                color: '{log.get('color', '#3498db')}'
            }}"""
            js_entries.append(js_entry)
            
        js_code = f"addLogEntriesBatch([{','.join(js_entries)}]);"
        self.execute_javascript(js_code)
        
    def start_countdown_timer(self):
        """启动倒计时定时器"""
        if not self.countdown_timer.isActive():
            self.countdown_timer.start(self.countdown_update_interval)
            
    def stop_countdown_timer(self):
        """停止倒计时定时器"""
        self.countdown_timer.stop()
        
    def update_countdown_display(self):
        """更新倒计时显示"""
        if not self.next_cultivation_time:
            self.stop_countdown_timer()
            return
            
        current_time = datetime.now()
        time_diff = (self.next_cultivation_time - current_time).total_seconds()
        
        if time_diff > 0:
            minutes = int(time_diff // 60)
            seconds = int(time_diff % 60)
            
            focus_name = CULTIVATION_FOCUS_TYPES.get(self.current_focus, "未知")
            message = f"正在进行[{focus_name}]，剩余时间{minutes}分{seconds:02d}秒..."
            timestamp = current_time.strftime("%H:%M:%S")
            
            if not self.countdown_entry_id:
                self.countdown_entry_id = f"countdown_{current_time.timestamp()}"
                js_code = f"addCountdownEntry('{self.countdown_entry_id}', '{timestamp}', '{message}');"
            else:
                js_code = f"updateCountdownEntry('{self.countdown_entry_id}', '{timestamp}', '{message}');"
                
            self.execute_javascript(js_code)
        else:
            # 倒计时结束
            if self.countdown_entry_id:
                js_code = f"removeCountdownEntry('{self.countdown_entry_id}');"
                self.execute_javascript(js_code)
                self.countdown_entry_id = None
                
            self.next_cultivation_time = None
            self.stop_countdown_timer()
            self.cultivation_completed.emit()
            
    def clear_logs(self):
        """清空日志"""
        self.cultivation_logs.clear()
        self.execute_javascript("clearLogs();")
        
    def set_cultivation_focus(self, focus: str):
        """设置修炼方向"""
        self.current_focus = focus
        self.update_cultivation_status()
        
    def set_next_cultivation_time(self, next_time: datetime):
        """设置下次修炼时间"""
        self.next_cultivation_time = next_time
        self.start_countdown_timer()
