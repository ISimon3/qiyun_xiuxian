# 服务端主程序入口 (启动FastAPI)

import sys
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.config import settings
from server.database.database import init_database, close_database
from shared.schemas import BaseResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动气运修仙游戏服务器...")

    try:
        # 初始化数据库
        await init_database()
        logger.info("数据库初始化完成")

        # 这里可以添加其他启动任务
        # 比如：初始化游戏数据、启动定时任务等

        logger.info(f"服务器启动成功，监听 {settings.HOST}:{settings.PORT}")
        yield

    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        raise

    # 关闭时执行
    logger.info("正在关闭服务器...")
    try:
        await close_database()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="气运修仙游戏后端API",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加可信主机中间件 (生产环境安全)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.HOST, "localhost", "127.0.0.1"]
    )


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseResponse(
            success=False,
            message=exc.detail,
            data=None
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=BaseResponse(
            success=False,
            message="服务器内部错误" if not settings.DEBUG else str(exc),
            data=None
        ).model_dump()
    )


# 中间件：请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = asyncio.get_event_loop().time()

    # 记录请求信息
    logger.info(f"请求: {request.method} {request.url}")

    response = await call_next(request)

    # 记录响应信息
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"响应: {response.status_code} - 耗时: {process_time:.3f}s")

    return response


# 根路径
@app.get("/", response_model=BaseResponse)
async def root():
    """根路径 - 服务器状态检查"""
    return BaseResponse(
        success=True,
        message=f"欢迎使用{settings.APP_NAME} API",
        data={
            "version": settings.APP_VERSION,
            "status": "running",
            "debug": settings.DEBUG
        }
    )


# 健康检查
@app.get("/health", response_model=BaseResponse)
async def health_check():
    """健康检查端点"""
    return BaseResponse(
        success=True,
        message="服务器运行正常",
        data={"status": "healthy"}
    )


# 注册API路由
from server.api.v1 import auth, user
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(user.router, prefix="/api/v1/user", tags=["用户"])


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
