# HTML组件性能优化配置
from typing import Dict, Any


class PerformanceConfig:
    """性能优化配置"""
    
    # 全局性能开关
    ENABLE_HTML_CACHE = True  # 启用HTML缓存
    ENABLE_BATCH_UPDATES = True  # 启用批量更新
    ENABLE_DATA_DIFF = True  # 启用数据差异检测
    ENABLE_LAZY_LOADING = True  # 启用延迟加载
    ENABLE_JS_BATCHING = True  # 启用JavaScript批处理
    
    # 缓存配置
    CACHE_CONFIG = {
        'max_template_cache_size': 50,  # 最大模板缓存数量
        'max_resource_cache_size': 100,  # 最大资源缓存数量
        'cache_expiry_time': 3600,  # 缓存过期时间(秒)
        'auto_cleanup_interval': 300,  # 自动清理间隔(秒)
    }
    
    # 批量更新配置
    BATCH_UPDATE_CONFIG = {
        'batch_interval': 100,  # 批量更新间隔(ms)
        'max_batch_size': 10,  # 最大批量大小
        'force_update_threshold': 1000,  # 强制更新阈值(ms)
    }
    
    # JavaScript优化配置
    JS_CONFIG = {
        'batch_interval': 50,  # JavaScript批处理间隔(ms)
        'max_batch_calls': 20,  # 最大批处理调用数
        'async_callback': True,  # 使用异步回调
        'error_retry_count': 3,  # 错误重试次数
    }
    
    # 组件特定配置
    COMPONENT_CONFIG = {
        'cultivation_log': {
            'max_log_entries': 100,
            'countdown_update_interval': 1000,
            'batch_log_threshold': 5,
        },
        'chat_channel': {
            'max_message_history': 200,
            'message_batch_size': 10,
            'auto_scroll_threshold': 50,
        },
        'upper_area': {
            'pentagon_update_interval': 500,
            'attribute_diff_threshold': 0.01,
            'icon_cache_enabled': True,
        },
        'cave_window': {
            'data_update_interval': 2000,
            'image_lazy_loading': True,
            'animation_enabled': False,
        },
        'backpack_window': {
            'item_render_batch_size': 20,
            'equipment_update_debounce': 200,
            'tooltip_delay': 300,
        },
        'daily_sign': {
            'calendar_render_optimization': True,
            'date_calculation_cache': True,
            'animation_duration': 200,
        }
    }
    
    # 性能监控配置
    MONITORING_CONFIG = {
        'enable_performance_logging': True,
        'log_slow_operations': True,
        'slow_operation_threshold': 100,  # 慢操作阈值(ms)
        'memory_usage_tracking': True,
        'metrics_collection_interval': 5000,  # 指标收集间隔(ms)
    }
    
    # 内存管理配置
    MEMORY_CONFIG = {
        'auto_gc_enabled': True,
        'gc_threshold': 100,  # GC触发阈值(MB)
        'max_memory_usage': 500,  # 最大内存使用(MB)
        'cleanup_interval': 30000,  # 清理间隔(ms)
    }
    
    @classmethod
    def get_component_config(cls, component_name: str) -> Dict[str, Any]:
        """获取组件特定配置"""
        return cls.COMPONENT_CONFIG.get(component_name, {})
    
    @classmethod
    def update_config(cls, config_dict: Dict[str, Any]):
        """更新配置"""
        for key, value in config_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'global': {
                'enable_html_cache': cls.ENABLE_HTML_CACHE,
                'enable_batch_updates': cls.ENABLE_BATCH_UPDATES,
                'enable_data_diff': cls.ENABLE_DATA_DIFF,
                'enable_lazy_loading': cls.ENABLE_LAZY_LOADING,
                'enable_js_batching': cls.ENABLE_JS_BATCHING,
            },
            'cache': cls.CACHE_CONFIG,
            'batch_update': cls.BATCH_UPDATE_CONFIG,
            'javascript': cls.JS_CONFIG,
            'components': cls.COMPONENT_CONFIG,
            'monitoring': cls.MONITORING_CONFIG,
            'memory': cls.MEMORY_CONFIG,
        }


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        
    def start_timing(self, operation_name: str):
        """开始计时"""
        import time
        self.start_times[operation_name] = time.time()
        
    def end_timing(self, operation_name: str):
        """结束计时"""
        import time
        if operation_name in self.start_times:
            duration = (time.time() - self.start_times[operation_name]) * 1000
            
            if operation_name not in self.metrics:
                self.metrics[operation_name] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf')
                }
            
            metric = self.metrics[operation_name]
            metric['count'] += 1
            metric['total_time'] += duration
            metric['avg_time'] = metric['total_time'] / metric['count']
            metric['max_time'] = max(metric['max_time'], duration)
            metric['min_time'] = min(metric['min_time'], duration)
            
            # 记录慢操作
            if (PerformanceConfig.MONITORING_CONFIG['log_slow_operations'] and 
                duration > PerformanceConfig.MONITORING_CONFIG['slow_operation_threshold']):
                print(f"⚠️ 慢操作检测: {operation_name} 耗时 {duration:.2f}ms")
            
            del self.start_times[operation_name]
            return duration
        return 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """重置性能指标"""
        self.metrics.clear()
        self.start_times.clear()
    
    def print_report(self):
        """打印性能报告"""
        print("\n=== 性能分析报告 ===")
        for operation, metric in self.metrics.items():
            print(f"{operation}:")
            print(f"  调用次数: {metric['count']}")
            print(f"  总耗时: {metric['total_time']:.2f}ms")
            print(f"  平均耗时: {metric['avg_time']:.2f}ms")
            print(f"  最大耗时: {metric['max_time']:.2f}ms")
            print(f"  最小耗时: {metric['min_time']:.2f}ms")
            print()


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self):
        self.memory_snapshots = []
        
    def take_snapshot(self, label: str = ""):
        """获取内存快照"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            snapshot = {
                'label': label,
                'timestamp': datetime.now(),
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
            
            self.memory_snapshots.append(snapshot)
            
            # 检查内存使用是否超过阈值
            if snapshot['rss'] > PerformanceConfig.MEMORY_CONFIG['max_memory_usage']:
                print(f"⚠️ 内存使用超过阈值: {snapshot['rss']:.2f}MB")
                
            return snapshot
            
        except ImportError:
            print("⚠️ psutil未安装，无法监控内存使用")
            return None
        except Exception as e:
            print(f"❌ 内存监控失败: {e}")
            return None
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况"""
        snapshot = self.take_snapshot()
        if snapshot:
            return {
                'rss_mb': snapshot['rss'],
                'vms_mb': snapshot['vms'],
                'percent': snapshot['percent']
            }
        return {}
    
    def print_memory_report(self):
        """打印内存使用报告"""
        if not self.memory_snapshots:
            print("没有内存快照数据")
            return
            
        print("\n=== 内存使用报告 ===")
        for snapshot in self.memory_snapshots[-10:]:  # 显示最近10个快照
            print(f"{snapshot['timestamp'].strftime('%H:%M:%S')} [{snapshot['label']}]: "
                  f"RSS={snapshot['rss']:.2f}MB, VMS={snapshot['vms']:.2f}MB, "
                  f"使用率={snapshot['percent']:.1f}%")


# 全局实例
performance_profiler = PerformanceProfiler()
memory_monitor = MemoryMonitor()


def profile_operation(operation_name: str):
    """性能分析装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            performance_profiler.start_timing(operation_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                performance_profiler.end_timing(operation_name)
        return wrapper
    return decorator


def monitor_memory(label: str = ""):
    """内存监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            memory_monitor.take_snapshot(f"{label}_before")
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                memory_monitor.take_snapshot(f"{label}_after")
        return wrapper
    return decorator
