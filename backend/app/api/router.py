"""
路由聚合模块
将所有子路由整合到统一的前缀下
"""
from fastapi import APIRouter
from app.api import auth, users, membership, parse, generate, payments, card_keys, admin

# 创建主路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(membership.router, prefix="/membership", tags=["会员管理"])
api_router.include_router(parse.router, prefix="/parse", tags=["视频解析"])
api_router.include_router(generate.router, prefix="/generate", tags=["视频生成"])
api_router.include_router(payments.router, prefix="/payments", tags=["支付管理"])
api_router.include_router(card_keys.router, prefix="/card-keys", tags=["卡密管理"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理后台"])
