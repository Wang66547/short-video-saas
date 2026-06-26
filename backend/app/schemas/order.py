"""
订单 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class OrderCreate(BaseModel):
    """创建订单"""
    plan_id: int


class OrderOut(BaseModel):
    """订单输出"""
    id: int
    order_no: str
    order_type: str
    user_id: int
    plan_id: Optional[int]
    amount: Decimal
    paid_amount: Decimal
    payment_method: Optional[str]
    payment_status: str
    paid_at: Optional[datetime]
    expired_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderDetailOut(BaseModel):
    """订单详情输出"""
    id: int
    order_no: str
    order_type: str
    user_id: int
    plan_id: Optional[int]
    plan_name: Optional[str]
    amount: float
    paid_amount: float
    payment_method: Optional[str]
    payment_status: str
    paid_at: Optional[str]
    expired_at: Optional[str]
    created_at: str
