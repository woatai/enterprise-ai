"""集中读取数据库配置并生成 SQLAlchemy 连接地址。"""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


def _find_env_file() -> Path | None:
    """寻找本地 .env，同时兼容从项目根目录或 fastapi 目录启动。"""

    candidates = (
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    )
    return next((path for path in candidates if path.is_file()), None)


class Settings(BaseSettings):
    """应用配置。

    字段名会自动匹配 .env 中对应的大写变量，例如 mysql_user 对应 MYSQL_USER。
    """

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "enterprise_ai"
    mysql_user: str = "enterprise_app"
    # 密码没有代码内默认值，缺少环境变量时应立即失败，避免误用示例密码。
    mysql_password: SecretStr

    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800

    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        """使用分离的 MySQL 变量安全构建连接地址。

        URL.create 会正确处理密码中的 @、: 等特殊字符，避免手工拼接 URL 出错。
        """

        return URL.create(
            drivername="mysql+pymysql",
            username=self.mysql_user,
            password=self.mysql_password.get_secret_value(),
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    """缓存配置对象，避免每次导入时重复读取环境变量。"""

    return Settings()


settings = get_settings()
