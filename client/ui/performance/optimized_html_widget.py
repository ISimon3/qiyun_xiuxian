# 优化的HTML组件基类
from typing import Dict, Any, Optional, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from .html_cache import html_cache_manager, OptimizedWebEngineView, JavaScriptBridge, performance_monitor

# 尝试导入WebEngine，如果失败则使用备用方案
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None


class OptimizedHTMLWidget(QWidget, OptimizedWebEngineView):
    """优化的HTML组件基类"""
    
    # 信号定义
    html_ready = pyqtSignal()
    update_requested = pyqtSignal(dict)
    
    def __init__(self, template_name: str, parent=None):
        QWidget.__init__(self, parent)
        OptimizedWebEngineView.__init__(self, parent)
        
        self.template_name = template_name
        self.web_view: Optional[QWebEngineView] = None
        self.js_bridge: Optional[JavaScriptBridge] = None
        self.last_data_hash = None
        
        # 性能优化配置
        self.enable_data_diff = True  # 启用数据差异检测
        self.enable_batch_updates = True  # 启用批量更新
        self.enable_lazy_loading = True  # 启用延迟加载
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if WEBENGINE_AVAILABLE:
            self.create_optimized_html_view(layout)
        else:
            self.create_fallback_view(layout)
            
        self.setLayout(layout)
        
    def create_optimized_html_view(self, layout: QVBoxLayout):
        """创建优化的HTML视图"""
        self.web_view = QWebEngineView()
        
        # 禁用右键上下文菜单
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        # 设置基础样式
        self.web_view.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #f8f9fa;
            }
        """)
        
        # 设置JavaScript桥接
        self.js_bridge = JavaScriptBridge(self.web_view)
        self.js_bridge.setup_bridge()
        
        # 设置批量更新
        if self.enable_batch_updates:
            self.setup_batch_updates()
        
        # 连接页面加载完成信号
        self.web_view.loadFinished.connect(self.on_html_load_finished)
        
        # 延迟加载HTML内容
        if self.enable_lazy_loading:
            QTimer.singleShot(50, self.load_html_content)
        else:
            self.load_html_content()
            
        layout.addWidget(self.web_view)
        
    def create_fallback_view(self, layout: QVBoxLayout):
        """创建备用视图"""
        from PyQt6.QtWidgets import QLabel
        
        fallback_label = QLabel("WebEngine不可用，请安装PyQt6-WebEngine")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        layout.addWidget(fallback_label)
        
    def load_html_content(self):
        """加载HTML内容"""
        if not self.web_view:
            return
            
        try:
            # 从缓存获取HTML模板
            html_content = html_cache_manager.get_template(
                self.template_name, 
                self.generate_html_template
            )
            
            performance_monitor.record_html_load()
            self.web_view.setHtml(html_content)
            
        except Exception as e:
            print(f"❌ 加载HTML内容失败: {e}")
            
    def generate_html_template(self) -> str:
        """生成HTML模板 - 子类需要实现"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Default Template</title>
        </head>
        <body>
            <div>请在子类中实现 generate_html_template 方法</div>
        </body>
        </html>
        """
        
    def on_html_load_finished(self, success: bool):
        """HTML页面加载完成回调"""
        if success:
            self.html_loaded = True
            print(f"✅ {self.template_name} HTML页面加载成功")
            
            # 设置JavaScript环境
            self.setup_javascript_environment()
            
            # 发出准备完成信号
            self.html_ready.emit()
            
            # 处理待处理的更新
            if self.enable_batch_updates:
                QTimer.singleShot(100, self._process_pending_updates)
        else:
            print(f"❌ {self.template_name} HTML页面加载失败")
            
    def setup_javascript_environment(self):
        """设置JavaScript环境 - 子类可以重写"""
        pass
        
    def update_data(self, data: dict, force_update: bool = False):
        """更新数据"""
        if not self.web_view or not self.html_loaded:
            if self.enable_batch_updates:
                self.queue_update(data)
            return
            
        # 数据差异检测
        if self.enable_data_diff and not force_update:
            import json
            import hashlib
            
            data_str = json.dumps(data, sort_keys=True)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            
            if data_hash == self.last_data_hash:
                return  # 数据未变化，跳过更新
                
            self.last_data_hash = data_hash
            
        performance_monitor.record_update()
        
        if self.enable_batch_updates:
            self.queue_update(data)
        else:
            self._apply_data_update(data)
            
    def _apply_batch_update(self, data: dict):
        """应用批量更新"""
        self._apply_data_update(data)
        
    def _apply_data_update(self, data: dict):
        """应用数据更新 - 子类需要实现"""
        pass
        
    def execute_javascript(self, js_code: str, callback: Callable = None):
        """执行JavaScript代码"""
        if not self.web_view or not self.html_loaded:
            return
            
        performance_monitor.record_js_call()
        
        if self.js_bridge and self.enable_batch_updates:
            self.js_bridge.queue_call(js_code, callback)
        else:
            if callback is None:
                callback = lambda result: None
            self.web_view.page().runJavaScript(js_code, callback)
            
    def get_cached_resource(self, resource_path: str) -> str:
        """获取缓存的资源"""
        return html_cache_manager.get_image_base64(resource_path)
        
    def clear_template_cache(self):
        """清空模板缓存"""
        html_cache_manager.clear_template_cache(self.template_name)
        
    def reload_html(self):
        """重新加载HTML"""
        self.clear_template_cache()
        self.html_loaded = False
        self.load_html_content()
        
    def set_performance_config(self, **kwargs):
        """设置性能配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def get_performance_metrics(self) -> dict:
        """获取性能指标"""
        return performance_monitor.get_metrics()


class HTMLTemplateBuilder:
    """HTML模板构建器"""
    
    def __init__(self):
        self.template_parts = []
        
    def add_head(self, title: str = "", css: str = "", meta: str = ""):
        """添加HTML头部"""
        head_content = f"""
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {meta}
            <title>{title}</title>
            <style>
                {css}
            </style>
        </head>
        """
        self.template_parts.append(head_content)
        return self
        
    def add_body_start(self, body_class: str = ""):
        """添加body开始标签"""
        self.template_parts.append(f'<body class="{body_class}">')
        return self
        
    def add_content(self, content: str):
        """添加内容"""
        self.template_parts.append(content)
        return self
        
    def add_script(self, script: str):
        """添加JavaScript脚本"""
        self.template_parts.append(f"<script>{script}</script>")
        return self
        
    def add_body_end(self):
        """添加body结束标签"""
        self.template_parts.append("</body>")
        return self
        
    def build(self) -> str:
        """构建完整的HTML模板"""
        html_parts = ["<!DOCTYPE html>", "<html>"]
        html_parts.extend(self.template_parts)
        html_parts.append("</html>")
        return "\n".join(html_parts)
        
    def clear(self):
        """清空模板内容"""
        self.template_parts.clear()
        return self
