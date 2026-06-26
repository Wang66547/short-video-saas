"""
接口限流模块
基于 Redis 实现：
- 按用户ID限流（登录后）
- 按IP限流（未登录/匿名）
- 支持分钟级和日级两种粒度
"""
from functools import wraps
import time
from typing import Optional
from fastapi import Request, HTTPException, Depends
from app.core.redis_client import get_redis


async def check_rate_limit(
    key_prefix: str,
    limit_per_minute: int = 60,
    limit_per_day: int = 10000,
) -> bool:
    """
    检查请求是否超过限流阈值
    :param key_prefix: Redis key 前缀
    :param limit_per_minute: 每分钟最大请求数
    :param limit_per_day: 每天最大请求数
    :return: True=通过, False=超限
    :raises HTTPException: 超限则抛出 429
    """
    redis = await get_redis()
    if not redis:
        return True  # Redis 不可用时放行

    now = int(time.time())

    # --- 分钟级限流（滑动窗口）---
    minute_key = f"rate:{key_prefix}:min:{now // 60}"
    minute_pipe = redis.pipeline()
    minute_pipe.incr(minute_key)
    minute_pipe.expire(minute_key, 120)  # 延长2分钟确保数据不丢
    minute_result = minute_pipe.execute()
    minute_count = minute_result[0]

    if minute_count > limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请稍后再试（每分钟最多{limit_per_minute}次）",
        )

    # --- 日级限流（按天计数）---
    day_key = f"rate:{key_prefix}:day:{now // 86400}"
    day_pipe = redis.pipeline()
    day_pipe.incr(day_key)
    day_pipe.expire(day_key, 172800)  # 延长2天
    day_result = day_pipe.execute()
    day_count = day_result[0]

    if day_count > limit_per_day:
        raise HTTPException(
            status_code=429,
            detail=f"今日请求次数已达上限（{limit_per_day}次），请明天再来",
        )

    return True


def rate_limit_user(limit_per_minute: int = 60, limit_per_day: int = 10000):
    """
    装饰器：对用户ID限流（需配合认证中间件使用）
    用法: @rate_limit_user()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 或 args 中获取当前用户ID
            # 实际使用时依赖注入 current_user
            from fastapi import Depends
            # 这里通过请求状态标记来获取用户ID
            request = kwargs.get("request") or (args[0] if args else None)
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                key = f"user:{user_id}"
            else:
                key = "anonymous"
            await check_rate_limit(key, limit_per_minute, limit_per_day)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit_ip(limit_per_minute: int = 30, limit_per_day: int = 5000):
    """
    装饰器：按IP限流（适用于未登录接口）
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or (args[0] if args else None)
            if request:
                ip = request.client.host if request.client else "unknown"
                key = f"ip:{ip}"
            else:
                key = "anonymous"
            await check_rate_limit(key, limit_per_minute, limit_per_day)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
