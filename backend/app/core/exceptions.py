"""
全局异常处理器
统一错误响应格式，避免暴露内部堆栈信息
"""
import logging
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验失败：返回 422"""
    errors = []
    for err in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "参数校验失败",
            "data": {"errors": errors},
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 异常：返回对应状态码和详情"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """未捕获异常兜底：记录日志并返回 500"""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
        },
    )
