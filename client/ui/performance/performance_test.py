# HTML组件性能测试脚本
"""
性能测试脚本，用于对比优化前后的性能差异

测试项目:
1. HTML加载时间
2. 数据更新延迟
3. JavaScript执行时间
4. 内存使用情况
5. 批量操作性能

使用方法:
    python performance_test.py
"""

import sys
import time
import random
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal

# 导入优化组件
from client.ui.performance import (
    OptimizedHTMLWidget,
    PerformanceConfig,
    performance_profiler,
    memory_monitor,
    profile_operation,
    monitor_memory
)

# 导入原始组件进行对比
try:
    from client.ui.widgets.cultivation_log_widget import CultivationLogWidget as OriginalWidget
    ORIGINAL_AVAILABLE = True
except ImportError:
    ORIGINAL_AVAILABLE = False
    print("⚠️ 原始组件不可用，跳过对比测试")

from client.ui.performance.migration_example import MigratedCultivationLogWidget as OptimizedWidget


class PerformanceTestWindow(QMainWindow):
    """性能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML组件性能测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 测试组件
        self.original_widget = None
        self.optimized_widget = None
        
        # 测试数据
        self.test_logs = self.generate_test_logs(1000)
        self.test_running = False
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("HTML组件性能测试")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 测试按钮
        self.create_test_buttons(layout)
        
        # 结果显示
        self.result_label = QLabel("点击测试按钮开始性能测试...")
        self.result_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.result_label)
        
        # 创建测试组件
        self.create_test_widgets(layout)
        
        central_widget.setLayout(layout)
        
    def create_test_buttons(self, layout):
        """创建测试按钮"""
        button_layout = QVBoxLayout()
        
        # 基础性能测试
        basic_test_btn = QPushButton("基础性能测试")
        basic_test_btn.clicked.connect(self.run_basic_performance_test)
        button_layout.addWidget(basic_test_btn)
        
        # 批量操作测试
        batch_test_btn = QPushButton("批量操作测试")
        batch_test_btn.clicked.connect(self.run_batch_operation_test)
        button_layout.addWidget(batch_test_btn)
        
        # 内存使用测试
        memory_test_btn = QPushButton("内存使用测试")
        memory_test_btn.clicked.connect(self.run_memory_test)
        button_layout.addWidget(memory_test_btn)
        
        # 压力测试
        stress_test_btn = QPushButton("压力测试")
        stress_test_btn.clicked.connect(self.run_stress_test)
        button_layout.addWidget(stress_test_btn)
        
        # 清理测试
        cleanup_btn = QPushButton("清理并重置")
        cleanup_btn.clicked.connect(self.cleanup_test)
        button_layout.addWidget(cleanup_btn)
        
        layout.addLayout(button_layout)
        
    def create_test_widgets(self, layout):
        """创建测试组件"""
        # 优化版组件
        self.optimized_widget = OptimizedWidget()
        layout.addWidget(QLabel("优化版组件:"))
        layout.addWidget(self.optimized_widget)
        
        # 原始组件（如果可用）
        if ORIGINAL_AVAILABLE:
            self.original_widget = OriginalWidget()
            layout.addWidget(QLabel("原始组件:"))
            layout.addWidget(self.original_widget)
        
    def generate_test_logs(self, count: int) -> List[Dict[str, Any]]:
        """生成测试日志数据"""
        logs = []
        log_types = ['info', 'success', 'warning', 'error']
        
        for i in range(count):
            log = {
                'id': f'test_log_{i}',
                'timestamp': (datetime.now() - timedelta(seconds=count-i)).strftime("%H:%M:%S"),
                'message': f'测试日志消息 {i+1} - 这是一条用于性能测试的日志消息',
                'type': random.choice(log_types),
                'color': '#3498db'
            }
            logs.append(log)
            
        return logs
    
    @profile_operation("basic_performance_test")
    @monitor_memory("basic_test")
    def run_basic_performance_test(self):
        """运行基础性能测试"""
        if self.test_running:
            return
            
        self.test_running = True
        self.result_label.setText("正在运行基础性能测试...")
        
        results = {}
        
        # 测试HTML加载时间
        results['html_load'] = self.test_html_load_time()
        
        # 测试数据更新时间
        results['data_update'] = self.test_data_update_time()
        
        # 测试JavaScript执行时间
        results['js_execution'] = self.test_javascript_execution_time()
        
        # 显示结果
        self.display_test_results("基础性能测试", results)
        self.test_running = False
    
    def test_html_load_time(self) -> Dict[str, float]:
        """测试HTML加载时间"""
        results = {}
        
        # 测试优化版组件
        start_time = time.time()
        optimized_widget = OptimizedWidget()
        optimized_widget.show()
        
        # 等待HTML加载完成
        while not optimized_widget.html_loaded:
            QApplication.processEvents()
            time.sleep(0.01)
            
        results['optimized'] = (time.time() - start_time) * 1000
        optimized_widget.close()
        
        # 测试原始组件（如果可用）
        if ORIGINAL_AVAILABLE:
            start_time = time.time()
            original_widget = OriginalWidget()
            original_widget.show()
            
            # 等待一段时间模拟加载
            time.sleep(0.1)
            
            results['original'] = (time.time() - start_time) * 1000
            original_widget.close()
        
        return results
    
    def test_data_update_time(self) -> Dict[str, float]:
        """测试数据更新时间"""
        results = {}
        
        # 准备测试数据
        test_data = {
            'focus': 'ATK',
            'logs': self.test_logs[:10]  # 使用前10条日志
        }
        
        # 测试优化版组件
        if self.optimized_widget:
            start_time = time.time()
            self.optimized_widget.update_data(test_data)
            QApplication.processEvents()
            results['optimized'] = (time.time() - start_time) * 1000
        
        # 测试原始组件（如果可用）
        if ORIGINAL_AVAILABLE and self.original_widget:
            start_time = time.time()
            # 模拟原始组件的更新方式
            for log in test_data['logs']:
                self.original_widget.add_log(log['message'], log['type'])
            QApplication.processEvents()
            results['original'] = (time.time() - start_time) * 1000
        
        return results
    
    def test_javascript_execution_time(self) -> Dict[str, float]:
        """测试JavaScript执行时间"""
        results = {}
        
        # 测试优化版组件
        if self.optimized_widget and self.optimized_widget.html_loaded:
            start_time = time.time()
            
            # 执行多个JavaScript操作
            for i in range(10):
                js_code = f"console.log('测试JavaScript执行 {i}');"
                self.optimized_widget.execute_javascript(js_code)
            
            QApplication.processEvents()
            results['optimized'] = (time.time() - start_time) * 1000
        
        return results
    
    @monitor_memory("batch_operation_test")
    def run_batch_operation_test(self):
        """运行批量操作测试"""
        if self.test_running:
            return
            
        self.test_running = True
        self.result_label.setText("正在运行批量操作测试...")
        
        results = {}
        
        # 测试批量添加日志
        batch_sizes = [10, 50, 100, 500]
        
        for batch_size in batch_sizes:
            test_logs = self.test_logs[:batch_size]
            
            # 测试优化版组件
            if self.optimized_widget:
                start_time = time.time()
                self.optimized_widget.add_logs_batch(test_logs)
                QApplication.processEvents()
                optimized_time = (time.time() - start_time) * 1000
                
                results[f'optimized_batch_{batch_size}'] = optimized_time
            
            # 测试原始组件（如果可用）
            if ORIGINAL_AVAILABLE and self.original_widget:
                start_time = time.time()
                for log in test_logs:
                    self.original_widget.add_log(log['message'], log['type'])
                QApplication.processEvents()
                original_time = (time.time() - start_time) * 1000
                
                results[f'original_batch_{batch_size}'] = original_time
        
        self.display_test_results("批量操作测试", results)
        self.test_running = False
    
    def run_memory_test(self):
        """运行内存使用测试"""
        if self.test_running:
            return
            
        self.test_running = True
        self.result_label.setText("正在运行内存使用测试...")
        
        # 记录初始内存
        initial_memory = memory_monitor.take_snapshot("test_start")
        
        # 执行大量操作
        for i in range(100):
            test_data = {
                'logs': [self.test_logs[i % len(self.test_logs)]]
            }
            
            if self.optimized_widget:
                self.optimized_widget.update_data(test_data)
            
            if i % 10 == 0:
                QApplication.processEvents()
        
        # 记录结束内存
        final_memory = memory_monitor.take_snapshot("test_end")
        
        # 计算内存增长
        if initial_memory and final_memory:
            memory_growth = final_memory['rss'] - initial_memory['rss']
            result_text = f"内存使用测试完成\n初始内存: {initial_memory['rss']:.2f}MB\n结束内存: {final_memory['rss']:.2f}MB\n内存增长: {memory_growth:.2f}MB"
        else:
            result_text = "内存监控不可用"
        
        self.result_label.setText(result_text)
        self.test_running = False
    
    def run_stress_test(self):
        """运行压力测试"""
        if self.test_running:
            return
            
        self.test_running = True
        self.result_label.setText("正在运行压力测试...")
        
        # 创建多个线程同时更新数据
        def stress_worker():
            for i in range(50):
                test_data = {
                    'logs': [random.choice(self.test_logs)]
                }
                
                if self.optimized_widget:
                    self.optimized_widget.update_data(test_data)
                
                time.sleep(0.01)
        
        # 启动多个线程
        threads = []
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=stress_worker)
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        result_text = f"压力测试完成\n总耗时: {(end_time - start_time) * 1000:.2f}ms\n线程数: 5\n每线程操作数: 50"
        self.result_label.setText(result_text)
        self.test_running = False
    
    def cleanup_test(self):
        """清理测试"""
        # 清理组件
        if self.optimized_widget:
            self.optimized_widget.clear_logs()
        
        if self.original_widget:
            self.original_widget.clear_logs()
        
        # 重置性能监控
        performance_profiler.reset_metrics()
        memory_monitor.memory_snapshots.clear()
        
        # 清理缓存
        from client.ui.performance.html_cache import html_cache_manager
        html_cache_manager.clear_cache()
        
        self.result_label.setText("清理完成，可以重新开始测试")
    
    def display_test_results(self, test_name: str, results: Dict[str, float]):
        """显示测试结果"""
        result_text = f"{test_name}结果:\n\n"
        
        for key, value in results.items():
            result_text += f"{key}: {value:.2f}ms\n"
        
        # 添加性能指标
        metrics = performance_profiler.get_metrics()
        if metrics:
            result_text += "\n性能指标:\n"
            for operation, metric in metrics.items():
                result_text += f"{operation}: 平均{metric['avg_time']:.2f}ms (调用{metric['count']}次)\n"
        
        self.result_label.setText(result_text)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置性能配置
    PerformanceConfig.update_config({
        'MONITORING_CONFIG': {
            'enable_performance_logging': True,
            'log_slow_operations': True,
            'slow_operation_threshold': 50,
        }
    })
    
    # 创建测试窗口
    window = PerformanceTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
