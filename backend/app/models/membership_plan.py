"""
会员套餐表模型
- 支持月卡/季卡/年卡/终身卡/次卡多种类型
- 每日解析次数、每日生成次数限制
- 是否支持高清导出
- 排序和上下架状态
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import TimestampMixin


class MembershipPlan(Base, TimestampMixin):
    """会员套餐表"""
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="套餐ID")

    name = Column(String(50), nullable=False, comment="套餐名称，如月度会员")
    # 类型: monthly/quarterly/yearly/lifetime/credit
    plan_type = Column(
        String(20), nullable=False, comment="套餐类型: monthly/quarterly/yearly/lifetime/credit"
    )
    price = Column(Numeric(10, 2), nullable=False, comment="售价（元）")
    original_price = Column(Numeric(10, 2), nullable=True, comment="原价（划线价）")

    # 权益配置
    daily_parse_count = Column(Integer, default=10, comment="每日解析次数")
    daily_generate_count = Column(Integer, default=5, comment="每日生成次数")
    support_hd_export = Column(Boolean, default=False, comment="是否支持高清导出")

    # 管理字段
    sort_order = Column(Integer, default=0, comment="排序权重，数值越小越靠前")
    is_active = Column(Integer, default=1, comment="上下架状态: 1上架 0下架")
