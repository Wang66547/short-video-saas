"""
系统配置表模型
- 存储所有可动态配置的系统参数
- 支持通过管理后台修改
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import TimestampMixin


class SystemConfig(Base, TimestampMixin):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="配置ID")

    config_key = Column(String(100), unique=True, nullable=False, comment="配置键名")
    config_value = Column(Text, default="", comment="配置值")
    category = Column(String(50), default="general", comment="配置分类: general/payment/limit/sms/ai")
    description = Column(String(200), default="", comment="配置描述")
    is_public = Column(Integer, default=0, comment="是否公开: 1是 0否")
    updated_by = Column(Integer, nullable=True, comment="最后修改人ID")

    __table_args__ = (
        Index("idx_config_category", "category"),
    )
