"""
JWT 辅助工具
"""
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import get_settings

settings = get_settings()


def decode_token(token: str) -> dict:
    """解码 JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception as e:
        raise ValueError(f"Token 无效: {e}")


def token_contains(user_id: int, token: str) -> bool:
    """检查 token 中的用户ID是否匹配"""
    try:
        payload = decode_token(token)
        return payload.get("sub") == user_id
    except ValueError:
        return False
