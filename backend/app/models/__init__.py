"""
模型注册
确保所有模型在 Base.metadata 中注册
"""
from app.models.user import User
from app.models.membership_plan import MembershipPlan
from app.models.order import Order
from app.models.parse_record import ParseRecord
from app.models.generate_record import GenerateRecord
from app.models.admin import Admin
from app.models.card_key import CardKey, CardKeyBatch
from app.models.operation_log import OperationLog
from app.models.system_config import SystemConfig

__all__ = [
    "User", "MembershipPlan", "Order",
    "ParseRecord", "GenerateRecord",
    "Admin", "CardKey", "CardKeyBatch",
    "OperationLog", "SystemConfig",
]
