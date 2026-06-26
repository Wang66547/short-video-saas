"""
会员业务逻辑
- 会员激活
- 卡密兑换
- 会员状态校验
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.membership_plan import MembershipPlan
from app.models.card_key import CardKey, CardKeyStatus


async def activate_membership(
    db: AsyncSession, 
    user_id: int, 
    plan: MembershipPlan, 
    source: str = "purchase", 
    source_id: int = None,
    auto_commit: bool = True
) -> User:
    """
    激活/续费会员
    :param db: 数据库会话
    :param user_id: 用户ID
    :param plan: 会员套餐对象
    :param source: 来源 (purchase/redeem)
    :param source_id: 来源ID（订单ID或卡密ID）
    :param auto_commit: 是否自动提交（外部事务控制时设为False）
    :return: 更新后的用户对象
    """
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"用户 {user_id} 不存在")

    now = datetime.now(timezone(timedelta(hours=8)))
    
    # 如果当前会员未过期，在原到期时间基础上累加
    if user.membership_expire_at and user.membership_expire_at > now:
        # 根据套餐类型计算续费天数
        days_map = {
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
            "lifetime": 99999,
            "credit": 0,
        }
        add_days = days_map.get(plan.plan_type, 30)
        new_expire = user.membership_expire_at + timedelta(days=add_days)
    else:
        # 新开通或已过期，从当前时间开始
        days_map = {
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
            "lifetime": 99999,
            "credit": 0,
        }
        new_expire = now + timedelta(days=days_map.get(plan.plan_type, 30))

    # 更新用户会员信息
    user.membership_level = plan.plan_type
    if plan.plan_type == "credit":
        # 点卡类型：增加积分，不设置会员等级
        user.remaining_credits = (user.remaining_credits or 0) + (plan.daily_parse_count or 0)
    else:
        user.membership_expire_at = new_expire
    user.status = "active"

    if auto_commit:
        await db.commit()
    return user


async def redeem_card_key(db: AsyncSession, card: CardKey, user_id: int):
    """
    卡密兑换（整个过程在一个事务中，保证原子性）
    :param db: 数据库会话
    :param card: 卡密对象
    :param user_id: 用户ID
    """
    # 使用行锁锁定卡密，防止并发重复兑换
    result = await db.execute(
        select(CardKey).where(CardKey.id == card.id).with_for_update()
    )
    locked_card = result.scalar_one_or_none()
    if not locked_card or locked_card.status != CardKeyStatus.UNUSED:
        raise ValueError("卡密已被使用或不存在")

    plan_result = await db.execute(
        select(MembershipPlan).where(MembershipPlan.id == locked_card.plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise ValueError("关联套餐不存在")

    # 激活会员（不自动提交，由本函数统一提交）
    await activate_membership(db, user_id, plan, source="redeem", source_id=locked_card.id, auto_commit=False)

    # 更新卡密状态
    locked_card.status = CardKeyStatus.USED
    locked_card.used_by_user_id = user_id
    locked_card.used_at = datetime.now(timezone(timedelta(hours=8)))

    await db.commit()
