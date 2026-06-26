"""
卡密业务逻辑
"""
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.card_key import CardKey, CardKeyStatus


async def generate_card_keys(db: AsyncSession, plan_id: int, count: int, prefix: str = "", length: int = 20) -> list:
    """批量生成卡密"""
    chars = string.ascii_uppercase + string.digits
    keys = []
    for _ in range(count):
        random_part = "".join(random.choices(chars, k=length))
        key_code = prefix + random_part
        card = CardKey(key_code=key_code, plan_id=plan_id)
        db.add(card)
        keys.append(key_code)
    await db.commit()
    return keys


async def verify_card_key(db: AsyncSession, key_code: str) -> dict:
    """校验卡密有效性"""
    result = await db.execute(select(CardKey).where(CardKey.key_code == key_code))
    card = result.scalar_one_or_none()
    if not card:
        return {"valid": False, "error": "卡密不存在"}
    if card.status != CardKeyStatus.UNUSED:
        return {"valid": False, "error": "卡密已被使用或已过期"}
    return {"valid": True, "plan_id": card.plan_id}
