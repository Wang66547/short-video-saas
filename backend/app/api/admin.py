"""
管理后台路由
- 管理员登录
- 数据统计面板
- 用户管理（搜索、修改会员时长/点数、禁用启用）
- 订单管理（全量列表、筛选、详情、手动补单）
- 套餐管理（增删改查、排序、上下架）
- 系统配置管理
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.db.session import get_db
from app.core.security import hash_password, verify_password, get_current_admin, create_access_token
from app.models.user import User
from app.models.admin import Admin
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.membership_plan import MembershipPlan
from app.models.parse_record import ParseRecord, ParseStatus
from app.models.generate_record import GenerateRecord, GenerateStatus
from app.models.operation_log import OperationLog
from app.models.system_config import SystemConfig
from app.schemas.admin import (
    AdminLogin, AdminStats,
    UserManageOut, UserSearchRequest, UserUpdateRequest,
    OrderManageOut, OrderSearchRequest, ManualOrderRequest,
    StatsTrendResponse, TrendPoint,
    PlanManageOut, PlanCreateRequest, PlanUpdateRequest,
    SystemConfigOut, SystemConfigUpdateRequest,
)
from app.services.membership_service import activate_membership

router = APIRouter()


# ==================== 管理员登录 ====================

@router.post("/login", response_model=dict)
async def admin_login(body: AdminLogin, db: AsyncSession = Depends(get_db)):
    """
    管理员登录
    1. 从 admins 表校验账号密码
    2. 返回 JWT token（含 admin 角色标识）
    """
    from app.core.redis_client import get_redis
    
    redis = await get_redis()
    fail_key = f"login_fail:admin:{body.username}"
    
    if redis:
        fail_count = await redis.get(fail_key)
        if fail_count and int(fail_count) >= 5:
            raise HTTPException(status_code=429, detail="登录失败次数过多，请15分钟后再试")
    
    result = await db.execute(
        select(Admin).where(Admin.username == body.username)
    )
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(body.password, admin.password_hash or ""):
        if redis:
            await redis.incr(fail_key)
            await redis.expire(fail_key, 900)
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if admin.is_active != 1:
        raise HTTPException(status_code=403, detail="管理员账号已被禁用")
    
    if redis:
        await redis.delete(fail_key)
    
    from app.core.redis_client import get_user_token_version
    token_version = await get_user_token_version(admin.id)

    token_data = {"sub": str(admin.id), "role": admin.role}
    token = create_access_token(token_data, token_version=token_version)

    return {
        "code": 200,
        "message": "登录成功",
        "data": {"token": token, "role": admin.role},
    }


# ==================== 数据统计 ====================

@router.get("/stats", response_model=dict)
async def get_stats(current_admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """获取管理后台统计数据"""
    

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    active_users = (await db.execute(
        select(func.count()).select_from(User).where(User.status == "active")
    )).scalar() or 0

    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar() or 0
    today_start = datetime.now(timezone(timedelta(hours=8))).replace(hour=0, minute=0, second=0)
    today_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.created_at >= today_start)
    )).scalar() or 0

    paid_result = await db.execute(
        select(func.sum(Order.paid_amount)).where(Order.payment_status == OrderStatus.PAID)
    )
    total_revenue = float(paid_result.scalar() or 0)
    today_result = await db.execute(
        select(func.sum(Order.paid_amount)).where(
            Order.payment_status == OrderStatus.PAID, Order.created_at >= today_start
        )
    )
    today_revenue = float(today_result.scalar() or 0)

    total_parses = (await db.execute(select(func.count()).select_from(ParseRecord))).scalar() or 0
    total_generates = (await db.execute(select(func.count()).select_from(GenerateRecord))).scalar() or 0
    pending_tasks = (await db.execute(
        select(func.count()).select_from(ParseRecord).where(ParseRecord.status == ParseStatus.PENDING)
    )).scalar() or 0

    return {
        "code": 200, "message": "success",
        "data": AdminStats(
            total_users=total_users,
            active_users=active_users,
            total_orders=total_orders,
            today_orders=today_orders,
            total_revenue=total_revenue,
            today_revenue=today_revenue,
            total_parses=total_parses,
            total_generates=total_generates,
            pending_tasks=pending_tasks,
        ),
    }


@router.get("/stats/trend", response_model=dict)
async def get_stats_trend(
    days: int = Query(default=7, ge=1, le=30, description="天数: 7或30"),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取趋势数据（7天/30天）
    返回每日注册量、订单量、营收、解析/生成次数
    """
    

    now = datetime.now(timezone(timedelta(hours=8)))
    trend_days = []
    for i in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        trend_days.append((day_start.strftime("%Y-%m-%d"), day_start, day_end))

    # 注册量趋势
    reg_stmts = []
    for _, ds, de in trend_days:
        reg_stmts.append(select(func.count()).select_from(User).where(
            and_(User.created_at >= ds, User.created_at < de)
        ))
    registrations = [(await db.execute(s)).scalar() or 0 for s in reg_stmts]

    # 订单量趋势
    ord_stmts = []
    for _, ds, de in trend_days:
        ord_stmts.append(select(func.count()).select_from(Order).where(
            and_(Order.created_at >= ds, Order.created_at < de)
        ))
    orders = [(await db.execute(s)).scalar() or 0 for s in ord_stmts]

    # 营收趋势
    rev_stmts = []
    for _, ds, de in trend_days:
        rev_stmts.append(select(func.sum(Order.paid_amount)).where(
            and_(Order.payment_status == OrderStatus.PAID, Order.paid_at >= ds, Order.paid_at < de)
        ))
    revenue = [float((await db.execute(s)).scalar() or 0) for s in rev_stmts]

    # 解析次数趋势
    par_stmts = []
    for _, ds, de in trend_days:
        par_stmts.append(select(func.count()).select_from(ParseRecord).where(
            and_(ParseRecord.created_at >= ds, ParseRecord.created_at < de)
        ))
    parses = [(await db.execute(s)).scalar() or 0 for s in par_stmts]

    # 生成次数趋势
    gen_stmts = []
    for _, ds, de in trend_days:
        gen_stmts.append(select(func.count()).select_from(GenerateRecord).where(
            and_(GenerateRecord.created_at >= ds, GenerateRecord.created_at < de)
        ))
    generates = [(await db.execute(s)).scalar() or 0 for s in gen_stmts]

    def build_trend(data, fmt=float):
        return [TrendPoint(date=d, value=fmt(v)) for d, v in zip([t[0] for t in trend_days], data)]

    return {
        "code": 200, "message": "success",
        "data": StatsTrendResponse(
            registrations=build_trend(registrations, int),
            orders=build_trend(orders, int),
            revenue=build_trend(revenue, float),
            parses=build_trend(parses, int),
            generates=build_trend(generates, int),
        ),
    }


