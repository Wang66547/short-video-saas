"""
支付路由
- 创建订单
- 发起微信支付（Native/JSAPI）
- 发起支付宝支付（WAP）
- 支付回调通知（微信/支付宝）
- 订单查询
- 订单列表
"""
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.membership_plan import MembershipPlan
from app.schemas.order import OrderCreate, OrderOut
from app.services.payment_service import (
    create_order,
    create_wechat_prepay,
    create_alipay_prepay,
    handle_wechat_notify,
    handle_alipay_notify,
    query_order,
)

router = APIRouter()


@router.post("/create-order", response_model=dict)
async def create_order_api(
    body: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建支付订单
    1. 校验套餐是否存在且上架
    2. 生成唯一订单号
    3. 保存订单记录
    """
    # 查询套餐
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == body.plan_id))
    plan = result.scalar_one_or_none()
    if not plan or plan.is_active != 1:
        raise HTTPException(status_code=404, detail="套餐不存在或已下架")

    # 创建订单
    order = await create_order(db, current_user.id, body.plan_id)

    return {
        "code": 201,
        "message": "订单创建成功",
        "data": {
            "order_no": order.order_no,
            "amount": str(order.amount),
            "expired_at": order.expired_at.isoformat() if order.expired_at else None,
        },
    }


@router.post("/wechat/prepay", response_model=dict)
async def wechat_prepay(
    order_no: str = Query(..., description="订单号"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发起微信支付预支付
    返回Native支付二维码URL
    """
    # 查询订单
    order = await query_order(db, order_no)
    if not order or order.payment_status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="订单不存在或已支付")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    # 创建微信支付预下单
    result = await create_wechat_prepay(order)
    return result


@router.post("/alipay/prepay", response_model=dict)
async def alipay_prepay(
    order_no: str = Query(..., description="订单号"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发起支付宝手机网站支付
    返回支付URL，前端直接跳转
    """
    # 查询订单
    order = await query_order(db, order_no)
    if not order or order.payment_status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="订单不存在或已支付")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    # 创建支付宝预下单
    result = await create_alipay_prepay(order)
    return result


@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    微信支付回调通知
    1. 解析回调数据
    2. 验签
    3. 更新订单状态
    4. 激活会员
    """
    body = await request.body()
    # 获取微信回调验签所需的 HTTP 头
    headers = dict(request.headers)
    result = await handle_wechat_notify(body, db, headers)
    if result == "SUCCESS":
        return {"code": "SUCCESS", "message": "成功"}
    return {"code": "FAIL", "message": "失败"}


@router.post("/alipay/notify")
async def alipay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    支付宝回调通知
    1. 解析回调参数
    2. 验签
    3. 更新订单状态
    4. 激活会员
    """
    form_data = await request.form()
    result = await handle_alipay_notify(dict(form_data), db)
    if result:
        return "<html>success</html>"
    return "<html>failure</html>"


@router.get("/detail", response_model=dict)
async def get_order_detail(
    order_no: str = Query(..., description="订单号"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询订单详情
    """
    order = await query_order(db, order_no)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此订单")

    # 获取关联套餐信息
    plan_name = ""
    if order.plan_id:
        plan_result = await db.execute(
            select(MembershipPlan).where(MembershipPlan.id == order.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan_name = plan.name

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "order_type": order.order_type,
            "amount": float(order.amount),
            "paid_amount": float(order.paid_amount),
            "payment_status": order.payment_status.value if hasattr(order.payment_status, 'value') else order.payment_status,
            "payment_method": order.payment_method.value if hasattr(order.payment_method, 'value') else order.payment_method,
            "plan_name": plan_name,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "expired_at": order.expired_at.isoformat() if order.expired_at else None,
            "created_at": order.created_at.isoformat(),
        },
    }


@router.get("/orders", response_model=dict)
async def list_orders(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的订单列表（分页）
    """
    offset = (page - 1) * size
    total = (await db.execute(
        select(func.count()).select_from(Order).where(Order.user_id == current_user.id)
    )).scalar() or 0

    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [OrderOut.model_validate(o) for o in orders],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }
