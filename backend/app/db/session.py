"""
数据库会话管理模块
使用 SQLAlchemy 2.0 异步引擎
提供连接池、会话工厂、依赖注入
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

_db_url = settings.DATABASE_URL
import os
_is_production = os.environ.get("ENV", "").lower() in ("production", "prod")
_engine_kwargs = dict(
    echo=settings.DEBUG if not _is_production else False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

if _db_url.startswith("sqlite"):
    _engine_kwargs.pop("pool_pre_ping", None)
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(_db_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有模型继承此类"""
    pass


async def get_db():
    """
    FastAPI 依赖注入：获取数据库会话
    使用 yield 模式，请求结束后自动关闭
    注意：不自动 commit，由业务逻辑自行控制提交时机
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
