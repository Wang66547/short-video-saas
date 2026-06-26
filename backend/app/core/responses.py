"""
全局统一响应格式
所有 API 接口返回固定结构: {"code": 200, "message": "success", "data": {...}}
配合全局异常处理器使用
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    data: Any = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    code: int = 200
    message: str = "success"
    data: list[T] = []
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0
