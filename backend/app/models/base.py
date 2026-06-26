"""
模型基类
提供公共字段和便捷方法
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, DateTime
from app.db.session import Base


def get_now_local() -> datetime:
    """获取当前东八区时间"""
    return datetime.now(timezone(timedelta(hours=8)))


class TimestampMixin:
    """时间戳 Mixin：自动维护 created_at / updated_at"""
    created_at = Column(
        DateTime, nullable=False, default=get_now_local, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=get_now_local,
        onupdate=get_now_local,
        comment="更新时间",
    )
