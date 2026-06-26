"""
会员管理路由
- 套餐列表（公开）
- 套餐CRUD（管理员）
- 卡密兑换
- 会员状态查询
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin
from app.models.membership_plan import MembershipPlan
from app.models.card_key import CardKey, CardKeyStatus
from app.schemas.membership_plan import MembershipPlanOut, MembershipPlanCreate, MembershipPlanUpdate
from app.schemas.card_key import CardKeyOut
from datetime import datetime, timezone, timedelta

router = APIRouter()


# ==================== 公开接口 ====================

@router.get("/plans", response_model=dict)
async def get_plans(db: AsyncSession = Depends(get_db)):
    """获取所有可用的会员套餐列表（公开）"""
    result = await db.execute(
        select(MembershipPlan)
        .where(MembershipPlan.is_active == 1)
        .order_by(MembershipPlan.sort_order.asc())
    )
    plans = result.scalars().all()
    return {
        "code": 200, "message": "success",
        "data": [MembershipPlanOut.model_validate(p) for p in plans],
    }


@router.get("/status", response_model=dict)
async def get_status(current_user: User = Depends(get_current_user)):
    """获取当前用户的会员状态"""
    is_valid = current_user.is_membership_valid()
    return {
        "code": 200, "message": "success",
        "data": {
            "membership_level": current_user.membership_level,
            "membership_expire_at": current_user.membership_expire_at.isoformat() if current_user.membership_expire_at else None,
            "is_valid": is_valid,
            "remaining_credits": current_user.remaining_credits,
        },
    }


# ==================== 卡密兑换 ====================

@router.post("/redeem", response_model=dict)
async def redeem(
    key_code: str = Query(..., description="卡密字符串"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """卡密兑换会员权益"""
    from app.core.redis_client import get_redis
    
    redis = await get_redis()
    if redis:
        rate_key = f"redeem_rate:{current_user.id}"
        current_count = await redis.get(rate_key)
        if current_count and int(current_count) >= 5:
            raise HTTPException(status_code=429, detail="兑换过于频繁，请稍后再试")
        await redis.incr(rate_key)
        await redis.expire(rate_key, 60)
    
    # 查询卡密
    result = await db.execute(select(CardKey).where(CardKey.key_code == key_code))
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="卡密不存在")
    if card.status != CardKeyStatus.UNUSED:
        raise HTTPException(status_code=400, detail="卡密已被使用或已过期")

    # 查询关联套餐
    plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == card.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="关联套餐不存在")

    # 兑换会员权益
    from app.services.membership_service import redeem_card_key
    await redeem_card_key(db, card, current_user.id)

    return {"code": 200, "message": "兑换成功", "data": {"plan_name": plan.name}}


# ==================== 管理员接口 ====================

@router.get("/admin/plans", response_model=dict)
async def admin_list_plans(
    page: int = 1,
    size: int = 20,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取所有套餐列表（包括下架的）"""
    offset = (page - 1) * size
    total = (await db.execute(select(func.count()).select_from(MembershipPlan))).scalar() or 0

    stmt = select(MembershipPlan).order_by(MembershipPlan.sort_order.asc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    plans = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [MembershipPlanOut.model_validate(p) for p in plans],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.post("/admin/plans", response_model=dict)
async def admin_create_plan(
    body: MembershipPlanCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员创建会员套餐"""
    plan = MembershipPlan(
        name=body.name,
        plan_type=body.plan_type,
        price=body.price,
        original_price=body.original_price,
        daily_parse_count=body.daily_parse_count,
        daily_generate_count=body.daily_generate_count,
        support_hd_export=body.support_hd_export,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {
        "code": 201,
        "message": "套餐创建成功",
        "data": MembershipPlanOut.model_validate(plan),
    }


@router.put("/admin/plans/{plan_id}", response_model=dict)
async def admin_update_plan(
    plan_id: int,
    body: MembershipPlanUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新会员套餐"""
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    # 更新字段
    if body.name is not None:
        plan.name = body.name
    if body.plan_type is not None:
        plan.plan_type = body.plan_type
    if body.price is not None:
        plan.price = body.price
    if body.original_price is not None:
        plan.original_price = body.original_price
    if body.daily_parse_count is not None:
        plan.daily_parse_count = body.daily_parse_count
    if body.daily_generate_count is not None:
        plan.daily_generate_count = body.daily_generate_count
    if body.support_hd_export is not None:
        plan.support_hd_export = body.support_hd_export
    if body.sort_order is not None:
        plan.sort_order = body.sort_order
    if body.is_active is not None:
        plan.is_active = body.is_active

    await db.commit()
    await db.refresh(plan)

    return {
        "code": 200,
        "message": "套餐更新成功",
        "data": MembershipPlanOut.model_validate(plan),
    }


@router.delete("/admin/plans/{plan_id}", response_model=dict)
async def admin_delete_plan(
    plan_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除会员套餐（软删除：设为下架）"""
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    plan.is_active = 0
    await db.commit()

    return {
        "code": 200,
        "message": "套餐已下架",
        "data": None,
    }


@router.put("/admin/plans/{plan_id}/toggle", response_model=dict)
async def admin_toggle_plan(
    plan_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员上下架套餐"""
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    plan.is_active = 0 if plan.is_active == 1 else 1
    await db.commit()

    return {
        "code": 200,
        "message": f"套餐已{'上架' if plan.is_active == 1 else '下架'}",
        "data": None,
    }
