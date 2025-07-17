# HTML缓存管理器 - 优化HTML组件性能
import os
import base64
import hashlib
from typing import Dict, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal


class HTMLCacheManager(QObject):
    """HTML缓存管理器，用于缓存HTML模板和资源"""
    
    def __init__(self):
        super().__init__()
        self._template_cache: Dict[str, str] = {}
        self._resource_cache: Dict[str, str] = {}
        self._css_cache: Dict[str, str] = {}
        self._js_cache: Dict[str, str] = {}
        
    def get_template(self, template_name: str, generator_func=None) -> str:
        """获取缓存的HTML模板"""
        if template_name not in self._template_cache:
            if generator_func:
                self._template_cache[template_name] = generator_func()
            else:
                raise ValueError(f"模板 {template_name} 不存在且未提供生成函数")
        return self._template_cache[template_name]
    
    def get_image_base64(self, image_path: str) -> str:
        """获取缓存的图片base64数据"""
        if image_path not in self._resource_cache:
            try:
                if os.path.exists(image_path):
                    with open(image_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        self._resource_cache[image_path] = encoded_string
                else:
                    print(f"⚠️ 图片不存在: {image_path}")
                    self._resource_cache[image_path] = ""
            except Exception as e:
                print(f"❌ 获取图片失败: {e}")
                self._resource_cache[image_path] = ""
        
        return self._resource_cache[image_path]
    
    def get_css(self, css_name: str, generator_func=None) -> str:
        """获取缓存的CSS样式"""
        if css_name not in self._css_cache:
            if generator_func:
                self._css_cache[css_name] = generator_func()
            else:
                raise ValueError(f"CSS {css_name} 不存在且未提供生成函数")
        return self._css_cache[css_name]
    
    def get_javascript(self, js_name: str, generator_func=None) -> str:
        """获取缓存的JavaScript代码"""
        if js_name not in self._js_cache:
            if generator_func:
                self._js_cache[js_name] = generator_func()
            else:
                raise ValueError(f"JavaScript {js_name} 不存在且未提供生成函数")
        return self._js_cache[js_name]
    
    def clear_cache(self):
        """清空所有缓存"""
        self._template_cache.clear()
        self._resource_cache.clear()
        self._css_cache.clear()
        self._js_cache.clear()
    
    def clear_template_cache(self, template_name: str = None):
        """清空指定模板缓存"""
        if template_name:
            self._template_cache.pop(template_name, None)
        else:
            self._template_cache.clear()


# 全局缓存管理器实例
html_cache_manager = HTMLCacheManager()


class OptimizedWebEngineView(QObject):
    """优化的WebEngine视图基类"""
    
    # 信号定义
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.html_loaded = False
        self.pending_updates = []
        self.update_timer = None
        self.batch_update_interval = 100  # 批量更新间隔(ms)
        
    def setup_batch_updates(self):
        """设置批量更新机制"""
        from PyQt6.QtCore import QTimer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_updates)
        self.update_timer.setSingleShot(True)
        
    def queue_update(self, update_data: dict):
        """将更新加入队列"""
        self.pending_updates.append(update_data)
        if self.update_timer and not self.update_timer.isActive():
            self.update_timer.start(self.batch_update_interval)
    
    def _process_pending_updates(self):
        """处理待处理的更新"""
        if not self.pending_updates or not self.html_loaded:
            return
            
        # 合并更新数据
        merged_data = {}
        for update in self.pending_updates:
            merged_data.update(update)
        
        # 清空待处理队列
        self.pending_updates.clear()
        
        # 执行批量更新
        self._apply_batch_update(merged_data)
    
    def _apply_batch_update(self, data: dict):
        """应用批量更新 - 子类需要实现"""
        pass
    
    def optimize_javascript_call(self, js_code: str, callback=None):
        """优化的JavaScript调用"""
        if not hasattr(self, 'web_view') or not self.html_loaded:
            return
            
        # 使用异步调用避免阻塞UI
        if callback is None:
            callback = lambda result: None
            
        self.web_view.page().runJavaScript(js_code, callback)


class JavaScriptBridge(QObject):
    """JavaScript桥接优化器"""
    
    def __init__(self, web_view):
        super().__init__()
        self.web_view = web_view
        self.pending_calls = []
        self.call_timer = None
        self.batch_interval = 50  # 批量调用间隔(ms)
        
    def setup_bridge(self):
        """设置JavaScript桥接"""
        from PyQt6.QtCore import QTimer
        self.call_timer = QTimer()
        self.call_timer.timeout.connect(self._process_pending_calls)
        self.call_timer.setSingleShot(True)
        
    def queue_call(self, js_code: str, callback=None):
        """将JavaScript调用加入队列"""
        self.pending_calls.append({
            'code': js_code,
            'callback': callback or (lambda result: None)
        })
        
        if self.call_timer and not self.call_timer.isActive():
            self.call_timer.start(self.batch_interval)
    
    def _process_pending_calls(self):
        """处理待处理的JavaScript调用"""
        if not self.pending_calls:
            return
            
        # 合并JavaScript代码
        combined_code = []
        callbacks = []
        
        for call in self.pending_calls:
            combined_code.append(call['code'])
            callbacks.append(call['callback'])
        
        # 清空待处理队列
        self.pending_calls.clear()
        
        # 执行合并的JavaScript代码
        final_code = ';\n'.join(combined_code)
        
        def combined_callback(result):
            # 调用所有回调函数
            for callback in callbacks:
                try:
                    callback(result)
                except Exception as e:
                    print(f"JavaScript回调执行失败: {e}")
        
        self.web_view.page().runJavaScript(final_code, combined_callback)


class PerformanceMonitor(QObject):
    """性能监控器"""
    
    def __init__(self):
        super().__init__()
        self.metrics = {
            'html_loads': 0,
            'js_calls': 0,
            'update_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
    def record_html_load(self):
        """记录HTML加载"""
        self.metrics['html_loads'] += 1
        
    def record_js_call(self):
        """记录JavaScript调用"""
        self.metrics['js_calls'] += 1
        
    def record_update(self):
        """记录更新调用"""
        self.metrics['update_calls'] += 1
        
    def record_cache_hit(self):
        """记录缓存命中"""
        self.metrics['cache_hits'] += 1
        
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.metrics['cache_misses'] += 1
        
    def get_metrics(self) -> dict:
        """获取性能指标"""
        return self.metrics.copy()
        
    def reset_metrics(self):
        """重置性能指标"""
        for key in self.metrics:
            self.metrics[key] = 0


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
