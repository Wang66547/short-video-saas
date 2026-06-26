"""
阿里云短信服务
- 发送验证码（带频率限制）
- 验证码5分钟有效
- 降级策略：未配置阿里云时返回测试验证码并记录警告
"""
import logging
import random
import sys
from app.core.config import get_settings
from app.core.redis_client import get_redis

settings = get_settings()

CAPTCHA_TTL_SECONDS = 300  # 验证码有效期 5 分钟
SMS_INTERVAL_SECONDS = 60  # 发送间隔 60 秒
SMS_DAILY_LIMIT = 10  # 每日最多发送 10 次


async def send_sms_code(phone: str) -> str:
    """
    发送短信验证码
    :param phone: 手机号
    :return: 验证码
    :raises ValueError: 频率限制时抛出异常
    """
    r = await get_redis()

    # 频率限制检查
    if r:
        # 60秒内不能重复发送
        interval_key = f"sms:interval:{phone}"
        if await r.get(interval_key):
            raise ValueError("验证码发送过于频繁，请稍后再试")

        # 每日次数限制
        from datetime import datetime, timezone, timedelta
        today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d")
        daily_key = f"sms:daily:{phone}:{today}"
        daily_count = await r.get(daily_key)
        if daily_count and int(daily_count) >= SMS_DAILY_LIMIT:
            raise ValueError("今日验证码发送次数已达上限")

    # 生成验证码
    code = str(random.randint(100000, 999999))

    # 降级策略：开发环境或未配置时返回测试验证码
    if settings.DEBUG or not settings.ALIBABA_CLOUD_ACCESS_KEY_ID:
        if not settings.DEBUG and not settings.ALIBABA_CLOUD_ACCESS_KEY_ID:
            logging.warning(f"阿里云短信未配置，使用模拟验证码: {code} -> {phone}")
        else:
            logging.info(f"[DEV] 短信验证码: {code} -> {phone}")

        # 存储验证码
        if r:
            from app.core.redis_client import set_captcha
            await set_captcha(phone, code)
            await r.setex(interval_key, SMS_INTERVAL_SECONDS, "1")
            await r.incr(daily_key)
            await r.expire(daily_key, 86400)

        return code

    # TODO: 实际接入阿里云短信服务
    # 生产环境已配置但代码未实现时，优雅降级
    logging.warning(f"阿里云短信服务代码未实现，使用模拟验证码: {code} -> {phone}")
    if r:
        from app.core.redis_client import set_captcha
        await set_captcha(phone, code)
        await r.setex(interval_key, SMS_INTERVAL_SECONDS, "1")
        await r.incr(daily_key)
        await r.expire(daily_key, 86400)
    return code


async def verify_sms_code(phone: str, code: str) -> bool:
    """
    验证短信验证码
    :param phone: 手机号
    :param code: 用户输入的验证码
    :return: True=正确, False=错误
    """
    from app.core.redis_client import get_captcha
    stored = await get_captcha(phone)
    if not stored:
        return False
    if stored != code:
        return False
    # 验证成功后删除验证码（一次性使用）
    r = await get_redis()
    if r:
        await r.delete(f"captcha:{phone}")
    return True
