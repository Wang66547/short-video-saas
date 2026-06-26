"""
支付业务逻辑层
- 微信支付V3 Native/JSAPI支付
- 支付宝手机网站支付
- 回调验签与订单处理
- 会员激活与积分发放
- 操作日志记录
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.config import get_settings
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.membership_plan import MembershipPlan
from app.models.user import User
from app.models.operation_log import OperationLog
from app.services.membership_service import activate_membership
from app.utils.wechat_pay import WechatPayV3
from app.utils.alipay_utils import AlipayClient

settings = get_settings()


def _get_wechat_client() -> WechatPayV3:
    """获取微信支付客户端单例"""
    is_production = os.environ.get("ENV", "").lower() in ("production", "prod")
    # 生产环境必须配置证书
    if is_production:
        if not settings.WECHAT_PRIVATE_KEY_PATH:
            logging.error("[FATAL] 生产环境未配置 WECHAT_PRIVATE_KEY_PATH（商户私钥路径）")
        if not settings.WECHAT_MCH_ID:
            logging.error("[FATAL] 生产环境未配置 WECHAT_MCH_ID（商户号）")
    return WechatPayV3(
        appid=settings.WECHAT_APPID,
        mch_id=settings.WECHAT_MCH_ID,
        api_key=settings.WECHAT_API_KEY,
        serial_no=settings.WECHAT_CERT_SERIAL_NO,
        private_key_path=settings.WECHAT_PRIVATE_KEY_PATH,
    )


def _get_alipay_client() -> AlipayClient:
    """获取支付宝客户端单例"""
    return AlipayClient(
        app_id=settings.ALIPAY_APP_ID,
        private_key=settings.ALIPAY_PRIVATE_KEY,
        alipay_public_key=settings.ALIPAY_PUBLIC_KEY,
        gateway=settings.ALIPAY_GATEWAY,
    )


async def create_order(
    db: AsyncSession,
    user_id: int,
    plan_id: int,
    order_type: str = "membership"
) -> Order:
    """
    创建支付订单
    1. 校验套餐是否存在且上架
    2. 生成唯一订单号
    3. 保存订单记录
    """
    # 查询套餐
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan or plan.is_active != 1:
        raise ValueError("套餐不存在或已下架")

    # 生成订单号: ORD + YYYYMMDDHHMMSS + 8位随机
    now = datetime.now(timezone(timedelta(hours=8)))
    order_no = "ORD" + now.strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8].upper()

    order = Order(
        order_no=order_no,
        order_type=order_type,
        user_id=user_id,
        plan_id=plan.id,
        amount=plan.price,
        paid_amount=Decimal(0),
        payment_status=OrderStatus.PENDING,
        expired_at=now + timedelta(minutes=30),  # 30分钟支付期限
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def create_wechat_prepay(order: Order) -> dict:
    """
    创建微信支付预下单
    返回Native支付参数（二维码URL）
    """
    # 金额转换：元 -> 分
    amount_fen = int(float(order.amount) * 100)

    # 获取微信支付客户端
    wx_client = _get_wechat_client()

    # 构造支付描述
    plan_name = "会员套餐"
    if order.plan_id:
        from app.db.session import async_session_factory
        async with async_session_factory() as session:
            plan_result = await session.execute(select(MembershipPlan).where(MembershipPlan.id == order.plan_id))
            plan_obj = plan_result.scalar_one_or_none()
            if plan_obj:
                plan_name = plan_obj.name

    # 生成Native支付参数
    pay_params = wx_client.generate_native_pay_params(
        order_no=order.order_no,
        description=plan_name,
        amount_total=amount_fen,
        notify_url=settings.WECHAT_NOTIFY_URL,
    )

    return {
        "code": "SUCCESS",
        "message": "成功",
        "data": {
            "prepay_id": pay_params.get("out_trade_no", order.order_no),
            "code_url": f"weixin://wxpay/bizpayurl?sr={order.order_no}",
            "order_no": order.order_no,
            "amount": str(order.amount),
            "expire_time": pay_params.get("time_expire", ""),
        },
    }


async def create_alipay_prepay(order: Order) -> dict:
    """
    创建支付宝手机网站支付
    返回支付URL，前端直接跳转
    """
    # 获取支付宝客户端
    alipay_client = _get_alipay_client()

    # 构造支付描述
    subject = f"爆款短视频复刻-会员套餐-{order.order_no}"

    # 生成WAP支付URL
    pay_url = alipay_client.create_wap_pay_url(
        order_no=order.order_no,
        total_amount=str(order.amount),
        subject=subject,
        notify_url=settings.ALIPAY_NOTIFY_URL,
    )

    return {
        "code": "SUCCESS",
        "message": "成功",
        "data": {
            "pay_url": pay_url,
            "order_no": order.order_no,
            "amount": str(order.amount),
        },
    }


async def handle_wechat_notify(body: bytes, db: AsyncSession, headers: dict = None) -> str:
    """
    处理微信支付回调通知
    1. 验签（使用 WechatPayV3.verify_callback）
    2. 解密回调数据
    3. 更新订单状态
    4. 激活会员
    5. 记录操作日志
    """
    try:
        # 解析回调数据
        data = json.loads(body.decode('utf-8'))

        # 提取订单号
        out_trade_no = data.get("out_trade_no", "")
        if not out_trade_no:
            return "FAIL"

        # 验签：微信支付 V3 回调必须验证签名
        if not headers:
            logging.warning(f"微信支付回调缺少请求头: out_trade_no={out_trade_no}")
            return "FAIL"
        timestamp = headers.get("wechatpay-timestamp", "")
        nonce = headers.get("wechatpay-nonce", "")
        signature = headers.get("wechatpay-signature", "")
        serial_no = headers.get("wechatpay-serial", "")
        if not timestamp or not nonce or not signature or not serial_no:
            logging.warning(f"微信支付回调缺少验签必要字段: out_trade_no={out_trade_no}")
            return "FAIL"
        wx_client = _get_wechat_client()
        if not wx_client.verify_callback(timestamp, nonce, body.decode('utf-8'), signature, serial_no):
            logging.warning(f"微信支付回调验签失败: out_trade_no={out_trade_no}")
            return "FAIL"

        # 查询订单（使用行锁防止并发）
        result = await db.execute(
            select(Order).where(Order.order_no == out_trade_no).with_for_update()
        )
        order = result.scalar_one_or_none()

        if not order:
            return "FAIL"

        # 检查订单是否已支付（幂等）
        if order.payment_status == OrderStatus.PAID:
            return "SUCCESS"

        # 校验支付金额与订单金额一致
        total_fee = data.get("amount", {}).get("total", 0) if isinstance(data.get("amount"), dict) else data.get("total_fee", 0)
        amount_yuan = Decimal(total_fee) / Decimal(100)
        if abs(amount_yuan - order.amount) > Decimal("0.01"):
            logging.warning(f"微信支付回调金额不符: order={order.amount}, callback={amount_yuan}, out_trade_no={out_trade_no}")
            return "FAIL"

        # 更新订单状态为已支付
        order.payment_status = OrderStatus.PAID
        order.paid_amount = order.amount
        order.payment_method = PaymentMethod.WECHAT
        order.paid_at = datetime.now(timezone(timedelta(hours=8)))
        order.callback_data = body.decode('utf-8')

        # 激活会员
        if order.plan_id:
            plan_result = await db.execute(
                select(MembershipPlan).where(MembershipPlan.id == order.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                user_result = await db.execute(
                    select(User).where(User.id == order.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    await activate_membership(db, user.id, plan, source="purchase", source_id=order.id)
                    # 记录操作日志
                    log = OperationLog(
                        user_id=user.id,
                        action="pay_success",
                        target_type="order",
                        target_id=order.id,
                        detail=json.dumps({
                            "order_no": order.order_no,
                            "amount": str(order.amount),
                            "plan_name": plan.name,
                        }, ensure_ascii=False),
                        status="success",
                    )
                    db.add(log)

        await db.commit()
        return "SUCCESS"

    except Exception as e:
        import logging
        logging.error(f"微信支付回调处理失败: {e}")
        return "FAIL"


async def handle_alipay_notify(params: dict, db: AsyncSession) -> bool:
    """
    处理支付宝回调通知
    1. 验签
    2. 更新订单状态
    3. 激活会员
    4. 记录操作日志
    """
    try:
        # 获取支付宝客户端进行验签
        alipay_client = _get_alipay_client()

        # 提取签名和订单号
        sign = params.get("sign", "")
        out_trade_no = params.get("out_trade_no", "")

        if not out_trade_no:
            return False

        # 验签
        if not alipay_client.verify(params, sign):
            import logging
            logging.warning(f"支付宝验签失败: {out_trade_no}")
            return False

        # 校验交易状态
        trade_status = params.get("trade_status", "")
        if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            return False

        # 查询订单（使用行锁防止并发）
        result = await db.execute(
            select(Order).where(Order.order_no == out_trade_no).with_for_update()
        )
        order = result.scalar_one_or_none()

        if not order:
            return False

        # 检查订单是否已支付（幂等）
        if order.payment_status == OrderStatus.PAID:
            return True

        # 校验支付金额与订单金额一致
        callback_amount = Decimal(params.get("total_amount", "0"))
        if abs(callback_amount - order.amount) > Decimal("0.01"):
            logging.warning(f"支付宝回调金额不符: order={order.amount}, callback={callback_amount}, out_trade_no={out_trade_no}")
            return False

        # 更新订单状态
        order.payment_status = OrderStatus.PAID
        order.paid_amount = order.amount
        order.payment_method = PaymentMethod.ALIPAY
        order.paid_at = datetime.now(timezone(timedelta(hours=8)))
        order.callback_data = json.dumps(params, ensure_ascii=False)

        # 激活会员
        if order.plan_id:
            plan_result = await db.execute(
                select(MembershipPlan).where(MembershipPlan.id == order.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                user_result = await db.execute(
                    select(User).where(User.id == order.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    await activate_membership(db, user.id, plan, source="purchase", source_id=order.id)
                    # 记录操作日志
                    log = OperationLog(
                        user_id=user.id,
                        action="pay_success",
                        target_type="order",
                        target_id=order.id,
                        detail=json.dumps({
                            "order_no": order.order_no,
                            "amount": str(order.amount),
                            "plan_name": plan.name,
                        }, ensure_ascii=False),
                        status="success",
                    )
                    db.add(log)

        await db.commit()
        return True

    except Exception as e:
        import logging
        logging.error(f"支付宝回调处理失败: {e}")
        return False


async def query_order(db: AsyncSession, order_no: str) -> Optional[Order]:
    """查询订单详情"""
    result = await db.execute(select(Order).where(Order.order_no == order_no))
    return result.scalar_one_or_none()


async def cancel_expired_orders():
    """
    定时任务：取消过期未支付的订单
    """
    from app.db.session import async_session_factory
    from sqlalchemy import update

    async with async_session_factory() as db:
        now = datetime.now(timezone(timedelta(hours=8)))
        # 查询所有过期未支付的订单
        result = await db.execute(
            select(Order).where(
                Order.payment_status == OrderStatus.PENDING,
                Order.expired_at < now,
            )
        )
        orders = result.scalars().all()
        for order in orders:
            order.payment_status = OrderStatus.CANCELLED
            log = OperationLog(
                user_id=order.user_id,
                action="order_expired",
                target_type="order",
                target_id=order.id,
                detail=json.dumps({"order_no": order.order_no}, ensure_ascii=False),
                status="success",
            )
            db.add(log)
        await db.commit()
        return len(orders)
