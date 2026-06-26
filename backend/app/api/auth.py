"""
用户认证路由
- 手机号验证码登录注册
- 微信授权登录
- 用户信息查询修改
- 权限中间件
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user,
)
from app.core.rate_limit import check_rate_limit
from app.core.redis_client import get_captcha, set_captcha, cache_delete, get_redis
from app.models.user import User
from app.models.parse_record import ParseRecord
from app.models.generate_record import GenerateRecord
from app.schemas.user import (
    UserRegister, UserLogin, TokenPair, 
    UserProfileUpdate, UserOut
)
from app.schemas.parse_record import ParseRecordOut
from app.schemas.generate_record import GenerateRecordOut
from app.services.sms_service import send_sms_code, verify_sms_code
from app.services.wechat_auth_service import wechat_login_or_register, generate_wechat_token
from app.services.credits_service import check_daily_parse_limit, check_daily_generate_limit, deduct_daily_parse, deduct_daily_generate
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/send-code", response_model=dict)
async def send_verification_code(
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    """
    发送短信验证码
    1. 校验手机号格式
    2. 检查发送频率（1分钟/60秒）
    3. 发送验证码或返回测试码
    """
    # 校验手机号格式
    import re
    if not re.match(r'^1[3-9]\d{9}$', phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 检查发送频率
    redis = await get_redis()
    if redis:
        freq_key = f"sms_freq:{phone}"
        current = await redis.get(freq_key)
        if current:
            raise HTTPException(status_code=429, detail="发送过于频繁，请60秒后重试")
    
    # 发送验证码
    code = await send_sms_code(phone)
    
    # 存储验证码到Redis（5分钟过期）
    await set_captcha(phone, code, expire=300)
    
    # 设置发送频率限制
    if redis:
        await redis.setex(freq_key, 60, "1")
    
    return {
        "code": 200,
        "message": "验证码发送成功",
        "data": {"sent": True}
    }


@router.post("/register", response_model=dict, status_code=201)
async def register(
    body: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册
    1. 校验验证码（如提供）
    2. 检查手机号是否已注册
    3. 创建用户记录
    """
    # 校验验证码（强制验证）
    if not body.captcha:
        raise HTTPException(status_code=400, detail="请输入验证码")
    stored_code = await get_captcha(body.phone)
    if not stored_code or stored_code != body.captcha:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    
    # 检查手机号是否已存在
    existing = await db.execute(select(User).where(User.phone == body.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="手机号已被注册")
    
    # 创建新用户
    user = User(
        phone=body.phone,
        password_hash=hash_password(body.password),
        nickname=body.nickname or body.phone[-4:],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 清除验证码
    await cache_delete(f"captcha:{body.phone}")
    
    return {
        "code": 201,
        "message": "注册成功",
        "data": {"user_id": user.id}
    }


@router.post("/login", response_model=TokenPair)
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录
    支持手机号密码登录、用户名密码登录和微信授权登录
    """
    user = None
    login_key = None
    
    # 手机号密码登录
    if body.phone and body.password:
        login_key = body.phone
        redis = await get_redis()
        if redis:
            fail_key = f"login_fail:user:{body.phone}"
            fail_count = await redis.get(fail_key)
            if fail_count and int(fail_count) >= 5:
                raise HTTPException(status_code=429, detail="登录失败次数过多，请15分钟后再试")
        
        result = await db.execute(select(User).where(User.phone == body.phone))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(body.password, user.password_hash):
            if redis:
                await redis.incr(fail_key)
                await redis.expire(fail_key, 900)
            raise HTTPException(status_code=401, detail="手机号或密码错误")
        if user.status != "active":
            raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 用户名密码登录
    elif body.username and body.password:
        login_key = body.username
        redis = await get_redis()
        if redis:
            fail_key = f"login_fail:user:{body.username}"
            fail_count = await redis.get(fail_key)
            if fail_count and int(fail_count) >= 5:
                raise HTTPException(status_code=429, detail="登录失败次数过多，请15分钟后再试")
        
        result = await db.execute(select(User).where(User.username == body.username))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(body.password, user.password_hash):
            if redis:
                await redis.incr(fail_key)
                await redis.expire(fail_key, 900)
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if user.status != "active":
            raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 微信授权登录
    elif body.wechat_code:
        user = await wechat_login_or_register(db, body.wechat_code)
    else:
        raise HTTPException(status_code=400, detail="请提供手机号+密码或用户名+密码或微信授权码")
    
    # 登录成功，清除失败计数
    if login_key:
        redis = await get_redis()
        if redis:
            await redis.delete(f"login_fail:user:{login_key}")
    
    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone(timedelta(hours=8)))
    await db.commit()
    
    # 获取用户token版本号
    from app.core.redis_client import get_user_token_version
    token_version = await get_user_token_version(user.id)
    
    # 生成令牌（sub 必须是字符串，JWT 标准要求）
    token_data = {"sub": str(user.id), "role": "user"}
    return TokenPair(
        access_token=create_access_token(token_data, token_version=token_version),
        refresh_token=create_refresh_token(token_data, token_version=token_version),
        expires_in=60 * 24 * 60,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    """退出登录，将当前 token 加入黑名单"""
    from app.core.redis_client import blacklist_token
    # 从请求头获取原始 token
    auth_header = request.headers.get("Authorization", "") if request else ""
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    if token:
        try:
            from jose import jwt
            from app.core.config import get_settings
            settings = get_settings()
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_jti = payload.get("jti")
            if token_jti:
                await blacklist_token(current_user.id, token_jti)
        except Exception:
            pass  # token 解析失败不影响登出
    return {"code": 200, "message": "退出成功", "data": None}


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    刷新访问令牌
    使用当前有效的 access_token 获取新的令牌对
    """
    from app.core.redis_client import get_user_token_version
    token_version = await get_user_token_version(current_user.id)
    token_data = {"sub": str(current_user.id), "role": "user"}
    return TokenPair(
        access_token=create_access_token(token_data, token_version=token_version),
        refresh_token=create_refresh_token(token_data, token_version=token_version),
        expires_in=60 * 24 * 60,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return current_user


@router.put("/profile", response_model=dict)
async def update_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新个人资料"""
    if body.nickname:
        current_user.nickname = body.nickname
    if body.avatar:
        current_user.avatar = body.avatar
    await db.commit()
    return {"code": 200, "message": "更新成功", "data": {"nickname": current_user.nickname}}


@router.get("/parse-records", response_model=dict)
async def list_parse_records(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的解析记录列表（分页）"""
    offset = (page - 1) * size
    total = (await db.execute(
        select(func.count()).select_from(ParseRecord).where(ParseRecord.user_id == current_user.id)
    )).scalar() or 0
    
    result = await db.execute(
        select(ParseRecord)
        .where(ParseRecord.user_id == current_user.id)
        .order_by(ParseRecord.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    records = result.scalars().all()
    
    return {
        "code": 200, "message": "success",
        "data": [ParseRecordOut.model_validate(r) for r in records],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/generate-records", response_model=dict)
async def list_generate_records(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的生成记录列表（分页）"""
    offset = (page - 1) * size
    total = (await db.execute(
        select(func.count()).select_from(GenerateRecord).where(GenerateRecord.user_id == current_user.id)
    )).scalar() or 0
    
    result = await db.execute(
        select(GenerateRecord)
        .where(GenerateRecord.user_id == current_user.id)
        .order_by(GenerateRecord.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    records = result.scalars().all()
    
    return {
        "code": 200, "message": "success",
        "data": [GenerateRecordOut.model_validate(r) for r in records],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }
