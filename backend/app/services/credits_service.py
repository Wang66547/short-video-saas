"""
每日次数/积分校验服务
- 校验用户当日解析/生成剩余次数
- 校验用户剩余积分
- 扣减次数/积分
- 每日自动重置（通过Redis计数器）
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.redis_client import cache_get, cache_set, cache_delete, get_redis
from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


def _get_daily_limit(user: User, action: str) -> int:
    """获取用户每日使用次数上限"""
    level = user.membership_level or "free"
    if action == "parse":
        limits = {
            "free": settings.FREE_DAILY_PARSE_LIMIT,
            "basic": settings.BASIC_DAILY_PARSE_LIMIT,
            "premium": settings.PREMIUM_DAILY_PARSE_LIMIT,
        }
        return limits.get(level, settings.FREE_DAILY_PARSE_LIMIT)
    else:
        limits = {
            "free": settings.FREE_DAILY_GENERATE_LIMIT,
            "basic": settings.BASIC_DAILY_GENERATE_LIMIT,
            "premium": settings.PREMIUM_DAILY_GENERATE_LIMIT,
        }
        return limits.get(level, settings.FREE_DAILY_GENERATE_LIMIT)


def _is_membership_valid(user: User) -> bool:
    """检查会员是否在有效期内"""
    if not user.membership_level or user.membership_level == "free":
        return True
    if not user.membership_expire_at:
        return False
    now = datetime.now(timezone(timedelta(hours=8)))
    return user.membership_expire_at > now


async def check_daily_parse_limit(db: AsyncSession, user_id: int) -> bool:
    """
    校验用户当日解析次数是否足够（会员过期按免费版算）
    :return: True=足够, False=不足
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        return False

    daily_limit = _get_daily_limit(user, "parse")
    if not _is_membership_valid(user):
        daily_limit = settings.FREE_DAILY_PARSE_LIMIT

    # 通过Redis记录当日已用次数
    today_key = f"daily:parse:{user_id}:{datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')}"
    used = await cache_get(today_key)
    if used is None:
        await cache_set(today_key, 0, expire=86400)
        used = 0

    return int(used) < daily_limit


async def deduct_daily_parse(db: AsyncSession, user_id: int) -> bool:
    """
    扣减用户当日解析次数（使用 Redis INCR 原子操作）
    :return: True=扣减成功, False=超出限制
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    daily_limit = _get_daily_limit(user, "parse")
    if not _is_membership_valid(user):
        daily_limit = settings.FREE_DAILY_PARSE_LIMIT

    today_key = f"daily:parse:{user_id}:{datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')}"

    # 使用 Redis 原子操作：先 INCR 再判断
    r = await get_redis()
    if r:
        new_count = await r.incr(today_key)
        if new_count == 1:
            await r.expire(today_key, 86400)
        if new_count > daily_limit:
            return False
        return True

    # Redis 不可用时降级（仍有竞态，但保证基本功能）
    current = await cache_get(today_key) or 0
    if int(current) >= daily_limit:
        return False
    await cache_set(today_key, int(current) + 1, expire=86400)
    return True


async def check_daily_generate_limit(db: AsyncSession, user_id: int) -> bool:
    """校验用户当日生成次数是否足够"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        return False

    daily_limit = _get_daily_limit(user, "generate")
    if not _is_membership_valid(user):
        daily_limit = settings.FREE_DAILY_GENERATE_LIMIT

    today_key = f"daily:generate:{user_id}:{datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')}"
    used = await cache_get(today_key)
    if used is None:
        await cache_set(today_key, 0, expire=86400)
        used = 0

    return int(used) < daily_limit


async def deduct_daily_generate(db: AsyncSession, user_id: int) -> bool:
    """
    扣减用户当日生成次数（使用 Redis INCR 原子操作）
    :return: True=扣减成功, False=超出限制
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    daily_limit = _get_daily_limit(user, "generate")
    if not _is_membership_valid(user):
        daily_limit = settings.FREE_DAILY_GENERATE_LIMIT

    today_key = f"daily:generate:{user_id}:{datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')}"

    # 使用 Redis 原子操作
    r = await get_redis()
    if r:
        new_count = await r.incr(today_key)
        if new_count == 1:
            await r.expire(today_key, 86400)
        if new_count > daily_limit:
            return False
        return True

    current = await cache_get(today_key) or 0
    if int(current) >= daily_limit:
        return False
    await cache_set(today_key, int(current) + 1, expire=86400)
    return True


async def consume_credits(user_id: int, credits: int) -> bool:
    """
    消耗用户积分（使用行锁防止并发超扣）
    :param user_id: 用户ID
    :param credits: 消耗的积分数量
    :return: True=成功, False=失败
    """
    from app.db.session import async_session_factory

    try:
        async with async_session_factory() as db:
            async with db.begin():
                # 使用行锁防止并发超扣
                result = await db.execute(
                    select(User).where(User.id == user_id).with_for_update()
                )
                user = result.scalar_one_or_none()

                if not user:
                    return False

                if user.remaining_credits < credits:
                    return False

                user.remaining_credits -= credits
            return True

    except Exception as e:
        logging.error(f"消耗积分失败: {e}")
        return False
