"""
用户相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """用户注册"""
    phone: str = Field(..., description="手机号")
    captcha: str = Field(..., description="验证码")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    nickname: Optional[str] = Field(None, max_length=50)


class UserLogin(BaseModel):
    """用户登录"""
    phone: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    wechat_code: Optional[str] = None


class TokenPair(BaseModel):
    """JWT令牌对"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileUpdate(BaseModel):
    """更新个人资料"""
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = None


class UserOut(BaseModel):
    """用户信息输出"""
    id: int
    username: Optional[str]
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
