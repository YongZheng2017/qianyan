"""
配置管理模块

使用 Pydantic Settings 从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """系统配置类"""

    # 数据库配置
    DATABASE_URL: str
    DB_ECHO: bool = False

    # JWT 安全配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ADMIN_TOKEN_EXPIRE_HOURS: int = 2

    # 系统配置
    ADMIN_DEFAULT_PASSWORD: str = "123456"
    ADMIN_DEFAULT_USERNAME: str = "admin"
    PROJECT_NAME: str = "钱眼投资分析系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS配置
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """将逗号分隔的CORS域名转换为列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()