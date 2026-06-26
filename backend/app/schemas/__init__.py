"""
Pydantic Schema 模块
"""
from app.schemas.user import UserRegister, UserLogin, TokenPair, UserProfileUpdate, UserOut
from app.schemas.membership_plan import MembershipPlanCreate, MembershipPlanUpdate, MembershipPlanOut
from app.schemas.order import OrderCreate, OrderOut, OrderDetailOut
from app.schemas.parse_record import ParseRecordCreate, ParseRecordOut, ParseResult
from app.schemas.generate_record import GenerateRecordCreate, GenerateRecordOut, GenerateRecordEdit, SceneEditItem
from app.schemas.card_key import CardKeyRedeem, CardKeyOut, CardKeyGenerateRequest
from app.schemas.admin import AdminLogin, AdminStats
from app.schemas.base import SuccessResponse, ErrorResponse, PaginatedResponse

__all__ = [
    # User
    "UserRegister", "UserLogin", "TokenPair", "UserProfileUpdate", "UserOut",
    # Membership
    "MembershipPlanCreate", "MembershipPlanUpdate", "MembershipPlanOut",
    # Order
    "OrderCreate", "OrderOut", "OrderDetailOut",
    # Parse
    "ParseRecordCreate", "ParseRecordOut", "ParseResult",
    # Generate
    "GenerateRecordCreate", "GenerateRecordOut", "GenerateRecordEdit", "SceneEditItem",
    # CardKey
    "CardKeyRedeem", "CardKeyOut", "CardKeyGenerateRequest",
    # Admin
    "AdminLogin", "AdminStats",
    # Base
    "SuccessResponse", "ErrorResponse", "PaginatedResponse",
]
