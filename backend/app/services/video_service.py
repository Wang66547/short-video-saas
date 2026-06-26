"""
视频处理业务逻辑层
- 视频下载
- 视频分析
- 结果管理
"""
import asyncio
import aiohttp
import os
from pathlib import Path
from app.config import get_settings

settings = get_settings()


async def download_video(url: str, save_path: str) -> bool:
    """
    从URL下载视频文件
    :param url: 视频下载地址
    :param save_path: 本地保存路径
    :return: True=成功, False=失败
    """
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                if resp.status != 200:
                    return False
                
                # 流式写入，避免大文件内存溢出
                with open(save_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)
        
        return True
    except Exception as e:
        print(f"视频下载失败: {e}")
        return False


async def get_video_duration(video_path: str) -> float:
    """
    获取视频时长（秒）
    使用 ffprobe 命令
    """
    import subprocess
    try:
        cmd = [
            settings.FFMPEG_BIN,
            "-i", video_path,
            "-hide_banner",
            "-loglevel", "error",
        ]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stderr = (await result.communicate())[1].decode()
        
        # 从 ffprobe 输出中提取时长
        import re
        match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
        
        return 0
    except Exception:
        return 0


async def generate_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """
    截取视频缩略图
    :param video_path: 视频路径
    :param output_path: 输出图片路径
    :param timestamp: 截取时间点(秒)
    """
    import subprocess
    try:
        cmd = [
            settings.FFMPEG_BIN,
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]
        await asyncio.create_subprocess_exec(*cmd)
        return os.path.exists(output_path)
    except Exception:
        return False
