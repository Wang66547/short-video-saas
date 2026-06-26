"""
PaddleOCR 字幕识别服务
- 视频帧字幕提取
- 文字区域定位
- OCR 结果后处理
"""
import os
import asyncio
from app.core.config import get_settings

settings = get_settings()


async def recognize_text_from_video(video_path: str) -> list:
    """
    从视频中识别字幕文字
    1. 抽帧（每秒1帧）
    2. PaddleOCR 识别
    3. 去重与合并
    """
    try:
        # 先抽帧
        frames_dir = os.path.join(settings.TEMP_DIR, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        # 使用 ffmpeg 抽帧
        import subprocess
        cmd = [
            settings.FFMPEG_BIN,
            "-i", video_path,
            "-vf", "fps=1",
            os.path.join(frames_dir, "frame_%04d.jpg"),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        
        # TODO: 接入 PaddleOCR
        # from paddleocr import PaddleOCR
        # ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        # results = ocr.ocr(frames_dir, cls=True)
        
        # 模拟OCR结果
        return [
            {
                "text": "示例字幕1",
                "timestamp": 1.0,
                "confidence": 0.9,
                "bbox": [100, 200, 300, 250],
            },
            {
                "text": "示例字幕2",
                "timestamp": 5.0,
                "confidence": 0.85,
                "bbox": [100, 200, 300, 250],
            },
        ]
        
    except Exception as e:
        print(f"OCR识别失败: {e}")
        return []


async def recognize_text_from_image(image_path: str) -> list:
    """
    从单张图片中识别文字
    """
    # TODO: 接入 PaddleOCR
    return []
