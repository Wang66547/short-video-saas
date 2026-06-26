"""
用户业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import hash_password


async def get_user_by_phone(db: AsyncSession, phone: str) -> User:
    """通过手机号查询用户"""
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, phone: str, password: str, nickname: str = None) -> User:
    """创建新用户"""
    user = User(
        phone=phone,
        password_hash=hash_password(password),
        nickname=nickname or phone[-4:],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
