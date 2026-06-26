"""
数据库初始化脚本
- 创建所有表
- 插入初始数据（会员套餐、管理员账号等）
- 支持 SQLite 和 MySQL
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import bcrypt
from app.db.session import engine, Base
from app.db.session import async_session_factory
from app.models import (
    User, MembershipPlan, Admin, CardKey, SystemConfig
)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def get_now():
    return datetime.now(timezone(timedelta(hours=8)))


async def init_db():
    """初始化数据库表结构"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建完成")


async def seed_data():
    """插入初始数据"""
    async with async_session_factory() as db:
        # 检查是否已有数据
        from sqlalchemy import select

        # 会员套餐
        existing_plans = (await db.execute(
            select(MembershipPlan).limit(1)
        )).scalar_one_or_none()

        if not existing_plans:
            plans = [
                MembershipPlan(
                    name="免费版",
                    plan_type="free",
                    price=Decimal("0.00"),
                    daily_parse_count=3,
                    daily_generate_count=1,
                    is_active=1,
                    sort_order=1,
                ),
                MembershipPlan(
                    name="基础版",
                    plan_type="basic",
                    price=Decimal("29.90"),
                    daily_parse_count=20,
                    daily_generate_count=5,
                    support_hd_export=True,
                    is_active=1,
                    sort_order=2,
                ),
                MembershipPlan(
                    name="专业版",
                    plan_type="premium",
                    price=Decimal("99.00"),
                    daily_parse_count=100,
                    daily_generate_count=50,
                    support_hd_export=True,
                    is_active=1,
                    sort_order=3,
                ),
                MembershipPlan(
                    name="企业版",
                    plan_type="enterprise",
                    price=Decimal("999.00"),
                    daily_parse_count=999,
                    daily_generate_count=500,
                    support_hd_export=True,
                    is_active=1,
                    sort_order=4,
                ),
            ]
            db.add_all(plans)
            await db.commit()
            print("会员套餐初始化完成")

        # 管理员账号
        existing_admin = (await db.execute(
            select(Admin).where(Admin.username == "admin")
        )).scalar_one_or_none()

        if not existing_admin:
            admin = Admin(
                username="admin",
                password_hash=hash_password("Admin@123"),
                role="super_admin",
                real_name="超级管理员",
                is_active=1,
            )
            db.add(admin)
            await db.commit()
            print("管理员账号初始化完成 (admin / Admin@123)")

        # 系统配置
        existing_config = (await db.execute(
            select(SystemConfig).limit(1)
        )).scalar_one_or_none()

        if not existing_config:
            configs = [
                SystemConfig(config_key="site_name", config_value="爆款短视频复刻平台", description="站点名称"),
                SystemConfig(config_key="free_daily_parse", config_value="3", description="免费用户每日解析次数"),
                SystemConfig(config_key="free_daily_generate", config_value="1", description="免费用户每日生成次数"),
                SystemConfig(config_key="registration_enabled", config_value="1", description="是否开放注册"),
                SystemConfig(config_key="default_membership", config_value="free", description="默认会员等级"),
            ]
            db.add_all(configs)
            await db.commit()
            print("系统配置初始化完成")

        # 测试用户（手机号格式）
        existing_user = (await db.execute(
            select(User).where(User.phone == "13800138000")
        )).scalar_one_or_none()

        if existing_user:
            # 更新已有用户信息
            existing_user.username = "13800138000"
            existing_user.password_hash = hash_password("13800138000")
            existing_user.nickname = "测试用户"
            await db.commit()
            print("测试用户已更新 (手机号: 13800138000 / 密码: 13800138000)")
        else:
            test_user = User(
                username="13800138000",
                phone="13800138000",
                password_hash=hash_password("13800138000"),
                nickname="测试用户",
                membership_level="free",
                remaining_credits=100,
                status="active",
            )
            db.add(test_user)
            await db.commit()
            print("测试用户创建完成 (手机号: 13800138000 / 密码: 13800138000)")

    print("初始数据插入完成")


async def main():
    await init_db()
    await seed_data()
    print("数据库初始化全部完成 ✓")


if __name__ == "__main__":
    asyncio.run(main())
