"""
订单表模型
- 关联用户和套餐
- 支付金额、方式、状态追踪
- 回调原始数据保存
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base
from app.models.base import TimestampMixin


class PaymentMethod(str, enum.Enum):
    """支付方式枚举"""
    WECHAT = "wechat"
    ALIPAY = "alipay"


class OrderStatus(str, enum.Enum):
    """订单状态枚举"""
    PENDING = "pending"       # 待支付
    PAID = "paid"             # 已支付
    REFUNDED = "refunded"     # 已退款
    CANCELLED = "cancelled"   # 已取消


class Order(Base, TimestampMixin):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="订单ID")

    order_no = Column(String(32), unique=True, nullable=False, comment="订单号")
    order_type = Column(String(20), default="membership", comment="订单类型: membership/credit")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=True, comment="关联套餐ID（会员订单）")

    amount = Column(Numeric(10, 2), nullable=False, comment="支付金额")
    paid_amount = Column(Numeric(10, 2), default=0, comment="实付金额")

    # 支付过期时间（30分钟后过期）
    expired_at = Column(DateTime, nullable=True, comment="订单过期时间")

    payment_method = Column(SAEnum(PaymentMethod), nullable=True, comment="支付方式")
    payment_status = Column(
        SAEnum(OrderStatus), default=OrderStatus.PENDING, comment="支付状态"
    )
    paid_at = Column(DateTime, nullable=True, comment="支付时间")

    # 回调原始数据（用于对账和排查）
    callback_data = Column(Text, default="", comment="回调原始数据")

    # 关系
    user = relationship("User", back_populates="orders")