# ==================== 用户管理 ====================

@router.get("/users", response_model=dict)
async def admin_list_users(
    keyword: str = Query(default="", description="搜索关键词（手机号/昵称）"),
    status: str = Query(default="", description="状态筛选: active/banned"),
    membership_level: str = Query(default="", description="会员等级筛选"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取用户列表（支持搜索和筛选）"""
    

    conditions = []
    if keyword:
        conditions.append(or_(
            User.phone.like(f"%{keyword}%"),
            User.nickname.like(f"%{keyword}%"),
        ))
    if status:
        conditions.append(User.status == status)
    if membership_level:
        conditions.append(User.membership_level == membership_level)

    base_query = select(User)
    if conditions:
        base_query = base_query.where(and_(*conditions))

    total = (await db.execute(select(func.count()).select_from(base_query.subquery()))).scalar() or 0

    offset = (page - 1) * size
    stmt = base_query.order_by(User.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [{
            "id": u.id, "phone": u.phone, "nickname": u.nickname,
            "avatar": u.avatar, "membership_level": u.membership_level,
            "membership_expire_at": u.membership_expire_at.isoformat() if u.membership_expire_at else None,
            "remaining_credits": u.remaining_credits, "status": u.status,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat(),
        } for u in users],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/users/{user_id}", response_model=dict)
async def admin_get_user(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取单个用户详情"""
    

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 200, "message": "success",
        "data": {
            "id": user.id, "phone": user.phone, "nickname": user.nickname,
            "avatar": user.avatar, "membership_level": user.membership_level,
            "membership_expire_at": user.membership_expire_at.isoformat() if user.membership_expire_at else None,
            "remaining_credits": user.remaining_credits, "status": user.status,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.put("/users/{user_id}", response_model=dict)
async def admin_update_user(
    user_id: int,
    body: UserUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    手动修改用户信息
    支持：修改会员等级、会员到期时间、剩余点数、状态
    """
    

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.nickname is not None:
        user.nickname = body.nickname
    if body.membership_level is not None:
        user.membership_level = body.membership_level
    if body.membership_expire_at is not None:
        user.membership_expire_at = body.membership_expire_at
    if body.remaining_credits is not None:
        user.remaining_credits = body.remaining_credits
    if body.status is not None:
        user.status = body.status

    await db.commit()
    await db.refresh(user)

    return {
        "code": 200,
        "message": "用户信息更新成功",
        "data": {
            "id": user.id, "nickname": user.nickname,
            "membership_level": user.membership_level,
            "remaining_credits": user.remaining_credits,
            "status": user.status,
        },
    }


@router.put("/users/{user_id}/toggle", response_model=dict)
async def toggle_user_status(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用用户"""
    

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.status = "banned" if user.status == "active" else "active"
    await db.commit()

    return {
        "code": 200,
        "message": f"用户已{'禁用' if user.status == 'banned' else '启用'}",
        "data": None,
    }


# ==================== 订单管理 ====================

@router.get("/orders", response_model=dict)
async def admin_list_orders(
    keyword: str = Query(default="", description="订单号/用户ID搜索"),
    status: str = Query(default="", description="状态筛选"),
    user_id: int = Query(default=None, description="用户ID筛选"),
    start_date: str = Query(default="", description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(default="", description="结束日期 YYYY-MM-DD"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取订单列表（支持搜索和筛选）"""
    

    conditions = []
    if keyword:
        conditions.append(or_(
            Order.order_no.like(f"%{keyword}%"),
            Order.user_id == int(keyword) if keyword.isdigit() else False,
        ))
    if status:
        conditions.append(Order.payment_status == status)
    if user_id:
        conditions.append(Order.user_id == user_id)
    if start_date:
        conditions.append(Order.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        conditions.append(Order.created_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    base_query = select(Order)
    if conditions:
        base_query = base_query.where(and_(*conditions))

    total = (await db.execute(select(func.count()).select_from(base_query.subquery()))).scalar() or 0

    offset = (page - 1) * size
    stmt = base_query.order_by(Order.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [{
            "id": o.id, "order_no": o.order_no, "user_id": o.user_id,
            "amount": float(o.amount), "paid_amount": float(o.paid_amount),
            "payment_status": o.payment_status.value if hasattr(o.payment_status, 'value') else o.payment_status,
            "payment_method": o.payment_method.value if hasattr(o.payment_method, 'value') else o.payment_method,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "created_at": o.created_at.isoformat(),
        } for o in orders],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/orders/{order_no}", response_model=dict)
async def admin_get_order(
    order_no: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取订单详情"""
    

    result = await db.execute(select(Order).where(Order.order_no == order_no))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 获取关联用户和套餐信息
    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalar_one_or_none()

    plan_name = ""
    if order.plan_id:
        plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == order.plan_id))
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan_name = plan.name

    return {
        "code": 200, "message": "success",
        "data": {
            "id": order.id, "order_no": order.order_no, "order_type": order.order_type,
            "user_id": order.user_id, "user_nickname": user.nickname if user else "",
            "plan_id": order.plan_id, "plan_name": plan_name,
            "amount": float(order.amount), "paid_amount": float(order.paid_amount),
            "payment_method": order.payment_method.value if hasattr(order.payment_method, 'value') else order.payment_method,
            "payment_status": order.payment_status.value if hasattr(order.payment_status, 'value') else order.payment_status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "expired_at": order.expired_at.isoformat() if order.expired_at else None,
            "callback_data": order.callback_data,
            "created_at": order.created_at.isoformat(),
        },
    }


@router.post("/orders/{order_no}/manual-pay", response_model=dict)
async def admin_manual_pay(
    order_no: str,
    body: ManualOrderRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    手动补单
    1. 校验订单是否存在且未支付
    2. 更新订单状态为已支付
    3. 激活会员
    4. 记录操作日志
    """
    

    result = await db.execute(select(Order).where(Order.order_no == order_no))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.payment_status == OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="订单已支付，无需补单")

    # 更新订单状态
    order.payment_status = OrderStatus.PAID
    order.paid_amount = Decimal(str(body.paid_amount))
    order.payment_method = PaymentMethod.WECHAT if body.payment_method == "wechat" else PaymentMethod.ALIPAY
    order.paid_at = datetime.now(timezone(timedelta(hours=8)))

    # 激活会员
    if order.plan_id:
        plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == order.plan_id))
        plan = plan_result.scalar_one_or_none()
        if plan:
            user_result = await db.execute(select(User).where(User.id == order.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                await activate_membership(db, user.id, plan, source="manual_pay", source_id=order.id)

    await db.commit()

    return {
        "code": 200,
        "message": "补单成功",
        "data": {"order_no": order.order_no},
    }


# ==================== 套餐管理 ====================

@router.get("/plans", response_model=dict)
async def admin_list_plans(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取所有套餐列表"""
    

    total = (await db.execute(select(func.count()).select_from(MembershipPlan))).scalar() or 0
    offset = (page - 1) * size
    stmt = select(MembershipPlan).order_by(MembershipPlan.sort_order.asc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    plans = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [{
            "id": p.id, "name": p.name, "plan_type": p.plan_type,
            "price": float(p.price), "original_price": float(p.original_price) if p.original_price else None,
            "daily_parse_count": p.daily_parse_count, "daily_generate_count": p.daily_generate_count,
            "support_hd_export": p.support_hd_export, "sort_order": p.sort_order,
            "is_active": p.is_active, "created_at": p.created_at.isoformat(),
        } for p in plans],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.post("/plans", response_model=dict)
async def admin_create_plan(
    body: PlanCreateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员创建会员套餐"""
    

    plan = MembershipPlan(
        name=body.name, plan_type=body.plan_type, price=Decimal(str(body.price)),
        original_price=Decimal(str(body.original_price)) if body.original_price else None,
        daily_parse_count=body.daily_parse_count, daily_generate_count=body.daily_generate_count,
        support_hd_export=body.support_hd_export, sort_order=body.sort_order, is_active=body.is_active,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {
        "code": 201, "message": "套餐创建成功",
        "data": {"id": plan.id, "name": plan.name},
    }


@router.put("/plans/{plan_id}", response_model=dict)
async def admin_update_plan(
    plan_id: int,
    body: PlanUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新会员套餐"""
    

    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    if body.name is not None: plan.name = body.name
    if body.plan_type is not None: plan.plan_type = body.plan_type
    if body.price is not None: plan.price = Decimal(str(body.price))
    if body.original_price is not None: plan.original_price = Decimal(str(body.original_price)) if body.original_price else None
    if body.daily_parse_count is not None: plan.daily_parse_count = body.daily_parse_count
    if body.daily_generate_count is not None: plan.daily_generate_count = body.daily_generate_count
    if body.support_hd_export is not None: plan.support_hd_export = body.support_hd_export
    if body.sort_order is not None: plan.sort_order = body.sort_order
    if body.is_active is not None: plan.is_active = body.is_active

    await db.commit()
    await db.refresh(plan)

    return {
        "code": 200, "message": "套餐更新成功",
        "data": {"id": plan.id, "name": plan.name},
    }


@router.delete("/plans/{plan_id}", response_model=dict)
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

    return {"code": 200, "message": "套餐已下架", "data": None}


@router.put("/plans/{plan_id}/toggle", response_model=dict)
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


# ==================== 系统配置 ====================

SENSITIVE_CONFIG_KEYS = {
    "wechat_api_key", "alipay_private_key", "alipay_public_key",
    "aliyun_access_key_secret", "jimeng_api_key", "kling_api_key",
}


def _mask_sensitive_value(key: str, value: str) -> str:
    """对敏感配置值进行脱敏处理"""
    if key in SENSITIVE_CONFIG_KEYS and value:
        if len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]
    return value


@router.get("/configs", response_model=dict)
async def admin_list_configs(
    category: str = Query(default="", description="配置分类筛选"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取系统配置列表（敏感字段脱敏）"""
    

    stmt = select(SystemConfig)
    if category:
        stmt = stmt.where(SystemConfig.category == category)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    offset = (page - 1) * size
    stmt = stmt.order_by(SystemConfig.category, SystemConfig.config_key).offset(offset).limit(size)
    result = await db.execute(stmt)
    configs = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [{
            "id": c.id, "key": c.config_key,
            "value": _mask_sensitive_value(c.config_key, c.config_value),
            "category": c.category, "description": c.description,
            "is_public": c.is_public,
            "is_sensitive": c.config_key in SENSITIVE_CONFIG_KEYS,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        } for c in configs],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/configs/{key}", response_model=dict)
async def admin_get_config(
    key: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取单个配置项"""
    

    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return {
        "code": 200, "message": "success",
        "data": {
            "id": config.id, "key": config.config_key, "value": config.config_value,
            "category": config.category, "description": config.description,
            "is_public": config.is_public, "updated_at": config.updated_at.isoformat(),
        },
    }


@router.put("/configs", response_model=dict)
async def admin_update_config(
    body: SystemConfigUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新系统配置"""
    

    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == body.key))
    config = result.scalar_one_or_none()

    if not config:
        config = SystemConfig(
            config_key=body.key, config_value=body.value, category=body.category,
            description=body.description or "", is_public=body.is_public,
        )
        db.add(config)
    else:
        config.config_value = body.value
        if body.category: config.category = body.category
        if body.description: config.description = body.description
        config.is_public = body.is_public

    await db.commit()
    await db.refresh(config)

    return {
        "code": 200, "message": "配置更新成功",
        "data": {"key": config.config_key, "value": config.config_value},
    }


@router.post("/configs/init-default", response_model=dict)
async def admin_init_default_configs(current_admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """初始化默认系统配置（首次部署时调用）"""
    

    from app.core.config import get_settings
    settings = get_settings()

    default_configs = [
        # 支付配置
        ("wechat_appid", settings.WECHAT_APPID, "payment", "微信支付AppID"),
        ("wechat_mch_id", settings.WECHAT_MCH_ID, "payment", "微信支付商户号"),
        ("wechat_api_key", settings.WECHAT_API_KEY, "payment", "微信支付APIv3密钥"),
        ("alipay_app_id", settings.ALIPAY_APP_ID, "payment", "支付宝应用ID"),
        ("alipay_private_key", settings.ALIPAY_PRIVATE_KEY, "payment", "支付宝应用私钥"),
        ("alipay_public_key", settings.ALIPAY_PUBLIC_KEY, "payment", "支付宝公钥"),
        # 限流配置
        ("rate_limit_per_minute", str(settings.RATE_LIMIT_PER_MINUTE), "limit", "每分钟限流次数"),
        ("rate_limit_per_day", str(settings.RATE_LIMIT_PER_DAY), "limit", "每日限流次数"),
        # 免费用户额度
        ("free_daily_parse_limit", str(settings.FREE_DAILY_PARSE_LIMIT), "limit", "免费用户每日解析次数"),
        ("free_daily_generate_limit", str(settings.FREE_DAILY_GENERATE_LIMIT), "limit", "免费用户每日生成次数"),
        ("basic_daily_parse_limit", str(settings.BASIC_DAILY_PARSE_LIMIT), "limit", "基础会员每日解析次数"),
        ("basic_daily_generate_limit", str(settings.BASIC_DAILY_GENERATE_LIMIT), "limit", "基础会员每日生成次数"),
        ("premium_daily_parse_limit", str(settings.PREMIUM_DAILY_PARSE_LIMIT), "limit", "高级会员每日解析次数"),
        ("premium_daily_generate_limit", str(settings.PREMIUM_DAILY_GENERATE_LIMIT), "limit", "高级会员每日生成次数"),
        # 短信配置
        ("aliyun_access_key_id", settings.ALIBABA_CLOUD_ACCESS_KEY_ID, "sms", "阿里云AccessKey ID"),
        ("aliyun_access_key_secret", settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET, "sms", "阿里云AccessKey Secret"),
        ("aliyun_sms_template_id", settings.ALIBABA_CLOUD_SMS_TEMPLATE_ID, "sms", "短信模板ID"),
        ("aliyun_sms_sign_name", settings.ALIBABA_CLOUD_SIGN_NAME, "sms", "短信签名"),
        # AI服务配置
        ("jimeng_api_key", settings.JIMENG_API_KEY, "ai", "即梦API密钥"),
        ("kling_api_key", settings.KLING_API_KEY, "ai", "可灵API密钥"),
    ]

    count = 0
    for key, value, category, description in default_configs:
        result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key))
        existing = result.scalar_one_or_none()
        if not existing:
            config = SystemConfig(config_key=key, config_value=value, category=category, description=description)
            db.add(config)
            count += 1

    await db.commit()
    return {"code": 200, "message": f"初始化 {count} 条默认配置", "data": {"count": count}}
