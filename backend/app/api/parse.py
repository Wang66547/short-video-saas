"""
视频解析路由（增强版）
- 创建解析任务（支持URL/文件上传）
- 批量解析任务
- 查询解析结果
- 权限校验（每日次数限制）
"""
import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.permissions import check_daily_usage
from app.models.user import User
from app.models.parse_record import ParseRecord, ParseStatus
from app.schemas.parse_record import ParseRecordCreate, ParseRecordOut
from app.services.credits_service import deduct_daily_parse
from app.core.config import get_settings
from app.services.batch_process_service import batch_service

settings = get_settings()
router = APIRouter()


async def analyze_video_task(record_id: int):
    """模拟视频解析任务（开发环境降级）"""
    import json
    from app.db.session import async_session_factory
    from app.models.parse_record import ParseRecord, ParseStatus

    async with async_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(select(ParseRecord).where(ParseRecord.id == record_id))
        record = result.scalar_one_or_none()
        if not record:
            return
        record.status = ParseStatus.PROCESSING
        record.progress = 50.0
        await db.commit()

        # 模拟解析结果
        mock_result = {
            "video_info": {
                "title": "模拟视频标题",
                "duration": 60,
                "width": 1080,
                "height": 1920,
            },
            "audio_track": {"url": "", "duration": 60},
            "subtitles": [
                {"start": 0, "end": 3, "text": "这是模拟的字幕"},
                {"start": 3, "end": 6, "text": "用于开发环境测试"},
            ],
            "scenes": [
                {"start": 0, "end": 10, "description": "场景1"},
                {"start": 10, "end": 20, "description": "场景2"},
            ],
        }
        record.result_json = json.dumps(mock_result, ensure_ascii=False)
        record.status = ParseStatus.SUCCESS
        record.progress = 100.0
        record.duration = 2.5
        await db.commit()


@router.post("/create", response_model=dict)
async def create_parse(
    body: ParseRecordCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建单个视频解析任务"""
    await check_daily_usage(current_user=current_user, db=db, task_type="parse")

    record = ParseRecord(
        user_id=current_user.id,
        video_url=body.video_url,
        status=ParseStatus.PENDING,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    await deduct_daily_parse(db, current_user.id)
    background_tasks.add_task(analyze_video_task, record.id)

    return {
        "code": 201,
        "message": "解析任务已创建",
        "data": {"record_id": record.id},
    }


@router.post("/upload", response_model=dict)
async def upload_and_parse(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传视频文件并创建解析任务"""
    await check_daily_usage(current_user=current_user, db=db, task_type="parse")

    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    file_ext = os.path.splitext(file.filename)[1].lower() or ".mp4"
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，仅支持: {', '.join(allowed_extensions)}"
        )
    
    max_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    file_size = 0
    file_uuid = str(uuid.uuid4())
    save_dir = os.path.join(settings.VIDEO_STORAGE_PATH, str(current_user.id))
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, f"{file_uuid}{file_ext}")
    with open(save_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > max_size:
                buffer.close()
                os.remove(save_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制，最大支持 {settings.MAX_VIDEO_SIZE_MB}MB"
                )
            buffer.write(chunk)

    record = ParseRecord(
        user_id=current_user.id,
        video_url=save_path,
        status=ParseStatus.PENDING,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    await deduct_daily_parse(db, current_user.id)
    background_tasks.add_task(analyze_video_task, record.id)

    return {
        "code": 201,
        "message": "视频上传成功，解析任务已创建",
        "data": {"record_id": record.id, "file_path": save_path},
    }


@router.post("/batch-create", response_model=dict)
async def batch_create_parse(
    body: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    批量创建解析任务
    接收 video_urls 列表，自动排队处理
    """
    video_urls = body.get("video_urls", [])
    if not video_urls:
        raise HTTPException(status_code=400, detail="请提供视频URL列表")
    if len(video_urls) > 50:
        raise HTTPException(status_code=400, detail="单次最多支持50个视频")

    # 检查额度
    from app.core.permissions import get_daily_limit
    daily_limit = get_daily_limit(current_user.membership_level, "parse")
    today_count = (await db.execute(
        select(func.count()).select_from(ParseRecord).where(
            ParseRecord.user_id == current_user.id,
            ParseRecord.created_at >= datetime.now(timezone(timedelta(hours=8))).replace(hour=0, minute=0, second=0),
        )
    )).scalar() or 0
    remaining = daily_limit - today_count

    if remaining < len(video_urls):
        raise HTTPException(
            status_code=403,
            detail=f"今日剩余解析次数不足（剩余{remaining}次，需要{len(video_urls)}次）",
        )

    # 创建批量任务
    task_id = await batch_service.create_batch_parse_task(
        user_id=current_user.id,
        video_urls=video_urls,
        platform=body.get("platform", "auto"),
    )

    # 逐个创建解析记录并提交任务
    created_ids = []
    for url in video_urls:
        record = ParseRecord(
            user_id=current_user.id,
            video_url=url,
            status=ParseStatus.PENDING,
        )
        db.add(record)
        await db.flush()
        created_ids.append(record.id)

    await db.commit()

    # 批量提交异步任务
    for rid in created_ids:
        background_tasks.add_task(analyze_video_task, rid)

    # 扣减次数
    for _ in created_ids:
        await deduct_daily_parse(db, current_user.id)

    return {
        "code": 201,
        "message": f"批量解析任务已创建（共{len(created_ids)}个视频，自动排队处理）",
        "data": {
            "batch_task_id": task_id,
            "record_ids": created_ids,
            "total": len(created_ids),
            "status": "queued",
        },
    }


@router.get("/batch-status/{task_id}", response_model=dict)
async def get_batch_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """查询批量任务状态"""
    status = await batch_service.get_batch_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    if status["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")

    return {
        "code": 200,
        "message": "success",
        "data": status,
    }


@router.get("/list", response_model=dict)
async def list_parses(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的解析记录列表"""
    offset = (page - 1) * size
    total = (await db.execute(
        select(func.count()).select_from(ParseRecord).where(ParseRecord.user_id == current_user.id)
    )).scalar() or 0

    result = await db.execute(
        select(ParseRecord)
        .where(ParseRecord.user_id == current_user.id)
        .order_by(ParseRecord.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    records = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [ParseRecordOut.model_validate(r) for r in records],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/{record_id}", response_model=dict)
async def get_parse(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个解析记录详情"""
    result = await db.execute(
        select(ParseRecord).where(ParseRecord.id == record_id, ParseRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="解析记录不存在")
    return {"code": 200, "message": "success", "data": ParseRecordOut.model_validate(record)}