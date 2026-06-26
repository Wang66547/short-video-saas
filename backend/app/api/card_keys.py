"""
卡密管理路由
- 用户卡密兑换
- 管理员批量生成卡密
- 卡密列表查询
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin
from app.models.card_key import CardKey, CardKeyStatus
from app.models.membership_plan import MembershipPlan
from app.schemas.card_key import CardKeyRedeem, CardKeyGenerateRequest, CardKeyOut
from app.services.membership_service import activate_membership
from app.services.card_key_service import generate_card_keys

router = APIRouter()


@router.post("/redeem", response_model=dict)
async def redeem(
    body: CardKeyRedeem,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """卡密兑换会员权益"""
    result = await db.execute(select(CardKey).where(CardKey.key_code == body.key_code))
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="卡密不存在")
    if card.status != CardKeyStatus.UNUSED:
        raise HTTPException(status_code=400, detail="卡密已被使用或已过期")

    plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == card.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="关联套餐不存在")

    await activate_membership(db, current_user.id, plan, source="redeem", source_id=card.id)

    card.status = CardKeyStatus.USED
    card.used_by_user_id = current_user.id
    card.used_at = datetime.now(timezone(timedelta(hours=8)))
    await db.commit()

    return {"code": 200, "message": "兑换成功", "data": {"plan_name": plan.name}}


@router.post("/generate", response_model=dict)
async def generate_cards(
    body: CardKeyGenerateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """批量生成卡密（管理员功能）"""
    plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == body.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    keys = await generate_card_keys(db, body.plan_id, body.count, body.prefix, body.length)

    return {
        "code": 200,
        "message": f"成功生成 {body.count} 张卡密",
        "data": {"keys": keys, "plan_name": plan.name},
    }


@router.get("/list", response_model=dict)
async def list_card_keys(
    page: int = 1, size: int = 20, status: str = None,
    current_admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db),
):
    """获取卡密列表（管理员）"""
    offset = (page - 1) * size
    base_query = select(CardKey)
    if status:
        base_query = base_query.where(CardKey.status == status)

    total = (await db.execute(select(func.count()).select_from(base_query.subquery()))).scalar() or 0
    stmt = base_query.order_by(CardKey.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    cards = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [{
            "id": c.id, "key_code": c.key_code,
            "status": c.status.value if hasattr(c.status, 'value') else c.status,
            "plan_name": c.plan.name if c.plan else "",
            "used_by_user_id": c.used_by_user_id,
            "used_at": c.used_at.isoformat() if c.used_at else None,
            "batch_name": c.batch_name,
            "created_at": c.created_at.isoformat(),
        } for c in cards],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }
