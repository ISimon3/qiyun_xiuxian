# 客户端主程序入口

import sys
import os
import traceback
from typing import Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 检查PyQt6是否可用
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QIcon
    PYQT_AVAILABLE = True
except ImportError as e:
    PYQT_AVAILABLE = False
    PYQT_ERROR = str(e)

if not PYQT_AVAILABLE:
    print("❌ PyQt6导入失败!")
    print(f"错误信息: {PYQT_ERROR}")
    print("\n🔧 解决方案:")
    print("1. 重新安装PyQt6: pip uninstall PyQt6 && pip install PyQt6")
    print("2. 如果是DLL错误，尝试安装Visual C++运行库")
    print("3. 或者尝试安装PyQt5: pip install PyQt5")
    print("4. 运行诊断工具: python fix_pyqt.py")
    sys.exit(1)

from client.ui.login_window import LoginWindow
from client.ui.main_window import MainWindow
from client.state_manager import init_state_manager, get_state_manager
from client.network.api_client import GameAPIClient


class GameApplication:
    """游戏应用程序主类"""
    
    def __init__(self):
        # 初始化Qt应用程序
        self.app = QApplication(sys.argv)
        self.setup_application()
        
        # 初始化组件
        self.state_manager = init_state_manager()
        self.api_client: Optional[GameAPIClient] = None
        
        # 窗口管理
        self.login_window: Optional[LoginWindow] = None
        self.main_window: Optional[MainWindow] = None  # 主游戏窗口
        
        # 设置异常处理
        self.setup_exception_handling()
        
        # 连接状态管理器信号
        self.setup_state_connections()

        # 连接应用程序退出信号
        self.app.aboutToQuit.connect(self.cleanup_before_quit)
    
    def setup_application(self):
        """设置应用程序基本信息"""
        self.app.setApplicationName("气运修仙")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("气运修仙工作室")
        self.app.setOrganizationDomain("qiyun-xiuxian.com")
        
        # 设置应用程序图标（如果存在）
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        # 设置样式
        self.setup_styles()
    
    def setup_styles(self):
        """设置应用程序样式"""
        # 基础样式
        style = """
        QWidget {
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            font-size: 12px;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QLineEdit {
            border: 2px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
        }
        
        QLineEdit:focus {
            border-color: #4CAF50;
        }
        
        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #4CAF50;
        }
        
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        """
        
        self.app.setStyleSheet(style)
    
    def setup_exception_handling(self):
        """设置全局异常处理"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            """全局异常处理器"""
            if issubclass(exc_type, KeyboardInterrupt):
                # 允许Ctrl+C中断
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # 记录异常信息
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            print(f"未处理的异常:\n{error_msg}")
            
            # 显示错误对话框
            try:
                QMessageBox.critical(
                    None,
                    "程序错误",
                    f"程序遇到未处理的错误:\n\n{str(exc_value)}\n\n"
                    f"错误类型: {exc_type.__name__}\n\n"
                    f"请联系开发者报告此问题。"
                )
            except:
                pass  # 如果连错误对话框都无法显示，就静默处理
        
        # 设置异常钩子
        sys.excepthook = handle_exception
    
    def setup_state_connections(self):
        """设置状态管理器信号连接"""
        self.state_manager.user_logged_in.connect(self.on_user_logged_in)
        self.state_manager.user_logged_out.connect(self.on_user_logged_out)
    
    def run(self):
        """运行应用程序"""
        try:
            print("🎮 正在启动气运修仙客户端...")
            
            # 检查是否已有登录状态
            if self.state_manager.is_logged_in and not self.state_manager.is_token_expired():
                print(f"✅ 检测到已登录用户: {self.state_manager.user_info.get('username')}")
                # 直接进入主界面
                self.show_main_window()
            else:
                print("📝 显示登录窗口")
                # 显示登录窗口
                self.show_login_window()
            
            # 启动事件循环
            return self.app.exec()
            
        except Exception as e:
            print(f"❌ 应用程序启动失败: {e}")
            traceback.print_exc()
            return 1

    def show_login_window(self):
        """显示登录窗口"""
        if self.login_window is None:
            server_url = self.state_manager.server_url
            self.login_window = LoginWindow(server_url)
            self.login_window.login_success.connect(self.on_login_success)

        self.login_window.show()
        self.login_window.raise_()
        self.login_window.activateWindow()

    def show_main_window(self):
        """显示主游戏窗口"""
        # 确保用户已登录且token有效
        if not self.state_manager.is_logged_in or self.state_manager.is_token_expired():
            print("⚠️ 用户未登录或token已过期，显示登录窗口")
            self.show_login_window()
            return

        # 初始化或更新API客户端
        if self.api_client is None:
            self.api_client = GameAPIClient(self.state_manager.server_url)

        # 确保API客户端有最新的token
        if self.state_manager.access_token:
            self.api_client.set_token(self.state_manager.access_token)
            print(f"✅ API客户端token已设置")
        else:
            print("❌ 未找到访问token，显示登录窗口")
            self.show_login_window()
            return

        if self.main_window is None:
            server_url = self.state_manager.server_url
            self.main_window = MainWindow(server_url)

            # 连接主窗口信号
            self.main_window.destroyed.connect(self.on_main_window_closed)

        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

        # 隐藏登录窗口
        if self.login_window:
            self.login_window.hide()

    def on_main_window_closed(self):
        """主窗口关闭处理"""
        print("📊 主窗口已关闭")
        self.main_window = None

        # 检查是否还有登录状态，如果没有则显示登录窗口
        if not self.state_manager.is_logged_in:
            print("🔐 用户已登出，显示登录窗口")
            self.show_login_window()
        else:
            # 用户主动关闭主窗口时退出应用程序
            print("🚪 退出应用程序")
            self.app.quit()

    def cleanup_before_quit(self):
        """应用程序退出前的清理工作"""
        print("🧹 执行退出前清理...")

        try:
            # 清理主窗口
            if self.main_window:
                print("🔄 清理主窗口...")
                # 主窗口的closeEvent会处理线程停止
                self.main_window = None

            # 清理登录窗口
            if self.login_window:
                print("🔄 清理登录窗口...")
                self.login_window = None

            print("✅ 清理完成")

        except Exception as e:
            print(f"❌ 清理时发生错误: {e}")

    def on_login_success(self, user_info: dict):
        """登录成功处理"""
        print(f"✅ 用户登录成功: {user_info.get('username')}")

        # 隐藏登录窗口
        if self.login_window:
            self.login_window.hide()

        # 显示主窗口
        self.show_main_window()

    def on_user_logged_in(self, user_info: dict):
        """用户登录状态变更处理"""
        print(f"📊 状态管理器: 用户已登录 - {user_info.get('username')}")

        # 初始化API客户端
        if self.api_client is None:
            self.api_client = GameAPIClient(self.state_manager.server_url)
            print("🔧 API客户端已初始化")

        # 设置访问令牌
        if self.state_manager.access_token:
            self.api_client.set_token(self.state_manager.access_token)
            print(f"🔑 API客户端token已设置: {self.state_manager.access_token[:20]}...")
        else:
            print("❌ 警告: 状态管理器中没有访问令牌")

    def on_user_logged_out(self):
        """用户登出状态变更处理"""
        print("📊 状态管理器: 用户已登出")

        # 清除API客户端令牌
        if self.api_client:
            self.api_client.clear_token()

        # 关闭主窗口，显示登录窗口
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.show_login_window()

    def cleanup(self):
        """清理资源"""
        print("🧹 正在清理应用程序资源...")

        # 关闭所有窗口
        if self.login_window:
            self.login_window.close()

        if self.main_window:
            self.main_window.close()

        # 保存状态
        if self.state_manager:
            self.state_manager.save_config()


def main():
    """主函数"""
    try:
        print("=" * 50)
        print("🎮 气运修仙 - 客户端启动器")
        print("=" * 50)

        # 创建应用程序实例
        game_app = GameApplication()

        # 运行应用程序
        exit_code = game_app.run()

        # 清理资源
        game_app.cleanup()

        print("👋 客户端已退出")
        return exit_code

    except Exception as e:
        print(f"❌ 应用程序运行失败: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
