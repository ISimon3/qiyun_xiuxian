# 配置文件 (数据库地址, 密钥等)

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "纸上修仙模拟器"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./qiyun_xiuxian.db"

    @property
    def database_url(self) -> str:
        """获取数据库URL，确保使用项目根目录的数据库文件"""
        import os
        # 获取项目根目录（config.py的上两级目录）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, "qiyun_xiuxian.db")
        return f"sqlite+aiosqlite:///{db_path}"
    DATABASE_ECHO: bool = False  # 是否打印SQL语句

    # PostgreSQL配置 (可选)
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:3000", "http://127.0.0.1:3000",  # Web前端
        "http://localhost:8000", "http://127.0.0.1:8000",  # 本地客户端
        "*"  # 允许所有来源（开发环境）
    ]

    # 游戏配置
    CULTIVATION_TICK_INTERVAL: int = 10   # 挂机修炼计算间隔(秒)

    # 测试模式配置
    STORE_PLAIN_PASSWORD: bool = True    # 是否存储明文密码（测试模式）

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def postgres_url(self) -> Optional[str]:
        """构建PostgreSQL连接URL"""
        if all([self.POSTGRES_HOST, self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB]):
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return None

    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        # 如果配置了PostgreSQL，优先使用PostgreSQL
        postgres_url = self.postgres_url
        if postgres_url:
            return postgres_url
        # 使用绝对路径的SQLite数据库
        return self.database_url


# 创建全局配置实例
settings = Settings()


# 开发环境配置
class DevelopmentSettings(Settings):
    DEBUG: bool = True
    DATABASE_ECHO: bool = True


# 生产环境配置
class ProductionSettings(Settings):
    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")


# 测试环境配置
class TestSettings(Settings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    SECRET_KEY: str = "test-secret-key"


def get_settings() -> Settings:
    """根据环境变量获取配置"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()
