# 服务端启动入口

import sys
import os
import uvicorn

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.config import settings


def start_server():
    """启动服务器"""
    print("🚀 正在启动气运修仙游戏服务器...")
    print(f"📡 服务器地址: http://{settings.HOST}:{settings.PORT}")
    print(f"🔧 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print("=" * 50)
    
    uvicorn.run(
        "server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )


if __name__ == "__main__":
    start_server()
