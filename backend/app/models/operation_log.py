"""
操作日志表模型
- 记录所有重要操作：支付、会员开通、卡密兑换等
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import TimestampMixin


class OperationLog(Base, TimestampMixin):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作用户ID（管理员操作时为None）")
    operator_id = Column(Integer, nullable=True, comment="操作人ID（管理员ID）")
    action = Column(String(50), nullable=False, comment="操作类型: pay_success/member_activate/card_redeem等")
    target_type = Column(String(50), nullable=False, comment="目标类型: order/membership/card等")
    target_id = Column(Integer, nullable=True, comment="目标ID")
    detail = Column(Text, default="", comment="操作详情JSON")
    ip_address = Column(String(50), default="", comment="操作IP")
    status = Column(String(20), default="success", comment="操作状态: success/failed")
    error_message = Column(String(500), default="", comment="错误信息")

    __table_args__ = (
        Index("idx_op_user", "user_id", "created_at"),
        Index("idx_op_action", "action", "created_at"),
    )

    user = relationship("User")
