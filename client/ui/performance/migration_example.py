# 组件迁移示例 - 修炼日志组件优化
"""
本文件展示如何将现有的HTML组件迁移到优化版本

迁移步骤:
1. 继承OptimizedHTMLWidget而不是QWidget
2. 实现generate_html_template方法
3. 重构数据更新逻辑
4. 优化JavaScript调用
5. 启用性能监控
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from client.ui.performance import (
    OptimizedHTMLWidget, 
    HTMLTemplateBuilder,
    PerformanceConfig,
    profile_operation,
    monitor_memory
)
from shared.constants import CULTIVATION_FOCUS_TYPES


class MigratedCultivationLogWidget(OptimizedHTMLWidget):
    """迁移后的修炼日志组件 - 性能优化版本"""
    
    # 信号定义
    clear_log_requested = pyqtSignal()
    cultivation_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        # 使用优化基类，指定模板名称
        super().__init__("cultivation_log_v2", parent)
        
        # 获取组件特定配置
        self.config = PerformanceConfig.get_component_config('cultivation_log')
        
        # 修炼相关数据
        self.log_entries: List[Dict[str, Any]] = []
        self.max_log_entries = self.config.get('max_log_entries', 100)
        self.cultivation_status: Optional[Dict[str, Any]] = None
        self.current_cultivation_focus = "HP"
        self.next_cultivation_time: Optional[datetime] = None
        self.countdown_entry_id: Optional[str] = None
        
        # 性能优化配置
        self.set_performance_config(
            enable_data_diff=True,
            enable_batch_updates=True,
            enable_lazy_loading=True,
            batch_update_interval=self.config.get('batch_log_threshold', 5) * 20
        )
        
        # 倒计时定时器
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown_display)
        
        # 连接信号
        self.html_ready.connect(self.on_html_ready)
        
    @profile_operation("generate_cultivation_log_template")
    def generate_html_template(self) -> str:
        """生成HTML模板 - 使用缓存优化"""
        # 使用HTMLTemplateBuilder构建模板
        builder = HTMLTemplateBuilder()
        
        # 获取缓存的CSS和JavaScript
        css = self.get_cached_css()
        js = self.get_cached_javascript()
        
        template = (builder
                   .add_head("修炼日志", css, self.get_meta_tags())
                   .add_body_start("cultivation-log-body")
                   .add_content(self.get_html_content())
                   .add_script(js)
                   .add_body_end()
                   .build())
        
        return template
    
    def get_cached_css(self) -> str:
        """获取缓存的CSS样式"""
        from client.ui.performance.html_cache import html_cache_manager
        
        return html_cache_manager.get_css("cultivation_log_css", self._generate_css)
    
    def get_cached_javascript(self) -> str:
        """获取缓存的JavaScript代码"""
        from client.ui.performance.html_cache import html_cache_manager
        
        return html_cache_manager.get_javascript("cultivation_log_js", self._generate_javascript)
    
    def get_meta_tags(self) -> str:
        """获取meta标签"""
        return """
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="修炼日志组件">
        """
    
    def get_html_content(self) -> str:
        """获取HTML内容结构"""
        return """
            <div class="cultivation-container">
                <div class="cultivation-status" id="cultivationStatus">
                    <div class="status-header">修炼状态</div>
                    <div class="status-content">
                        <span class="focus-label">当前方向:</span>
                        <span class="focus-value" id="focusValue">体修</span>
                        <span class="focus-indicator" id="focusIndicator">HP</span>
                    </div>
                </div>
                
                <div class="log-container">
                    <div class="log-header">
                        <span class="log-title">修炼日志</span>
                        <button class="clear-btn" onclick="clearLogs()">清空</button>
                    </div>
                    <div class="log-content" id="logContainer">
                        <!-- 日志条目将在这里动态添加 -->
                    </div>
                </div>
            </div>
        """
    
    def _generate_css(self) -> str:
        """生成CSS样式 - 只在首次调用时生成，后续使用缓存"""
        return """
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                margin: 0;
                padding: 8px;
                background-color: #f8f9fa;
                font-size: 13px;
                line-height: 1.4;
            }
            
            .cultivation-container {
                display: flex;
                flex-direction: column;
                height: 100%;
                gap: 10px;
            }
            
            .cultivation-status {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                padding: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .status-header {
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 8px;
                text-align: center;
            }
            
            .status-content {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .focus-label {
                font-size: 12px;
                opacity: 0.9;
            }
            
            .focus-value {
                font-weight: bold;
                font-size: 14px;
            }
            
            .focus-indicator {
                background-color: rgba(255,255,255,0.2);
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
            
            .log-container {
                flex: 1;
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e1e5e9;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .log-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #e1e5e9;
            }
            
            .log-title {
                font-weight: bold;
                color: #2c3e50;
            }
            
            .clear-btn {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .clear-btn:hover {
                background-color: #c0392b;
            }
            
            .log-content {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
                max-height: 300px;
            }
            
            .log-entry {
                margin-bottom: 6px;
                padding: 8px 10px;
                border-radius: 4px;
                border-left: 3px solid #3498db;
                background-color: #f8f9fa;
                transition: all 0.2s ease;
                font-size: 12px;
            }
            
            .log-entry:hover {
                background-color: #e9ecef;
                transform: translateX(2px);
            }
            
            .log-timestamp {
                color: #6c757d;
                font-size: 10px;
                margin-right: 8px;
                font-family: monospace;
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
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            /* 滚动条样式 */
            .log-content::-webkit-scrollbar {
                width: 6px;
            }
            
            .log-content::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 3px;
            }
            
            .log-content::-webkit-scrollbar-thumb {
                background: #c1c1c1;
                border-radius: 3px;
            }
            
            .log-content::-webkit-scrollbar-thumb:hover {
                background: #a8a8a8;
            }
        """
    
    def _generate_javascript(self) -> str:
        """生成JavaScript代码 - 只在首次调用时生成，后续使用缓存"""
        return """
            // 日志管理
            let logEntries = [];
            let maxEntries = 100;
            let logContainer = null;
            
            // 初始化
            document.addEventListener('DOMContentLoaded', function() {
                logContainer = document.getElementById('logContainer');
                console.log('修炼日志组件初始化完成');
            });
            
            // 批量添加日志条目（性能优化）
            function addLogEntriesBatch(entries) {
                if (!logContainer || !entries || entries.length === 0) return;
                
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
                
                logContainer.appendChild(fragment);
                scrollToBottom();
            }
            
            // 添加单条日志
            function addLogEntry(timestamp, message, type, color) {
                const entry = {
                    id: 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                    timestamp: timestamp,
                    message: message,
                    type: type,
                    color: color
                };
                
                addLogEntriesBatch([entry]);
            }
            
            // 创建日志条目元素
            function createLogEntryElement(entry) {
                const div = document.createElement('div');
                div.id = entry.id;
                div.className = `log-entry log-${entry.type}`;
                
                div.innerHTML = `
                    <span class="log-timestamp">${entry.timestamp}</span>
                    <span class="log-message">${escapeHtml(entry.message)}</span>
                `;
                
                return div;
            }
            
            // 倒计时相关函数
            function addCountdownEntry(entryId, timestamp, message) {
                if (!logContainer) return;
                
                const div = document.createElement('div');
                div.id = entryId;
                div.className = 'log-entry countdown-entry';
                
                div.innerHTML = `
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="log-message">${escapeHtml(message)}</span>
                `;
                
                logContainer.appendChild(div);
                scrollToBottom();
            }
            
            function updateCountdownEntry(entryId, timestamp, message) {
                const entry = document.getElementById(entryId);
                if (entry) {
                    entry.innerHTML = `
                        <span class="log-timestamp">${timestamp}</span>
                        <span class="log-message">${escapeHtml(message)}</span>
                    `;
                }
            }
            
            function removeCountdownEntry(entryId) {
                const entry = document.getElementById(entryId);
                if (entry) {
                    entry.remove();
                }
            }
            
            // 更新修炼状态
            function updateCultivationStatus(focusType, focusName) {
                const focusValue = document.getElementById('focusValue');
                const focusIndicator = document.getElementById('focusIndicator');
                
                if (focusValue) focusValue.textContent = focusName;
                if (focusIndicator) focusIndicator.textContent = focusType;
            }
            
            // 清空日志
            function clearLogs() {
                if (logContainer) {
                    logContainer.innerHTML = '';
                }
                logEntries = [];
                
                // 通知Python端
                if (window.pyqtSignal) {
                    window.pyqtSignal('clear_log_requested');
                } else {
                    document.title = 'SIGNAL:clear_log_requested:' + Date.now();
                }
            }
            
            // 工具函数
            function scrollToBottom() {
                if (logContainer) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            // 性能优化：防抖滚动
            let scrollTimeout;
            function debouncedScrollToBottom() {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(scrollToBottom, 50);
            }
        """
    
    def on_html_ready(self):
        """HTML准备完成回调"""
        print("✅ 优化版修炼日志组件HTML加载完成")
        
        # 设置JavaScript事件监听
        self.setup_javascript_events()
        
        # 更新修炼状态
        self.update_cultivation_status()
        
        # 如果有历史日志，批量添加
        if self.log_entries:
            self.add_logs_batch(self.log_entries[-50:])  # 只显示最近50条
    
    def setup_javascript_events(self):
        """设置JavaScript事件监听"""
        js_code = """
            // 设置全局信号函数
            window.pyqtSignal = function(eventType, data) {
                document.title = 'SIGNAL:' + eventType + ':' + (data || '') + ':' + Date.now();
            };
        """
        
        self.execute_javascript(js_code)
        
        # 监听页面标题变化
        if self.web_view:
            self.web_view.page().titleChanged.connect(self.handle_title_change)
    
    def handle_title_change(self, title: str):
        """处理页面标题变化（用于JavaScript信号）"""
        if title.startswith('SIGNAL:'):
            parts = title.split(':')
            if len(parts) >= 3:
                signal_type = parts[1]
                if signal_type == 'clear_log_requested':
                    self.clear_log_requested.emit()
    
    @profile_operation("cultivation_log_data_update")
    def _apply_data_update(self, data: dict):
        """应用数据更新 - 优化版本"""
        updates = []
        
        # 处理修炼方向变化
        if 'focus' in data and data['focus'] != self.current_cultivation_focus:
            self.current_cultivation_focus = data['focus']
            focus_name = CULTIVATION_FOCUS_TYPES.get(self.current_cultivation_focus, "未知")
            
            js_code = f"updateCultivationStatus('{self.current_cultivation_focus}', '{focus_name}');"
            updates.append(js_code)
        
        # 处理新日志
        if 'logs' in data and data['logs']:
            # 批量添加日志
            self.add_logs_batch(data['logs'])
        
        # 处理倒计时
        if 'next_cultivation_time' in data:
            self.next_cultivation_time = data['next_cultivation_time']
            if self.next_cultivation_time:
                self.start_countdown_timer()
            else:
                self.stop_countdown_timer()
        
        # 批量执行JavaScript更新
        if updates:
            combined_js = '\n'.join(updates)
            self.execute_javascript(combined_js)
    
    @monitor_memory("add_logs_batch")
    def add_logs_batch(self, logs: List[Dict[str, Any]]):
        """批量添加日志 - 性能优化版本"""
        if not logs:
            return
        
        # 限制内存中的日志数量
        self.log_entries.extend(logs)
        if len(self.log_entries) > self.max_log_entries:
            excess = len(self.log_entries) - self.max_log_entries
            self.log_entries = self.log_entries[excess:]
        
        # 转换为JavaScript格式
        js_entries = []
        for log in logs:
            js_entry = {
                'id': log.get('id', f'log_{datetime.now().timestamp()}_{len(js_entries)}'),
                'timestamp': log.get('timestamp', datetime.now().strftime("%H:%M:%S")),
                'message': log.get('message', ''),
                'type': log.get('type', 'info'),
                'color': log.get('color', '#3498db')
            }
            js_entries.append(str(js_entry).replace("'", '"'))
        
        # 批量添加到HTML
        js_code = f"addLogEntriesBatch([{','.join(js_entries)}]);"
        self.execute_javascript(js_code)
    
    def add_log(self, message: str, log_type: str = "info", color: str = "#3498db"):
        """添加单条日志"""
        log_entry = {
            'id': f'log_{datetime.now().timestamp()}_{len(self.log_entries)}',
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'message': message,
            'type': log_type,
            'color': color
        }
        
        self.add_logs_batch([log_entry])
    
    def start_countdown_timer(self):
        """启动倒计时定时器"""
        interval = self.config.get('countdown_update_interval', 1000)
        if not self.countdown_timer.isActive():
            self.countdown_timer.start(interval)
    
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
            
            focus_name = CULTIVATION_FOCUS_TYPES.get(self.current_cultivation_focus, "未知")
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
    
    def update_cultivation_status(self):
        """更新修炼状态显示"""
        focus_name = CULTIVATION_FOCUS_TYPES.get(self.current_cultivation_focus, "未知")
        js_code = f"updateCultivationStatus('{self.current_cultivation_focus}', '{focus_name}');"
        self.execute_javascript(js_code)
    
    def clear_logs(self):
        """清空日志"""
        self.log_entries.clear()
        self.execute_javascript("clearLogs();")
    
    def set_cultivation_focus(self, focus: str):
        """设置修炼方向"""
        if focus != self.current_cultivation_focus:
            self.current_cultivation_focus = focus
            self.update_cultivation_status()
    
    def get_performance_summary(self) -> dict:
        """获取性能摘要"""
        return {
            'log_entries_count': len(self.log_entries),
            'max_log_entries': self.max_log_entries,
            'countdown_active': self.countdown_timer.isActive(),
            'html_loaded': self.html_loaded,
            'performance_config': {
                'enable_data_diff': self.enable_data_diff,
                'enable_batch_updates': self.enable_batch_updates,
                'batch_update_interval': self.batch_update_interval,
            }
        }
