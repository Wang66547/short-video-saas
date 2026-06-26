"""
管理员表模型
- 登录账号、密码哈希
- 角色权限区分
"""
from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base
from app.models.base import TimestampMixin


class Admin(Base, TimestampMixin):
    """管理员表"""
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="管理员ID")

    username = Column(String(50), unique=True, nullable=False, comment="登录账号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    # 角色: super_admin/operator/viewer
    role = Column(String(20), default="viewer", comment="角色权限")
    real_name = Column(String(50), default="", comment="真实姓名")
    is_active = Column(Integer, default=1, comment="是否启用 1/0")
