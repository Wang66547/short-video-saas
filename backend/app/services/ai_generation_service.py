"""
AI视频生成服务
- 对接即梦(Jimeng)和可灵(Kling)开放平台API
- 自动把分镜脚本转为生成参数
- 批量提交多镜头生成任务
- 轮询生成结果
- 成品自动裁剪去除水印/AI标识
"""
import os
import json
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.core.config import get_settings

settings = get_settings()


class AIGenerationService:
    """AI视频生成服务基类"""
    
    def __init__(self, platform: str = "jimeng"):
        self.platform = platform
        self.api_key = settings.JIMENG_API_KEY if platform == "jimeng" else settings.KLING_API_KEY
        self.base_url = settings.JIMENG_BASE_URL if platform == "jimeng" else settings.KLING_BASE_URL
    
    async def create_generation_task(self, params: Dict[str, Any]) -> str:
        """
        创建AI生成任务
        :param params: 生成参数
        :return: 任务ID
        """
        raise NotImplementedError("子类必须实现此方法")
    
    async def poll_task_status(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        轮询任务状态
        :param task_id: 任务ID
        :param timeout: 超时时间(秒)
        :return: 任务结果
        """
        raise NotImplementedError("子类必须实现此方法")
    
    async def crop_watermark(self, video_path: str, output_path: str, watermark_info: Dict[str, Any]) -> bool:
        """
        裁剪去除平台水印和AI标识
        :param video_path: 输入视频路径
        :param output_path: 输出视频路径
        :param watermark_info: 水印信息
        :return: True=成功, False=失败
        """
        try:
            from app.services.ffmpeg_service import run_ffmpeg
            
            # 构建FFmpeg命令去除水印
            filters = []
            
            # 去除指定位置的水印
            if watermark_info.get("delogo_filter"):
                filters.append(watermark_info["delogo_filter"])
            
            # 裁剪边缘水印
            if watermark_info.get("x", 0) > 0:
                w = watermark_info.get("width", 150)
                h = watermark_info.get("height", 50)
                x = watermark_info.get("x", 0)
                y = watermark_info.get("y", 0)
                filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}:display=0")
            
            # 构建FFmpeg命令
            cmd = [
                "-i", video_path,
                "-c:v", "libx264",
                "-c:a", "aac",
            ]
            
            if filters:
                cmd.extend(["-filter_complex", ";".join(filters)])
            
            cmd.extend(["-movflags", "+faststart", output_path])
            
            _, _, rc = await run_ffmpeg(cmd)
            return rc == 0 and os.path.exists(output_path)
            
        except Exception as e:
            print(f"水印裁剪失败: {e}")
            return False


class JimengService(AIGenerationService):
    """即梦(Jimeng)API服务"""
    
    def __init__(self):
        super().__init__(platform="jimeng")
    
    async def create_generation_task(self, params: Dict[str, Any]) -> str:
        """
        创建即梦生成任务
        :param params: 包含prompt、aspect_ratio、scene_scripts等参数
        :return: 任务ID
        """
        try:
            # 构建即梦API请求参数
            request_params = {
                "model": "jimeng-video-v1",
                "prompt": params.get("prompt", ""),
                "negative_prompt": params.get("negative_prompt", ""),
                "aspect_ratio": params.get("aspect_ratio", "9:16"),
                "duration": params.get("duration", 5),
                "seed": params.get("seed", -1),
                "guidance_scale": params.get("guidance_scale", 7.5),
                "num_inference_steps": params.get("steps", 25),
            }
            
            # 添加分镜脚本
            if params.get("scene_scripts"):
                request_params["scene_scripts"] = params["scene_scripts"]
            
            # 添加参考图片
            if params.get("reference_images"):
                request_params["reference_images"] = params["reference_images"]
            
            # 调用即梦API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/v1/videos/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_params,
                )
                
                if response.status_code != 200:
                    raise Exception(f"即梦API请求失败: {response.text}")
                
                result = response.json()
                return result.get("task_id", "")
                
        except Exception as e:
            print(f"即梦创建任务失败: {e}")
            raise
    
    async def poll_task_status(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        轮询即梦任务状态
        :param task_id: 任务ID
        :param timeout: 超时时间(秒)
        :return: 任务结果
        """
        try:
            start_time = datetime.now(timezone(timedelta(hours=8)))
            
            while True:
                # 检查是否超时
                if (datetime.now(timezone(timedelta(hours=8))) - start_time).seconds > timeout:
                    raise Exception("即梦任务轮询超时")
                
                # 查询任务状态
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        f"{self.base_url}/v1/videos/tasks/{task_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                        },
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"即梦状态查询失败: {response.text}")
                    
                    result = response.json()
                    status = result.get("status", "")
                    
                    if status == "SUCCESS":
                        # 任务完成，返回结果
                        return {
                            "status": "success",
                            "video_url": result.get("video_url", ""),
                            "thumbnail_url": result.get("thumbnail_url", ""),
                            "task_id": task_id,
                        }
                    elif status == "FAILED":
                        raise Exception(f"即梦任务失败: {result.get('error_message', '未知错误')}")
                    elif status in ["PENDING", "PROCESSING"]:
                        # 任务进行中，等待一段时间后继续轮询
                        await asyncio.sleep(5)
                    else:
                        # 未知状态，继续等待
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"即梦轮询任务失败: {e}")
            raise


