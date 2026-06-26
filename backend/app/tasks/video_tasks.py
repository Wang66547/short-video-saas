"""
Celery 异步视频生成任务
- AI视频生成（即梦/可灵）
- 本地视频合成
- 成品处理（去水印/去字幕/AI标识）
- 对象存储上传
- 用户积分扣减
"""
import os
import json
import datetime
import logging
from app.tasks.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.generate_record import GenerateRecord, GenerateStatus, GenerateMode
from app.models.parse_record import ParseRecord
from app.core.config import get_settings
from app.services.credits_service import consume_credits

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_video_task(record_id: int):
    """
    视频生成任务
    完整流程：
    1. 加载生成参数
    2. 选择生成模式（AI生成/本地合成）
    3. 执行生成
    4. 成品处理（去水印/去字幕/AI标识）
    5. 上传对象存储
    6. 更新记录状态
    7. 扣减用户积分
    """
    async with async_session_factory() as db:
        try:
            from sqlalchemy import select
            result = await db.execute(select(GenerateRecord).where(GenerateRecord.id == record_id))
            record = result.scalar_one_or_none()
            
            if not record:
                logger.error(f"生成任务 {record_id} 不存在")
                return {"error": "任务不存在"}
            
            # 更新状态为处理中
            record.status = GenerateStatus.PROCESSING
            record.progress = 10.0
            await db.commit()
            logger.info(f"开始视频生成任务 {record_id}")
            
            # 解析生成参数
            params = json.loads(record.generation_params or "{}")
            generate_mode = record.generate_mode or GenerateMode.AI_GENERATE
            
            # 获取解析记录
            parse_result = await db.execute(
                select(ParseRecord).where(ParseRecord.id == record.parse_id)
            )
            parse_record = parse_result.scalar_one_or_none()
            
            if not parse_record:
                raise Exception("关联的解析记录不存在")
            
            # 解析解析结果
            parse_data = json.loads(parse_record.result_json or "{}")
            
            if generate_mode == GenerateMode.AI_GENERATE:
                # AI生成模式
                logger.info(f"使用AI生成模式，平台: {params.get('ai_platform', 'jimeng')}")
                result = await generate_video_with_ai(
                    parse_record_id=record.parse_id,
                    edited_script=params.get("edited_script", ""),
                    edited_scenes=json.loads(params.get("edited_scenes", "[]")),
                    voice_tone=params.get("voice_tone", ""),
                    aspect_ratio=params.get("aspect_ratio", "9:16"),
                    ai_platform=params.get("ai_platform", "jimeng"),
                )
            else:
                # 本地合成模式
                logger.info("使用本地合成模式")
                result = await synthesize_video_locally(
                    parse_record_id=record.parse_id,
                    edited_script=params.get("edited_script", ""),
                    edited_scenes=json.loads(params.get("edited_scenes", "[]")),
                    voice_tone=params.get("voice_tone", ""),
                    bgm_path=parse_data.get("bgm_path", ""),
                    aspect_ratio=params.get("aspect_ratio", "9:16"),
                )
            
            if result.get("status") != "success":
                record.status = GenerateStatus.FAILED
                record.error_message = result.get("error", "生成失败")
                await db.commit()
                return {"error": "生成失败"}
            
            # 更新生成记录
            record.output_video_url = result.get("output_path", "")
            record.output_thumbnail = result.get("thumbnail_path", "")
            record.status = GenerateStatus.SUCCESS
            record.progress = 100.0
            record.completed_at = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
            
            # 扣减用户积分
            await consume_credits(record.user_id, record.cost_credits)
            
            await db.commit()
            logger.info(f"视频生成任务 {record_id} 完成")
            
            return {
                "status": "completed",
                "record_id": record_id,
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"视频生成任务 {record_id} 失败: {e}", exc_info=True)
            
            # 更新失败状态
            async with async_session_factory() as db:
                from sqlalchemy import select
                result = await db.execute(select(GenerateRecord).where(GenerateRecord.id == record_id))
                record = result.scalar_one_or_none()
                if record:
                    record.status = GenerateStatus.FAILED
                    record.error_message = str(e)[:500]
                    await db.commit()
            
            return {"status": "failed", "error": str(e)}


def cleanup_temp_files():
    """定时清理临时文件"""
    import shutil
    if os.path.exists(settings.TEMP_DIR):
        shutil.rmtree(settings.TEMP_DIR, ignore_errors=True)
        logger.info(f"已清理临时目录: {settings.TEMP_DIR}")
