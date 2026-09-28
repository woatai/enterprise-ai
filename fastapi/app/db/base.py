"""声明所有 SQLAlchemy 模型共享的基类。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 声明式模型基类。"""

    pass
