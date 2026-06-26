"""
卡密模型
- 卡密生成与管理
- 卡密状态追踪（未使用/已使用/已过期）
- 批量导入功能
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base
from app.models.base import TimestampMixin
from app.models.base import get_now_local


class CardKeyStatus(str, enum.Enum):
    """卡密状态枚举"""
    UNUSED = "unused"     # 未使用
    USED = "used"         # 已使用
    EXPIRED = "expired"   # 已过期


class CardKey(Base, TimestampMixin):
    """卡密表"""
    __tablename__ = "card_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="卡密ID")

    key_code = Column(String(50), unique=True, nullable=False, comment="卡密字符串")
    
    # 关联套餐
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False, comment="关联套餐ID")
    
    # 状态
    status = Column(SAEnum(CardKeyStatus), default=CardKeyStatus.UNUSED, comment="卡密状态")
    
    # 使用信息
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="使用人ID")
    used_at = Column(DateTime, nullable=True, comment="使用时间")
    
    # 批次信息
    batch_name = Column(String(100), default="", comment="批次名称")
    remark = Column(String(200), default="", comment="备注")
    
    # 关系
    plan = relationship("MembershipPlan")
    user = relationship("User")


class CardKeyBatch(Base, TimestampMixin):
    """卡密批次表 - 管理批量生成的卡密"""
    __tablename__ = "card_key_batches"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="批次ID")

    batch_name = Column(String(100), nullable=False, comment="批次名称")
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False, comment="关联套餐ID")
    
    # 统计
    total_count = Column(Integer, default=0, comment="总数量")
    used_count = Column(Integer, default=0, comment="已使用数量")
    
    # 生成规则
    prefix = Column(String(10), default="", comment="前缀")
    length = Column(Integer, default=20, comment="卡密长度")
