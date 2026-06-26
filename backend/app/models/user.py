"""
用户表模型
- 手机号 + 微信 OpenID 双登录支持
- 会员等级、到期时间、剩余生成点数
- 状态管理（active/banned）
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean, Index
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")

    # 基本身份信息
    username = Column(String(50), unique=True, nullable=True, comment="用户名")
    phone = Column(String(20), unique=True, nullable=True, comment="手机号")
    wechat_openid = Column(String(64), unique=True, nullable=True, comment="微信OpenID")
    nickname = Column(String(50), default="", comment="昵称")
    avatar = Column(String(500), default="", comment="头像URL")
    password_hash = Column(String(255), nullable=True, comment="密码哈希（微信登录可为空）")

    # 会员信息
    membership_level = Column(
        String(20), default="free", comment="会员等级: free/basic/premium/enterprise"
    )
    membership_expire_at = Column(DateTime, nullable=True, comment="会员到期时间")
    remaining_credits = Column(BigInteger, default=0, comment="剩余生成点数")

    # 账户状态
    status = Column(String(20), default="active", comment="状态: active/banned/deleted")

    # 登录追踪
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    # 索引优化
    __table_args__ = (
        Index("idx_user_phone", "phone"),
        Index("idx_user_wechat", "wechat_openid"),
        Index("idx_user_status", "status", "membership_level"),
    )

    # 关系映射
    parse_records = relationship("ParseRecord", back_populates="user")
    generate_records = relationship("GenerateRecord", back_populates="user")
    orders = relationship("Order", back_populates="user")

    def is_membership_valid(self) -> bool:
        """判断会员是否有效"""
        if self.membership_level == "free":
            return False
        if not self.membership_expire_at:
            return False
        return self.membership_expire_at > datetime.now(timezone(timedelta(hours=8)))
