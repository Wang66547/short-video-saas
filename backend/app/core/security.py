"""
安全认证模块
- 密码 bcrypt 哈希
- JWT 令牌签发与验证
- 权限校验依赖注入
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.models.admin import Admin

settings = get_settings()

# OAuth2 Bearer Token 认证 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# 管理员 OAuth2 scheme（使用不同 tokenUrl，避免与用户端冲突）
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login", auto_error=False)


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希，不可逆加密"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配哈希值"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, token_version: int = 0) -> str:
    """
    创建 JWT 访问令牌
    :param data: 载荷数据（用户ID、角色等）
    :param expires_delta: 自定义过期时间
    :param token_version: token版本号，用于修改密码后失效旧token
    """
    import uuid
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone(timedelta(hours=8))) + expires_delta
    else:
        expire = datetime.now(timezone(timedelta(hours=8))) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4()), "token_version": token_version})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, token_version: int = 0) -> str:
    """创建刷新令牌，有效期更长"""
    return create_access_token(data, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), token_version=token_version)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    依赖注入：从 JWT 获取当前登录用户
    验证：令牌有效性 -> 过期时间 -> 用户存在且活跃 -> 不在黑名单 -> token版本匹配
    """
    from app.core.redis_client import is_token_blacklisted, get_user_token_version
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据，请先登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)  # sub 存储为字符串，解析时转换
        token_jti = payload.get("jti")
        # 检查 token 是否在黑名单中
        if token_jti and await is_token_blacklisted(user_id, token_jti):
            raise credentials_exception
        # 检查 token 版本（修改密码后旧token失效）
        token_version = payload.get("token_version", 0)
        current_version = await get_user_token_version(user_id)
        if token_version < current_version:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or user.status != "active":
        raise credentials_exception
    return user


async def get_current_admin(
    token: str = Depends(admin_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """
    依赖注入：从 JWT 获取当前管理员
    验证：令牌有效性 -> role 必须是 admin/super_admin -> 管理员存在且启用 -> 不在黑名单 -> token版本匹配
    注意：管理员身份与普通用户完全分离，不再依赖 membership_level 判断
    """
    from app.core.redis_client import is_token_blacklisted, get_user_token_version
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="管理员认证失败，请先登录管理后台",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        admin_id_str: str = payload.get("sub")
        if admin_id_str is None:
            raise credentials_exception
        admin_id = int(admin_id_str)
        role: str = payload.get("role", "")
        if role not in ("admin", "super_admin"):
            raise credentials_exception
        # 检查 token 是否在黑名单中
        token_jti = payload.get("jti")
        if token_jti and await is_token_blacklisted(admin_id, token_jti):
            raise credentials_exception
        # 检查 token 版本（修改密码后旧token失效）
        token_version = payload.get("token_version", 0)
        current_version = await get_user_token_version(admin_id)
        if token_version < current_version:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    if admin is None or admin.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员账号已被禁用",
        )
    return admin