class KlingService(AIGenerationService):
    """可灵(Kling)API服务"""
    
    def __init__(self):
        super().__init__(platform="kling")
    
    async def create_generation_task(self, params: Dict[str, Any]) -> str:
        """
        创建可灵生成任务
        :param params: 包含prompt、aspect_ratio、scene_scripts等参数
        :return: 任务ID
        """
        try:
            # 构建可灵API请求参数
            request_params = {
                "model": "kling-v1",
                "prompt": params.get("prompt", ""),
                "negative_prompt": params.get("negative_prompt", ""),
                "aspect_ratio": params.get("aspect_ratio", "9:16"),
                "duration": params.get("duration", 5),
                "seed": params.get("seed", -1),
            }
            
            # 添加分镜脚本
            if params.get("scene_scripts"):
                request_params["scene_scripts"] = params["scene_scripts"]
            
            # 添加参考图片
            if params.get("reference_images"):
                request_params["reference_images"] = params["reference_images"]
            
            # 调用可灵API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/v1/images/videos",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_params,
                )
                
                if response.status_code != 200:
                    raise Exception(f"可灵API请求失败: {response.text}")
                
                result = response.json()
                return result.get("task_id", "")
                
        except Exception as e:
            print(f"可灵创建任务失败: {e}")
            raise
    
    async def poll_task_status(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        轮询可灵任务状态
        :param task_id: 任务ID
        :param timeout: 超时时间(秒)
        :return: 任务结果
        """
        try:
            start_time = datetime.now(timezone(timedelta(hours=8)))
            
            while True:
                # 检查是否超时
                if (datetime.now(timezone(timedelta(hours=8))) - start_time).seconds > timeout:
                    raise Exception("可灵任务轮询超时")
                
                # 查询任务状态
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        f"{self.base_url}/v1/images/videos/{task_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                        },
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"可灵状态查询失败: {response.text}")
                    
                    result = response.json()
                    status = result.get("status", "")
                    
                    if status == "SUCCESS":
                        # 任务完成，返回结果
                        return {
                            "status": "success",
                            "video_url": result.get("video_url", ""),
                            "thumbnail_url": result.get("thumbnail_url", ""),
                            "task_id": task_id,
                        }
                    elif status == "FAILED":
                        raise Exception(f"可灵任务失败: {result.get('error_message', '未知错误')}")
                    elif status in ["PENDING", "PROCESSING"]:
                        # 任务进行中，等待一段时间后继续轮询
                        await asyncio.sleep(5)
                    else:
                        # 未知状态，继续等待
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"可灵轮询任务失败: {e}")
            raise


async def convert_scene_scripts_to_generation_params(
    scene_scripts: List[Dict[str, Any]],
    aspect_ratio: str = "9:16",
    ai_platform: str = "jimeng"
) -> Dict[str, Any]:
    """
    把分镜脚本转为AI生成参数
    :param scene_scripts: 分镜脚本列表
    :param aspect_ratio: 画面比例
    :param ai_platform: AI平台
    :return: 生成参数字典
    """
    # 构建提示词
    prompts = []
    for i, scene in enumerate(scene_scripts):
        prompt = scene.get("script", "")
        if prompt:
            prompts.append(f"镜头{i+1}: {prompt}")
    
    combined_prompt = "\n".join(prompts) if prompts else "视频生成提示词"
    
    # 构建生成参数
    generation_params = {
        "prompt": combined_prompt,
        "negative_prompt": "水印，字幕，AI标识，低质量，模糊，扭曲",
        "aspect_ratio": aspect_ratio,
        "duration": 5,  # 每个镜头5秒
        "scene_scripts": scene_scripts,
    }
    
    return generation_params


async def generate_video_with_ai(
    parse_record_id: int,
    edited_script: str,
    edited_scenes: List[Dict[str, Any]],
    voice_tone: str,
    aspect_ratio: str = "9:16",
    ai_platform: str = "jimeng",
) -> Dict[str, Any]:
    """
    AI视频生成主流程
    :param parse_record_id: 解析记录ID
    :param edited_script: 编辑后的文案
    :param edited_scenes: 编辑后的分镜
    :param voice_tone: 配音音色
    :param aspect_ratio: 画面比例
    :param ai_platform: AI平台
    :return: 生成结果
    """
    try:
        # 1. 转换分镜脚本为生成参数
        generation_params = await convert_scene_scripts_to_generation_params(
            edited_scenes,
            aspect_ratio,
            ai_platform
        )
        
        # 2. 选择AI服务平台
        if ai_platform == "jimeng":
            service = JimengService()
        elif ai_platform == "kling":
            service = KlingService()
        else:
            raise ValueError(f"不支持的AI平台: {ai_platform}")
        
        # 3. 创建生成任务
        task_id = await service.create_generation_task(generation_params)
        
        # 4. 轮询任务状态
        result = await service.poll_task_status(task_id, timeout=600)  # 10分钟超时
        
        # 5. 下载成品视频
        output_path = os.path.join(settings.VIDEO_STORAGE_PATH, f"output_{parse_record_id}.mp4")
        await download_video(result["video_url"], output_path)
        
        # 6. 裁剪去除水印和AI标识
        # TODO: 获取水印信息并裁剪
        
        return {
            "status": "success",
            "output_path": output_path,
            "task_id": task_id,
            "result": result,
        }
        
    except Exception as e:
        print(f"AI视频生成失败: {e}")
        raise


async def download_video(url: str, output_path: str) -> bool:
    """
    下载视频文件
    :param url: 视频URL
    :param output_path: 本地保存路径
    :return: True=成功, False=失败
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("GET", url) as response:
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                    return True
        
        return False
        
    except Exception as e:
        print(f"视频下载失败: {e}")
        return False
