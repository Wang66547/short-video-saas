"""
权限中间件模块
- 调用解析/生成接口时自动校验用户当日剩余次数
- 次数不足直接返回403，引导开通会员
- 免费用户默认每日3次解析、1次生成，可后台配置
"""
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.parse_record import ParseRecord
from app.models.generate_record import GenerateRecord
from app.core.config import get_settings

settings = get_settings()


def get_daily_limit(membership_level: str, task_type: str) -> int:
    """
    根据会员等级和任务类型获取每日限制次数
    :param membership_level: 会员等级
    :param task_type: 任务类型 (parse/generate)
    :return: 每日最大次数
    """
    if task_type == "parse":
        limits = {
            "free": settings.FREE_DAILY_PARSE_LIMIT,
            "basic": settings.BASIC_DAILY_PARSE_LIMIT,
            "premium": settings.PREMIUM_DAILY_PARSE_LIMIT,
        }
    else:  # generate
        limits = {
            "free": settings.FREE_DAILY_GENERATE_LIMIT,
            "basic": settings.BASIC_DAILY_GENERATE_LIMIT,
            "premium": settings.PREMIUM_DAILY_GENERATE_LIMIT,
        }
    return limits.get(membership_level, 3)


async def check_daily_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    task_type: str = "parse"
):
    """
    检查用户当日使用次数是否充足
    :param current_user: 当前用户
    :param db: 数据库会话
    :param task_type: 任务类型 (parse/generate)
    :raises HTTPException: 次数不足时抛出403
    """
    # 获取每日限制次数
    limit = get_daily_limit(current_user.membership_level, task_type)
    
    if limit == 0:
        raise HTTPException(
            status_code=403,
            detail=f"当前会员等级不支持{task_type}任务，请升级会员",
        )
    
    # 检查今日已使用次数
    today_start = datetime.now(timezone(timedelta(hours=8))).replace(hour=0, minute=0, second=0)
    
    if task_type == "parse":
        count_stmt = (
            select(func.count())
            .select_from(ParseRecord)
            .where(ParseRecord.user_id == current_user.id, ParseRecord.created_at >= today_start)
        )
    else:
        count_stmt = (
            select(func.count())
            .select_from(GenerateRecord)
            .where(GenerateRecord.user_id == current_user.id, GenerateRecord.created_at >= today_start)
        )
    
    today_count = (await db.execute(count_stmt)).scalar() or 0
    
    if today_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"今日{task_type}次数已达上限({limit}次)，请明天再来或升级会员",
        )
    
    return True
