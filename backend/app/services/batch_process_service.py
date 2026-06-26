"""
批量处理服务
- 批量上传视频解析
- 批量提交生成任务
- 自动排队调度
- 进度追踪
- 任务状态持久化到 Redis（生产环境）
"""
import os
import uuid
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.core.redis_client import get_batch_task, set_batch_task, add_user_batch_task
from app.services.watermark_removal_service import WatermarkRemovalService

settings = get_settings()


class BatchProcessService:
    """批量处理服务（支持 Redis 持久化）"""

    def __init__(self):
        # 内存缓存（仅在 Redis 不可用时降级使用）
        self._memory_queues: Dict[str, List[Dict]] = {}
        self._memory_status: Dict[str, Dict] = {}

    async def _save_status(self, task_id: str, status_data: Dict) -> None:
        """保存任务状态到 Redis，失败时降级到内存"""
        if not await set_batch_task(task_id, status_data):
            # Redis 不可用，降级到内存
            self._memory_status[task_id] = status_data

    async def _get_status(self, task_id: str) -> Optional[Dict]:
        """从 Redis 获取任务状态，不存在则从内存获取"""
        status = await get_batch_task(task_id)
        if status is not None:
            return status
        return self._memory_status.get(task_id)

    async def create_batch_parse_task(
        self,
        user_id: int,
        video_urls: List[str],
        platform: str = "auto",
    ) -> str:
        """
        创建批量解析任务
        :param user_id: 用户ID
        :param video_urls: 视频URL列表
        :param platform: 平台标识
        :return: 任务ID
        """
        task_id = f"batch_parse_{uuid.uuid4().hex[:8]}"

        # 创建任务状态
        status_data = {
            "task_id": task_id,
            "type": "batch_parse",
            "user_id": user_id,
            "total": len(video_urls),
            "completed": 0,
            "failed": 0,
            "status": "queued",
            "created_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "items": [
                {
                    "index": i,
                    "url": url,
                    "status": "pending",
                    "result": None,
                }
                for i, url in enumerate(video_urls)
            ],
        }

        # 持久化到 Redis
        await self._save_status(task_id, status_data)
        await add_user_batch_task(user_id, task_id)

        # 内存队列也保留一份（降级用）
        self._memory_queues.setdefault(user_id, []).append(task_id)

        return task_id

    async def create_batch_generate_task(
        self,
        user_id: int,
        parse_ids: List[int],
        generate_params: Dict[str, Any],
    ) -> str:
        """
        创建批量生成任务
        :param user_id: 用户ID
        :param parse_ids: 解析记录ID列表
        :param generate_params: 生成参数
        :return: 任务ID
        """
        task_id = f"batch_gen_{uuid.uuid4().hex[:8]}"

        status_data = {
            "task_id": task_id,
            "type": "batch_generate",
            "user_id": user_id,
            "total": len(parse_ids),
            "completed": 0,
            "failed": 0,
            "status": "queued",
            "created_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "params": generate_params,
            "items": [
                {
                    "index": i,
                    "parse_id": pid,
                    "status": "pending",
                    "result": None,
                }
                for i, pid in enumerate(parse_ids)
            ],
        }

        # 持久化到 Redis
        await self._save_status(task_id, status_data)
        await add_user_batch_task(user_id, task_id)

        # 内存队列也保留一份（降级用）
        self._memory_queues.setdefault(user_id, []).append(task_id)
        return task_id

    async def get_batch_status(self, task_id: str) -> Optional[Dict]:
        """获取批量任务状态"""
        return await self._get_status(task_id)

    async def process_batch_parse_item(
        self,
        task_id: str,
        item_index: int,
        result: Dict,
        success: bool = True,
    ):
        """
        处理单个批量解析项的结果
        :param task_id: 任务ID
        :param item_index: 项索引
        :param result: 解析结果
        :param success: 是否成功
        """
        task = await self._get_status(task_id)
        if task is None:
            task = self._memory_status.get(task_id)
        if task is None:
            return

        item = task["items"][item_index]
        item["status"] = "completed" if success else "failed"
        item["result"] = result

        if success:
            task["completed"] += 1
        else:
            task["failed"] += 1

        # 检查是否全部完成
        if task["completed"] + task["failed"] >= task["total"]:
            task["status"] = "completed"

        # 持久化更新后的状态
        await self._save_status(task_id, task)
        # 内存也同步更新
        self._memory_status[task_id] = task

    async def remove_watermark_batch(
        self,
        video_paths: List[str],
        output_dir: str,
        platform: str = "auto",
    ) -> List[Dict]:
        """
        批量去水印
        :param video_paths: 视频路径列表
        :param output_dir: 输出目录
        :param platform: 平台
        :return: 处理结果
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, path in enumerate(video_paths):
            output_path = os.path.join(output_dir, f"cleaned_{i}.mp4")
            result = await WatermarkRemovalService.remove_watermark_from_video(
                input_path=path,
                output_path=output_path,
                platform=platform,
            )
            results.append({"index": i, "input": path, **result})

        return results


# 全局单例
batch_service = BatchProcessService()