"""
Celery 异步任务队列配置
- Broker: Redis
- Backend: Redis
- Task 自动发现
- 开发环境无 Redis 时优雅降级
"""
from app.core.config import get_settings

settings = get_settings()

celery_app = None

try:
    from celery import Celery

    celery_app = Celery(
        "video_processor",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    celery_app.autodiscover_tasks(["app.tasks"])

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_soft_time_limit=3600,
        task_time_limit=7200,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_concurrency=4,
        task_track_started=True,
    )
except Exception:
    celery_app = None
