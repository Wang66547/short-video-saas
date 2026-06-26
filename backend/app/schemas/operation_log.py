"""
操作日志 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OperationLogOut(BaseModel):
    """操作日志输出"""
    id: int
    user_id: Optional[int]
    operator_id: Optional[int]
    action: str
    target_type: str
    target_id: Optional[int]
    detail: Optional[str]
    ip_address: str
    status: str
    error_message: str
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogQuery(BaseModel):
    """操作日志查询条件"""
    action: Optional[str] = None
    target_type: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
