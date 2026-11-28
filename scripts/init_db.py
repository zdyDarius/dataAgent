# 文件：scripts/init_db.py
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# 项目自定义基类，继承框架原生 DeclarativeBase
class Base(DeclarativeBase):
    """所有数据表实体的父类：后续可在这里统一加公共字段与全局配置。"""

    # 插入时由数据库生成，不占 Python 侧逻辑
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        comment="创建时间",
    )
    # 更新时由 SQLAlchemy 自动带上 now()
    update_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=text("now()"),
        nullable=True,
        comment="更新时间",
    )

    class User(Base):
        __tablename__ = "users"  # 数据库表名

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)