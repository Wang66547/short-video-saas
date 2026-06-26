"""
微信授权登录服务
- code2session 换取 openid
- 自动注册/登录
- 生成 JWT 令牌
"""
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.user import User

settings = get_settings()


async def code2session(code: str) -> dict:
    """
    微信 code2session 接口
    换取 openid 和 session_key
    """
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "errcode" in data:
        raise ValueError(f"WeChat error: {data['errmsg']}")

    return {
        "openid": data["openid"],
        "session_key": data.get("session_key", ""),
        "unionid": data.get("unionid"),
    }


async def wechat_login_or_register(db: AsyncSession, code: str) -> User:
    """
    微信授权登录/注册
    1. 通过 code 换取 openid
    2. 查找或创建用户
    3. 返回用户对象
    """
    wx_data = await code2session(code)
    openid = wx_data["openid"]

    # 查找或创建用户
    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()

    if not user:
        # 自动注册
        user = User(
            wechat_openid=openid,
            nickname="微信用户",
            password_hash=hash_password(openid[:16]),  # 占位密码
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone(timedelta(hours=8)))
    await db.commit()

    return user


async def generate_wechat_token(user: User) -> dict:
    """生成微信登录JWT令牌"""
    token_data = {"sub": user.id, "role": "user"}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "expires_in": 60 * 24 * 60,
    }
