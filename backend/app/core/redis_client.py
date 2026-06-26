"""
Redis 客户端模块
提供连接管理、缓存读写、限流器、会话管理等能力
"""
from typing import Optional, Any, Dict
import json
from redis.asyncio import Redis, from_url

_redis: Optional[Redis] = None


async def get_redis() -> Optional[Redis]:
    """获取 Redis 连接实例（单例）"""
    global _redis
    if _redis is None:
        from app.core.config import get_settings
        settings = get_settings()
        url = (settings.REDIS_URL or "").strip()
        if not url or not url.startswith(("redis://", "rediss://", "unix://")):
            _redis = None
            return None
        try:
            _redis = from_url(
                url,
                decode_responses=True,
                retry_on_timeout=True,
            )
            await _redis.ping()
        except Exception:
            _redis = None
    return _redis


async def close_redis():
    """关闭 Redis 连接"""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


# ==================== 缓存读写 ====================

async def cache_get(key: str) -> Optional[Any]:
    """获取缓存，自动反序列化"""
    r = await get_redis()
    if not r:
        return None
    raw = await r.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


async def cache_set(key: str, value: Any, expire: int = 3600) -> bool:
    """设置缓存，自动序列化"""
    r = await get_redis()
    if not r:
        return False
    try:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        await r.setex(key, expire, serialized)
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    """删除缓存"""
    r = await get_redis()
    if not r:
        return False
    await r.delete(key)
    return True


# ==================== 短信验证码 ====================

async def get_captcha(phone: str) -> Optional[str]:
    """获取短信验证码"""
    return await cache_get(f"captcha:{phone}")


async def set_captcha(phone: str, code: str, expire: int = 300):
    """设置短信验证码，5分钟过期"""
    await cache_set(f"captcha:{phone}", code, expire)


# ==================== 用户令牌黑名单（登出用）====================

async def blacklist_token(user_id: int, token_jti: str):
    """将令牌加入黑名单"""
    r = await get_redis()
    if r:
        await r.setex(f"blacklist:{user_id}:{token_jti}", 86400, "1")


async def is_token_blacklisted(user_id: int, token_jti: str) -> bool:
    """检查令牌是否在黑名单中"""
    r = await get_redis()
    if not r:
        return False
    val = await r.get(f"blacklist:{user_id}:{token_jti}")
    return val is not None


# ==================== 批量任务状态（持久化到 Redis）====================

async def get_batch_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取批量任务状态"""
    r = await get_redis()
    if not r:
        return None
    raw = await r.get(f"batch_task:{task_id}")
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


async def set_batch_task(task_id: str, data: Dict[str, Any], expire: int = 86400) -> bool:
    """保存批量任务状态（默认24小时过期）"""
    r = await get_redis()
    if not r:
        return False
    try:
        serialized = json.dumps(data, ensure_ascii=False, default=str)
        await r.setex(f"batch_task:{task_id}", expire, serialized)
        return True
    except Exception:
        return False


async def add_user_batch_task(user_id: int, task_id: str, expire: int = 86400) -> bool:
    """将任务ID添加到用户的批量任务列表"""
    r = await get_redis()
    if not r:
        return False
    try:
        await r.sadd(f"user_batch_tasks:{user_id}", task_id)
        await r.expire(f"user_batch_tasks:{user_id}", expire)
        return True
    except Exception:
        return False


async def get_user_batch_tasks(user_id: int) -> list:
    """获取用户的所有批量任务ID"""
    r = await get_redis()
    if not r:
        return []
    try:
        return list(await r.smembers(f"user_batch_tasks:{user_id}"))
    except Exception:
        return []


# ==================== 用户Token版本（修改密码失效用）====================

async def get_user_token_version(user_id: int) -> int:
    """获取用户当前token版本号"""
    r = await get_redis()
    if not r:
        return 0
    val = await r.get(f"user_token_version:{user_id}")
    return int(val) if val else 0


async def increment_user_token_version(user_id: int) -> int:
    """递增用户token版本号（修改密码时调用，使所有旧token失效）"""
    r = await get_redis()
    if not r:
        return 0
    new_version = await r.incr(f"user_token_version:{user_id}")
    await r.expire(f"user_token_version:{user_id}", 86400 * 30)
    return int(new_version)
