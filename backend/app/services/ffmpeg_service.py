"""
FFmpeg 视频处理服务
- 视频下载与去水印
- 视频剪辑与拼接
- 字幕合成
- 转码与压缩
- 截图生成
"""
import asyncio
import os
import aiohttp
import re
from app.core.config import get_settings

settings = get_settings()


async def run_ffmpeg(args: list, timeout: int = 300) -> tuple:
    """
    通用 FFmpeg 命令执行
    :param args: FFmpeg 参数列表
    :param timeout: 超时时间(秒)
    :return: (stdout, stderr, returncode)
    """
    cmd = [settings.FFMPEG_BIN, "-y"] + args
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode(), proc.returncode


async def download_video(url: str, output_path: str) -> bool:
    """
    从URL下载视频文件
    :param url: 视频下载地址
    :param output_path: 本地保存路径
    :return: True=成功, False=失败
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 尝试使用 ffmpeg 下载
        stdout, stderr, rc = await run_ffmpeg([
            "-headers", "User-Agent: Mozilla/5.0",
            "-i", url,
            "-c", "copy",
            "-f", "mp4",
            output_path,
        ])
        
        if rc == 0 and os.path.exists(output_path):
            return True
        
        # 如果 ffmpeg 下载失败，尝试使用 aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                if resp.status == 200:
                    with open(output_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                    return True
        
        return False
        
    except Exception as e:
        print(f"视频下载失败: {e}")
        return False


async def get_video_info(video_path: str) -> dict:
    """
    使用 ffprobe 获取视频详细信息
    """
    try:
        cmd = [
            settings.FFPROBE_BIN,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            video_path,
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        
        import json
        info = json.loads(stdout.decode())
        
        # 提取视频流信息
        video_stream = None
        audio_stream = None
        
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
            elif stream.get("codec_type") == "audio":
                audio_stream = stream
        
        # 计算时长
        duration = float(info.get("format", {}).get("duration", 0))
        if not duration and video_stream:
            duration = float(video_stream.get("duration", 0))
        
        # 计算帧率
        fps = 0
        if video_stream:
            fps_str = video_stream.get("r_frame_rate", "0/1")
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                fps = num / den if den else 0
            else:
                fps = float(fps_str)
        
        # 计算码率
        bitrate = int(info.get("format", {}).get("bit_rate", 0))
        if not bitrate and video_stream:
            bitrate = int(video_stream.get("bit_rate", 0))
        
        # 分辨率
        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0
        
        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "bitrate": bitrate,
            "format": info.get("format", {}).get("format_long_name", ""),
            "video_codec": video_stream.get("codec_name", "") if video_stream else "",
            "audio_codec": audio_stream.get("codec_name", "") if audio_stream else "",
        }
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return {"duration": 0, "width": 0, "height": 0, "fps": 0, "bitrate": 0}


async def clip_video(input_path: str, output_path: str, start: float, duration: float):
    """
    截取视频片段
    :param input_path: 输入视频
    :param output_path: 输出视频
    :param start: 起始时间(秒)
    :param duration: 截取时长(秒)
    """
    await run_ffmpeg([
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",
        output_path,
    ])


async def add_watermark(input_path: str, watermark_path: str, output_path: str):
    """
    添加水印
    """
    await run_ffmpeg([
        "-i", input_path,
        "-i", watermark_path,
        "-filter_complex", "[0:v][1:v]overlay=W-w-10:10",
        "-c:a", "copy",
        output_path,
    ])


async def compress_video(input_path: str, output_path: str, quality: str = "medium"):
    """
    压缩视频
    :param quality: 质量 preset: ultrafast/fast/medium/slow/veryslow
    """
    crf_map = {"fast": "28", "medium": "23", "slow": "20", "veryslow": "18"}
    crf = crf_map.get(quality, "23")
    
    await run_ffmpeg([
        "-i", input_path,
        "-c:v", "libx264",
        "-crf", crf,
        "-preset", quality,
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ])


async def extract_audio(input_path: str, output_path: str):
    """
    提取视频音频
    """
    await run_ffmpeg([
        "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        output_path,
    ])


async def concat_videos(input_paths: list, output_path: str):
    """
    拼接多个视频
    使用 concat demuxer
    """
    # 生成 concat 文件列表
    list_file = os.path.splitext(output_path)[0] + "_list.txt"
    with open(list_file, "w") as f:
        for p in input_paths:
            f.write(f"file '{p}'\n")
    
    await run_ffmpeg([
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path,
    ])
    os.remove(list_file)
