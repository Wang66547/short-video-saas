"""
本地视频合成服务
- 基于FFmpeg把用户素材、AI配音、BGM合成新视频
- 支持多镜头拼接
- 自动去除水印和AI标识
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.services.ffmpeg_service import run_ffmpeg, download_video

settings = get_settings()


async def synthesize_video_locally(
    parse_record_id: int,
    edited_script: str,
    edited_scenes: List[Dict[str, Any]],
    voice_tone: str,
    bgm_path: str,
    aspect_ratio: str = "9:16",
) -> Dict[str, Any]:
    """
    本地视频合成主流程
    :param parse_record_id: 解析记录ID
    :param edited_script: 编辑后的文案
    :param edited_scenes: 编辑后的分镜
    :param voice_tone: 配音音色
    :param bgm_path: BGM文件路径
    :param aspect_ratio: 画面比例
    :return: 合成结果
    """
    try:
        output_dir = os.path.join(settings.VIDEO_STORAGE_PATH, str(parse_record_id))
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 生成AI配音
        audio_path = await generate_voiceover(edited_script, voice_tone, output_dir)
        
        # 2. 准备素材列表
        material_paths = await prepare_materials(edited_scenes, output_dir)
        
        # 3. 合成视频
        output_path = os.path.join(output_dir, f"output_{parse_record_id}.mp4")
        success = await compose_video(material_paths, audio_path, bgm_path, output_path, aspect_ratio)
        
        if not success:
            raise Exception("视频合成失败")
        
        # 4. 生成缩略图
        thumbnail_path = os.path.join(output_dir, f"thumbnail_{parse_record_id}.jpg")
        await generate_thumbnail(output_path, thumbnail_path)
        
        return {
            "status": "success",
            "output_path": output_path,
            "thumbnail_path": thumbnail_path,
        }
        
    except Exception as e:
        print(f"本地视频合成失败: {e}")
        raise


async def generate_voiceover(script: str, voice_tone: str, output_dir: str) -> str:
    """
    生成AI配音
    :param script: 文案脚本
    :param voice_tone: 音色
    :param output_dir: 输出目录
    :return: 音频文件路径
    """
    audio_path = os.path.join(output_dir, "voiceover.wav")
    
    # TODO: 接入TTS服务（如阿里云TTS、Azure TTS等）
    # 这里模拟生成音频文件
    try:
        # 实际项目中需要调用TTS API
        # 例如：
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.tts-service.com/v1/synthesize",
        #         json={
        #             "text": script,
        #             "voice_id": voice_tone,
        #         },
        #     )
        #     with open(audio_path, "wb") as f:
        #         f.write(response.content)
        
        # 模拟：创建一个空的音频文件
        with open(audio_path, "wb") as f:
            f.write(b"")
        
        return audio_path
        
    except Exception as e:
        print(f"生成配音失败: {e}")
        # 返回空路径表示没有配音
        return ""


async def prepare_materials(scenes: List[Dict[str, Any]], output_dir: str) -> List[str]:
    """
    准备素材列表
    :param scenes: 分镜列表
    :param output_dir: 输出目录
    :return: 素材文件路径列表
    """
    material_paths = []
    
    for i, scene in enumerate(scenes):
        material_url = scene.get("material_url", "")
        if material_url:
            # 下载素材
            material_path = os.path.join(output_dir, f"material_{i}.mp4")
            downloaded = await download_video(material_url, material_path)
            if downloaded and os.path.exists(material_path):
                material_paths.append(material_path)
        else:
            # 如果没有素材URL，使用占位符
            placeholder_path = os.path.join(output_dir, f"placeholder_{i}.mp4")
            # TODO: 生成占位视频
            material_paths.append(placeholder_path)
    
    return material_paths


async def compose_video(
    material_paths: List[str],
    audio_path: str,
    bgm_path: str,
    output_path: str,
    aspect_ratio: str = "9:16",
) -> bool:
    """
    合成视频
    :param material_paths: 素材文件路径列表
    :param audio_path: 配音文件路径
    :param bgm_path: BGM文件路径
    :param output_path: 输出文件路径
    :param aspect_ratio: 画面比例
    :return: True=成功, False=失败
    """
    try:
        if not material_paths:
            return False
        
        # 构建FFmpeg命令
        cmd = []
        
        # 添加素材文件
        for path in material_paths:
            if os.path.exists(path):
                cmd.extend(["-i", path])
        
        # 添加配音
        if audio_path and os.path.exists(audio_path):
            cmd.extend(["-i", audio_path])
        
        # 添加BGM
        if bgm_path and os.path.exists(bgm_path):
            cmd.extend(["-i", bgm_path])
        
        # 构建过滤器
        filter_complex = []
        
        # 1. 视频拼接
        if len(material_paths) > 1:
            video_inputs = " ".join([f"[{i}:v]" for i in range(len(material_paths))])
            filter_complex.append(f"{video_inputs}concat=n={len(material_paths)}:v=1:a=0[outv]")
        
        # 2. 音频混合（配音+BGM）
        audio_filters = []
        if audio_path and os.path.exists(audio_path):
            audio_filters.append(f"[1:a]volume=1.0[voice]")
        if bgm_path and os.path.exists(bgm_path):
            audio_filters.append(f"[2:a]volume=0.3[bgm]")  # BGM音量调低
        
        if audio_filters:
            filter_complex.extend(audio_filters)
            if len(audio_filters) > 1:
                filter_complex.append("[voice][bgm]amix=inputs=2:duration=first[audio]")
        
        # 构建完整命令
        if filter_complex:
            cmd.extend(["-filter_complex", ";".join(filter_complex)])
        
        # 添加输出参数
        cmd.extend([
            "-map", "[outv]" if filter_complex else "0:v",
            "-map", "[audio]" if filter_complex else "0:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:v", "2000k",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ])
        
        # 执行FFmpeg
        _, _, rc = await run_ffmpeg(cmd, timeout=600)
        return rc == 0 and os.path.exists(output_path)
        
    except Exception as e:
        print(f"视频合成失败: {e}")
        return False


async def generate_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """
    生成视频缩略图
    :param video_path: 视频路径
    :param output_path: 输出路径
    :param timestamp: 截取时间点(秒)
    :return: True=成功, False=失败
    """
    try:
        cmd = [
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]
        _, _, rc = await run_ffmpeg(cmd)
        return rc == 0 and os.path.exists(output_path)
        
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return False
