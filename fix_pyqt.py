# PyQt6问题诊断和修复工具

import sys
import os
import subprocess
import platform

def check_python_version():
    """检查Python版本"""
    print(f"🐍 Python版本: {sys.version}")
    if sys.version_info < (3, 8):
        print("⚠️  警告: PyQt6需要Python 3.8或更高版本")
        return False
    return True

def check_system_info():
    """检查系统信息"""
    print(f"💻 操作系统: {platform.system()} {platform.release()}")
    print(f"🏗️  架构: {platform.architecture()[0]}")
    
def test_pyqt_import():
    """测试PyQt导入"""
    print("\n🔍 测试PyQt6导入...")
    
    try:
        import PyQt6
        print("✅ PyQt6基础模块导入成功")
    except ImportError as e:
        print(f"❌ PyQt6基础模块导入失败: {e}")
        return False
    
    try:
        from PyQt6 import QtCore
        print(f"✅ QtCore导入成功，版本: {QtCore.PYQT_VERSION_STR}")
    except ImportError as e:
        print(f"❌ QtCore导入失败: {e}")
        return False
    
    try:
        from PyQt6 import QtWidgets
        print("✅ QtWidgets导入成功")
    except ImportError as e:
        print(f"❌ QtWidgets导入失败: {e}")
        return False
    
    try:
        from PyQt6 import QtGui
        print("✅ QtGui导入成功")
    except ImportError as e:
        print(f"❌ QtGui导入失败: {e}")
        return False
    
    return True

def test_simple_app():
    """测试简单的PyQt应用"""
    print("\n🧪 测试简单PyQt应用...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QLabel
        
        app = QApplication([])
        label = QLabel("测试")
        print("✅ 简单应用创建成功")
        app.quit()
        return True
    except Exception as e:
        print(f"❌ 简单应用创建失败: {e}")
        return False

def get_installed_packages():
    """获取已安装的相关包"""
    print("\n📦 检查已安装的相关包...")
    
    packages_to_check = ['PyQt6', 'PyQt6-Qt6', 'PyQt6-sip', 'PyQt5', 'PySide6']
    
    for package in packages_to_check:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                version_line = next((line for line in lines if line.startswith('Version:')), None)
                if version_line:
                    version = version_line.split(':')[1].strip()
                    print(f"✅ {package}: {version}")
                else:
                    print(f"✅ {package}: 已安装")
            else:
                print(f"❌ {package}: 未安装")
        except Exception as e:
            print(f"❓ {package}: 检查失败 - {e}")

def suggest_solutions():
    """提供解决方案建议"""
    print("\n🔧 解决方案建议:")
    print("=" * 50)
    
    print("方案1: 重新安装PyQt6")
    print("pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip")
    print("pip install PyQt6")
    print()
    
    print("方案2: 尝试使用PyQt5")
    print("pip uninstall PyQt6")
    print("pip install PyQt5")
    print("然后修改代码中的导入语句从PyQt6改为PyQt5")
    print()
    
    print("方案3: 安装Visual C++运行库")
    print("下载并安装Microsoft Visual C++ Redistributable")
    print("https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print()
    
    print("方案4: 使用conda安装")
    print("conda install pyqt")
    print()
    
    print("方案5: 尝试PySide6")
    print("pip install PySide6")
    print("然后修改代码使用PySide6而不是PyQt6")

def main():
    """主函数"""
    print("🔧 PyQt6问题诊断工具")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return
    
    # 检查系统信息
    check_system_info()
    
    # 检查已安装的包
    get_installed_packages()
    
    # 测试PyQt导入
    if test_pyqt_import():
        # 测试简单应用
        if test_simple_app():
            print("\n🎉 PyQt6工作正常！")
        else:
            print("\n⚠️  PyQt6导入成功但应用创建失败")
            suggest_solutions()
    else:
        print("\n❌ PyQt6导入失败")
        suggest_solutions()

if __name__ == "__main__":
    main()
