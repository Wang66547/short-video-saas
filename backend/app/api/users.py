"""
用户管理路由
- 个人资料更新 / 密码修改 / 用户列表（管理员）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import hash_password, verify_password, get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin
from app.schemas.user import UserProfileUpdate, UserOut

router = APIRouter()


@router.put("/profile", response_model=dict)
async def update_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新个人资料"""
    if body.nickname:
        current_user.nickname = body.nickname
    if body.avatar:
        current_user.avatar = body.avatar
    await db.commit()
    return {"code": 200, "message": "更新成功", "data": {"nickname": current_user.nickname}}


@router.put("/password", response_model=dict)
async def change_password(
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码"""
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")
    current_user.password_hash = hash_password(new_password)
    await db.commit()
    
    from app.core.redis_client import increment_user_token_version
    await increment_user_token_version(current_user.id)
    
    return {"code": 200, "message": "密码修改成功", "data": None}


@router.get("/list", response_model=dict)
async def list_users(
    page: int = 1,
    size: int = 20,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（管理员）"""
    offset = (page - 1) * size
    total = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(size)
    )
    users = result.scalars().all()
    return {
        "code": 200, "message": "success",
        "data": [UserOut.model_validate(u) for u in users],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }
