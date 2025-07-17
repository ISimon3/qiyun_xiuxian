# HTML组件性能优化模块
"""
HTML组件性能优化模块

提供以下功能:
1. HTML模板缓存管理
2. 批量更新机制
3. JavaScript调用优化
4. 数据差异检测
5. 性能监控和分析

主要类:
- HTMLCacheManager: HTML缓存管理器
- OptimizedHTMLWidget: 优化的HTML组件基类
- JavaScriptBridge: JavaScript桥接优化器
- PerformanceConfig: 性能配置管理
- PerformanceProfiler: 性能分析器
- MemoryMonitor: 内存监控器

使用示例:
    from client.ui.performance import OptimizedHTMLWidget, PerformanceConfig
    
    class MyWidget(OptimizedHTMLWidget):
        def __init__(self):
            super().__init__("my_template")
            
        def generate_html_template(self):
            return "<html>...</html>"
"""

from .html_cache import (
    HTMLCacheManager,
    OptimizedWebEngineView,
    JavaScriptBridge,
    PerformanceMonitor,
    html_cache_manager,
    performance_monitor
)

from .optimized_html_widget import (
    OptimizedHTMLWidget,
    HTMLTemplateBuilder
)

from .performance_config import (
    PerformanceConfig,
    PerformanceProfiler,
    MemoryMonitor,
    performance_profiler,
    memory_monitor,
    profile_operation,
    monitor_memory
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Qiyun Xiuxian Team"

# 导出的公共接口
__all__ = [
    # 缓存管理
    'HTMLCacheManager',
    'html_cache_manager',
    
    # 优化组件
    'OptimizedHTMLWidget',
    'OptimizedWebEngineView',
    'HTMLTemplateBuilder',
    
    # JavaScript优化
    'JavaScriptBridge',
    
    # 性能配置
    'PerformanceConfig',
    
    # 性能监控
    'PerformanceProfiler',
    'PerformanceMonitor',
    'MemoryMonitor',
    'performance_profiler',
    'performance_monitor',
    'memory_monitor',
    
    # 装饰器
    'profile_operation',
    'monitor_memory',
]


def initialize_performance_system():
    """初始化性能优化系统"""
    print("🚀 初始化HTML组件性能优化系统...")
    
    # 设置默认配置
    PerformanceConfig.update_config({
        'ENABLE_HTML_CACHE': True,
        'ENABLE_BATCH_UPDATES': True,
        'ENABLE_DATA_DIFF': True,
        'ENABLE_LAZY_LOADING': True,
        'ENABLE_JS_BATCHING': True,
    })
    
    # 启动性能监控
    if PerformanceConfig.MONITORING_CONFIG['enable_performance_logging']:
        print("📊 性能监控已启用")
        
    # 启动内存监控
    if PerformanceConfig.MEMORY_CONFIG['auto_gc_enabled']:
        print("🧹 自动内存管理已启用")
        
    print("✅ 性能优化系统初始化完成")


def get_optimization_summary():
    """获取优化效果摘要"""
    metrics = performance_profiler.get_metrics()
    memory_info = memory_monitor.get_memory_usage()
    
    summary = {
        'performance_metrics': metrics,
        'memory_usage': memory_info,
        'cache_stats': {
            'template_cache_size': len(html_cache_manager._template_cache),
            'resource_cache_size': len(html_cache_manager._resource_cache),
            'css_cache_size': len(html_cache_manager._css_cache),
            'js_cache_size': len(html_cache_manager._js_cache),
        },
        'config': PerformanceConfig.get_all_config()
    }
    
    return summary


def cleanup_performance_system():
    """清理性能优化系统"""
    print("🧹 清理性能优化系统...")
    
    # 清理缓存
    html_cache_manager.clear_cache()
    
    # 重置性能指标
    performance_profiler.reset_metrics()
    
    # 清理内存快照
    memory_monitor.memory_snapshots.clear()
    
    print("✅ 性能优化系统清理完成")


# 自动初始化
try:
    initialize_performance_system()
except Exception as e:
    print(f"⚠️ 性能优化系统初始化失败: {e}")
