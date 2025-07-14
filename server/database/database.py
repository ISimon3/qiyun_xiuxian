# 数据库连接和会话配置

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from server.config import settings

logger = logging.getLogger(__name__)


# 数据库基类
class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


# 数据库引擎
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,   # 连接回收时间(秒)
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def init_database():
    """初始化数据库表"""
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def close_database():
    """关闭数据库连接"""
    try:
        await engine.dispose()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入用的数据库会话获取器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            raise
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal

    async def create_tables(self):
        """创建所有表"""
        await init_database()

    async def drop_tables(self):
        """删除所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        return self.session_factory()

    async def close(self):
        """关闭数据库连接"""
        await close_database()


# 全局数据库管理器实例
db_manager = DatabaseManager()
