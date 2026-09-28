"""创建同步 SQLAlchemy Engine、Session 工厂和请求级依赖。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# pool_pre_ping 会在借出连接前确认连接仍然有效；pool_recycle 用于规避 MySQL
# 主动关闭长时间空闲连接后，连接池继续复用失效连接的问题。
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """为一次 FastAPI 请求提供 Session，并在请求结束后确保关闭。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
