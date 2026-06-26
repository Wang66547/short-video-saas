"""
统一响应 Schema
"""
from typing import Generic, TypeVar, Optional, Any, List
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


class PageItem(BaseModel):
    """分页项"""
    page: int = 1
    size: int = 20
    total: int = 0
    pages: int = 0


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    code: int = 200
    message: str = "success"
    data: List[T] = []
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0
