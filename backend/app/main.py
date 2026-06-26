"""
FastAPI 应用主入口
- 注册中间件（CORS、请求日志）
- 挂载各模块路由
- 定义全局异常处理器
- 启动/关闭事件钩子
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.middleware import setup_middleware
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.core.redis_client import close_redis
from app.api.router import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # 启动时初始化 Redis 等
    yield
    # 关闭时清理
    await close_redis()
    logger.info("Application shutdown complete")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="爆款短视频复刻SaaS平台 - API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ==================== 中间件 ====================
setup_middleware(app)

# ==================== 全局异常处理器 ====================
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ==================== 路由注册 ====================
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"code": 200, "message": "ok", "data": {"status": "running"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
