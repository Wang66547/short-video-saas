"""
卡密 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CardKeyRedeem(BaseModel):
    """卡密兑换请求"""
    key_code: str = Field(..., min_length=16, max_length=50)


class CardKeyOut(BaseModel):
    """卡密输出"""
    id: int
    key_code: str
    status: str
    plan_name: str
    used_by_user_id: Optional[int]
    used_at: Optional[datetime]
    batch_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CardKeyGenerateRequest(BaseModel):
    """批量生成卡密请求"""
    plan_id: int = Field(..., description="关联套餐ID")
    count: int = Field(default=10, ge=1, le=1000, description="生成数量")
    prefix: str = Field(default="", max_length=10, description="前缀")
    length: int = Field(default=20, ge=10, le=30, description="卡密长度")
