"""
中间件模块
- CORS 跨域配置
- 安全响应头
- 请求日志
- 限流标记（将用户ID/IP注入请求状态）
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录每个请求的方法、路径、状态码、耗时
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 将客户端IP注入请求状态，供后续限流使用
        # 生产环境应配置可信代理列表，只信任代理设置的 XFF
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取最右侧的可信IP（即最后一个代理添加的IP）
            ip_list = [ip.strip() for ip in forwarded.split(",")]
            request.state.client_ip = ip_list[-1] if ip_list else "unknown"
        else:
            request.state.client_ip = request.client.host if request.client else "unknown"

        response = await call_next(request)

        # 记录请求耗时
        process_time = time.time() - start_time
        logger.info(
            f"%s %s -> %s (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        return response


def setup_middleware(app):
    """
    统一注册所有中间件到 FastAPI 应用
    :param app: FastAPI 应用实例
    """
    from app.core.config import get_settings
    settings = get_settings()

    # CORS 跨域中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    # 安全响应头中间件
    app.add_middleware(SecurityHeadersMiddleware)

    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
