"""
管理员 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class AdminLogin(BaseModel):
    """管理员登录"""
    username: str
    password: str


class AdminStats(BaseModel):
    """管理后台统计数据"""
    total_users: int
    active_users: int
    total_orders: int
    today_orders: int
    total_revenue: float
    today_revenue: float
    total_parses: int
    total_generates: int
    pending_tasks: int


class UserManageOut(BaseModel):
    """用户管理输出"""
    id: int
    phone: Optional[str]
    nickname: str
    avatar: str
    membership_level: str
    membership_expire_at: Optional[datetime]
    remaining_credits: int
    status: str
    last_login_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserSearchRequest(BaseModel):
    """用户搜索请求"""
    keyword: Optional[str] = None
    status: Optional[str] = None
    membership_level: Optional[str] = None
    page: int = 1
    size: int = 20


class UserUpdateRequest(BaseModel):
    """用户信息修改请求"""
    nickname: Optional[str] = None
    membership_level: Optional[str] = None
    membership_expire_at: Optional[datetime] = None
    remaining_credits: Optional[int] = None
    status: Optional[str] = None


class OrderManageOut(BaseModel):
    """订单管理输出"""
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
    paid_at: Optional[datetime]
    expired_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderSearchRequest(BaseModel):
    """订单搜索请求"""
    keyword: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    size: int = 20


class ManualOrderRequest(BaseModel):
    """手动补单请求"""
    order_no: str
    payment_method: str
    paid_amount: float


class TrendPoint(BaseModel):
    """趋势数据点"""
    date: str
    value: int


class StatsTrendResponse(BaseModel):
    """趋势统计响应"""
    registrations: List[TrendPoint]
    orders: List[TrendPoint]
    revenue: List[TrendPoint]
    parses: List[TrendPoint]
    generates: List[TrendPoint]


class PlanManageOut(BaseModel):
    """套餐管理输出"""
    id: int
    name: str
    plan_type: str
    price: float
    original_price: Optional[float]
    daily_parse_count: int
    daily_generate_count: int
    support_hd_export: bool
    sort_order: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlanCreateRequest(BaseModel):
    """套餐创建请求"""
    name: str = Field(..., max_length=50)
    plan_type: str = Field(..., description="monthly/quarterly/yearly/lifetime")
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    daily_parse_count: int = Field(default=10, ge=0)
    daily_generate_count: int = Field(default=5, ge=0)
    support_hd_export: bool = False
    sort_order: int = Field(default=0, ge=0)
    is_active: int = Field(default=1, description="1上架 0下架")


class PlanUpdateRequest(BaseModel):
    """套餐更新请求"""
    name: Optional[str] = Field(None, max_length=50)
    plan_type: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = None
    daily_parse_count: Optional[int] = Field(None, ge=0)
    daily_generate_count: Optional[int] = Field(None, ge=0)
    support_hd_export: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[int] = None


class SystemConfigOut(BaseModel):
    """系统配置输出"""
    id: int
    key: str
    value: str
    category: str
    description: str
    is_public: int
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigUpdateRequest(BaseModel):
    """系统配置更新请求"""
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=5000)
    category: str = Field(default="general", max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    is_public: int = Field(default=0, ge=0, le=1)
