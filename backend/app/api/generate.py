"""
视频生成路由（增强版）
- 创建生成任务（支持复刻编辑）
- 文案改写（AI降重）
- 配音合成（TTS）
- 批量生成
- 查询生成结果
- 权限校验（每日次数限制）
"""
import os
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.permissions import check_daily_usage
from app.models.user import User
from app.models.generate_record import GenerateRecord, GenerateStatus, GenerateMode
from app.models.parse_record import ParseRecord
from app.schemas.generate_record import (
    GenerateRecordCreate, GenerateRecordOut,
    GenerateRecordEdit, AIGenerationParams,
    SceneEditItem, VoiceToneSelect, MaterialReplace
)
from app.schemas.base import SuccessResponse
from app.services.credits_service import deduct_daily_generate, consume_credits
from app.services.copywriting_service import copywriting_service, REWRITE_MODES
from app.services.tts_voice_service import tts_service, VOICE_TONES
from app.services.batch_process_service import batch_service
from app.tasks.video_tasks import generate_video_task
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


# ==================== 文案改写 ====================

@router.post("/rewrite-script", response_model=dict)
async def rewrite_script(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """
    AI 文案改写
    POST /api/generate/rewrite-script
    Body: { "script": "...", "mode": "synonym|rewrite|style_change|optimize" }
    """
    script = body.get("script", "")
    if not script:
        raise HTTPException(status_code=400, detail="请提供要改写的文案")

    mode = body.get("mode", "synonym")
    if mode not in REWRITE_MODES:
        raise HTTPException(status_code=400, detail=f"不支持的改写模式: {mode}")

    temperature = body.get("temperature", 0.7)

    try:
        result = await copywriting_service.rewrite_script(script, mode, temperature)
        return {
            "code": 200,
            "message": "文案改写成功",
            "data": result,
            "is_mock": False,
        }
    except Exception as e:
        # AI 服务异常时返回 mock 结果，但明确标记
        return {
            "code": 200,
            "message": f"改写服务暂时不可用，已返回模拟结果（原因: {str(e)[:50]}）",
            "data": {
                "original": script,
                "rewritten": f"[模拟改写] {script}",
                "mode": mode,
                "mode_name": REWRITE_MODES[mode]["name"],
                "word_count_original": len(script),
                "word_count_rewritten": len(script),
            },
            "is_mock": True,
        }


@router.get("/rewrite-modes", response_model=dict)
async def get_rewrite_modes():
    """获取可用的文案改写模式"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            mode: {"name": cfg["name"], "desc": cfg["desc"]}
            for mode, cfg in REWRITE_MODES.items()
        },
    }


# ==================== 配音服务 ====================

@router.post("/synthesize-voice", response_model=dict)
async def synthesize_voice(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """
    AI 语音合成
    POST /api/generate/synthesize-voice
    Body: { "text": "...", "voice": "female_warm", "speed": 1.0 }
    """
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="请提供要合成的文本")

    voice = body.get("voice", "female_warm")
    speed = body.get("speed", 1.0)
    pitch = body.get("pitch", 0)
    volume = body.get("volume", 50)
    output_format = body.get("format", "mp3")

    result = await tts_service.synthesize(
        text=text,
        voice=voice,
        speed=speed,
        pitch=pitch,
        volume=volume,
        output_format=output_format,
    )

    return {
        "code": 200 if result.get("status") == "success" else 500,
        "message": "语音合成成功" if result.get("status") == "success" else "合成失败",
        "data": result,
    }


@router.get("/voices", response_model=dict)
async def get_voices(provider: str = "ali"):
    """获取可用音色列表"""
    voices = await tts_service.get_available_voices(provider)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "provider": provider,
            "voices": {
                k: {"name": v["name"], "gender": v["gender"], "description": v["description"]}
                for k, v in voices.items()
            },
        },
    }


# ==================== 平台优化 ====================

@router.post("/optimize-for-platform", response_model=dict)
async def optimize_for_platform(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """
    针对特定平台优化文案
    POST /api/generate/optimize
    Body: { "script": "...", "platform": "douyin|kuaishou|xiaohongshu" }
    """
    script = body.get("script", "")
    platform = body.get("platform", "douyin")

    if not script:
        raise HTTPException(status_code=400, detail="请提供文案")

    try:
        result = await copywriting_service.optimize_script_for_platform(script, platform)
        return {
            "code": 200,
            "message": "优化成功",
            "data": result,
        }
    except Exception as e:
        return {
            "code": 200,
            "message": "优化完成（模拟结果）",
            "data": {"original": script, "optimized": f"[优化] {script}", "platform": platform},
        }


# ==================== 生成任务 ====================

@router.post("/create", response_model=dict)
async def create_generate(
    body: GenerateRecordCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建视频生成任务"""
    await check_daily_usage(current_user=current_user, db=db, task_type="generate")

    record = GenerateRecord(
        user_id=current_user.id,
        parse_id=body.parse_id,
        generate_mode=body.generate_mode,
        edited_script=body.edited_script or "",
        edited_scenes=body.edited_scenes or "[]",
        voice_tone=body.voice_tone or "",
        replace_materials=body.replace_materials or "[]",
        aspect_ratio=body.aspect_ratio,
        ai_platform=body.ai_platform,
        generation_params=body.generation_params or "{}",
        status=GenerateStatus.PENDING,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    await deduct_daily_generate(db, current_user.id)
    background_tasks.add_task(generate_video_task, record.id)

    return {
        "code": 201,
        "message": "生成任务已创建",
        "data": {"record_id": record.id},
    }


@router.post("/batch-create", response_model=dict)
async def batch_create_generate(
    body: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    批量创建生成任务
    Body: { "parse_ids": [1,2,3], "generate_params": {...} }
    """
    parse_ids = body.get("parse_ids", [])
    if not parse_ids:
        raise HTTPException(status_code=400, detail="请提供解析记录ID列表")
    if len(parse_ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多支持20个生成任务")

    # 检查额度
    daily_count = (await db.execute(
        select(func.count()).select_from(GenerateRecord).where(
            GenerateRecord.user_id == current_user.id,
            GenerateRecord.created_at >= datetime.now(timezone(timedelta(hours=8))).replace(hour=0, minute=0, second=0),
        )
    )).scalar() or 0

    limit = {"free": 1, "basic": 5, "premium": 20}.get(current_user.membership_level, 1)
    if daily_count + len(parse_ids) > limit:
        raise HTTPException(
            status_code=403,
            detail=f"今日生成次数已达上限（{limit}次）",
        )

    # 创建批量任务
    task_id = await batch_service.create_batch_generate_task(
        user_id=current_user.id,
        parse_ids=parse_ids,
        generate_params=body.get("generate_params", {}),
    )

    # 逐个创建生成记录
    created_ids = []
    for pid in parse_ids:
        record = GenerateRecord(
            user_id=current_user.id,
            parse_id=pid,
            generate_mode=body.get("generate_mode", "ai_generate"),
            edited_script=body.get("edited_script", ""),
            edited_scenes=body.get("edited_scenes", "[]"),
            voice_tone=body.get("voice_tone", ""),
            aspect_ratio=body.get("aspect_ratio", "9:16"),
            ai_platform=body.get("ai_platform", "jimeng"),
            generation_params=json.dumps(body.get("generate_params", {}), ensure_ascii=False),
            status=GenerateStatus.PENDING,
        )
        db.add(record)
        await db.flush()
        created_ids.append(record.id)

    await db.commit()

    # 批量提交异步任务
    for rid in created_ids:
        background_tasks.add_task(generate_video_task, rid)

    # 扣减次数
    for _ in created_ids:
        await deduct_daily_generate(db, current_user.id)

    return {
        "code": 201,
        "message": f"批量生成任务已创建（共{len(created_ids)}个，自动排队处理）",
        "data": {
            "batch_task_id": task_id,
            "record_ids": created_ids,
            "total": len(created_ids),
            "status": "queued",
        },
    }


@router.post("/edit/{record_id}", response_model=dict)
async def edit_generate_params(
    record_id: int,
    body: GenerateRecordEdit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """编辑生成参数"""
    result = await db.execute(
        select(GenerateRecord).where(
            GenerateRecord.id == record_id,
            GenerateRecord.user_id == current_user.id
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="生成记录不存在")

    if record.status not in [GenerateStatus.PENDING, GenerateStatus.EDITING]:
        raise HTTPException(status_code=400, detail="任务已开始处理，无法编辑")

    if body.edited_script is not None:
        record.edited_script = body.edited_script
    if body.edited_scenes is not None:
        record.edited_scenes = json.dumps([s.model_dump() for s in body.edited_scenes], ensure_ascii=False)
    if body.voice_tone is not None:
        record.voice_tone = json.dumps(body.voice_tone.model_dump(), ensure_ascii=False)
    if body.replace_materials is not None:
        record.replace_materials = json.dumps([m.model_dump() for m in body.replace_materials], ensure_ascii=False)
    if body.aspect_ratio is not None:
        record.aspect_ratio = body.aspect_ratio
    if body.generation_params is not None:
        record.generation_params = json.dumps(body.generation_params.model_dump(), ensure_ascii=False)

    record.status = GenerateStatus.EDITING
    await db.commit()

    return {
        "code": 200,
        "message": "参数编辑成功",
        "data": {"record_id": record_id},
    }


@router.get("/list", response_model=dict)
async def list_generates(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的生成记录列表"""
    offset = (page - 1) * size
    total = (await db.execute(
        select(func.count()).select_from(GenerateRecord).where(GenerateRecord.user_id == current_user.id)
    )).scalar() or 0

    result = await db.execute(
        select(GenerateRecord)
        .where(GenerateRecord.user_id == current_user.id)
        .order_by(GenerateRecord.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    records = result.scalars().all()

    return {
        "code": 200, "message": "success",
        "data": [GenerateRecordOut.model_validate(r) for r in records],
        "total": total, "page": page, "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/{record_id}", response_model=dict)
async def get_generate(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个生成记录详情"""
    result = await db.execute(
        select(GenerateRecord).where(
            GenerateRecord.id == record_id,
            GenerateRecord.user_id == current_user.id
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="生成记录不存在")
    return {"code": 200, "message": "success", "data": GenerateRecordOut.model_validate(record)}


@router.get("/parse/{parse_id}", response_model=dict)
async def get_parse_detail(
    parse_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取解析记录详情，用于复刻编辑"""
    result = await db.execute(
        select(ParseRecord).where(
            ParseRecord.id == parse_id,
            ParseRecord.user_id == current_user.id
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="解析记录不存在")

    parse_data = json.loads(record.result_json or "{}")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "parse_record": {
                "id": record.id,
                "video_url": record.video_url,
                "status": record.status.value if hasattr(record.status, 'value') else record.status,
                "duration": record.duration,
            },
            "analysis_result": parse_data,
        },
    }