"""
会员套餐 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class MembershipPlanCreate(BaseModel):
    """创建套餐"""
    name: str = Field(..., max_length=50, description="套餐名称")
    plan_type: str = Field(..., description="套餐类型: monthly/quarterly/yearly/lifetime/credit")
    price: Decimal = Field(..., gt=0, description="售价（元）")
    original_price: Optional[Decimal] = Field(None, description="原价（划线价）")
    daily_parse_count: int = Field(default=10, ge=0, description="每日解析次数")
    daily_generate_count: int = Field(default=5, ge=0, description="每日生成次数")
    support_hd_export: bool = Field(default=False, description="是否支持高清导出")
    sort_order: int = Field(default=0, ge=0, description="排序权重")
    is_active: int = Field(default=1, description="上下架状态: 1上架 0下架")


class MembershipPlanUpdate(BaseModel):
    """更新套餐"""
    name: Optional[str] = Field(None, max_length=50)
    plan_type: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    original_price: Optional[Decimal] = None
    daily_parse_count: Optional[int] = Field(None, ge=0)
    daily_generate_count: Optional[int] = Field(None, ge=0)
    support_hd_export: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[int] = None


class MembershipPlanOut(BaseModel):
    """套餐输出"""
    id: int
    name: str
    plan_type: str
    price: Decimal
    original_price: Optional[Decimal]
    daily_parse_count: int
    daily_generate_count: int
    support_hd_export: bool
    sort_order: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True
