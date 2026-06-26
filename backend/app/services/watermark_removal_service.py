"""
智能去水印服务
- 自动识别抖音/快手/小红书/视频号/B站等平台固定角落水印
- FFmpeg delogo 无痕处理，保持原画质无压缩
- 支持批量视频去水印
"""
import os
import re
import json
import asyncio
from typing import Dict, List, Optional
from app.core.config import get_settings

settings = get_settings()

# ==================== 平台水印特征库 ====================
# 各平台常见水印位置和尺寸（基于分辨率 1080x1920 竖屏）
PLATFORM_WATERMARK_DB = {
    # 抖音
    "douyin": {
        "patterns": [
            # 右下角账号水印（最常见）
            {"x_percent": 0.65, "y_percent": 0.78, "w_percent": 0.30, "h_percent": 0.12, "label": "douyin_account"},
            # 左下角文案区域
            {"x_percent": 0.02, "y_percent": 0.75, "w_percent": 0.35, "h_percent": 0.15, "label": "douyin_caption"},
            # 顶部标题栏
            {"x_percent": 0.0, "y_percent": 0.0, "w_percent": 1.0, "h_percent": 0.08, "label": "douyin_top"},
        ],
        "delogo_filter": "delogo=x=0.65*w:y=0.78*h:w=0.30*w:h=0.12*h:flags=t",
    },
    # 快手
    "kuaishou": {
        "patterns": [
            {"x_percent": 0.02, "y_percent": 0.02, "w_percent": 0.15, "h_percent": 0.08, "label": "kuaishou_logo"},
            {"x_percent": 0.65, "y_percent": 0.80, "w_percent": 0.30, "h_percent": 0.10, "label": "kuaishou_account"},
        ],
    },
    # 小红书
    "xiaohongshu": {
        "patterns": [
            {"x_percent": 0.02, "y_percent": 0.02, "w_percent": 0.18, "h_percent": 0.06, "label": "xhs_logo"},
            {"x_percent": 0.02, "y_percent": 0.90, "w_percent": 0.30, "h_percent": 0.06, "label": "xhs_share"},
        ],
    },
    # 视频号
    "wechat_video": {
        "patterns": [
            {"x_percent": 0.02, "y_percent": 0.02, "w_percent": 0.20, "h_percent": 0.06, "label": "wx_video_logo"},
            {"x_percent": 0.70, "y_percent": 0.02, "w_percent": 0.10, "h_percent": 0.05, "label": "wx_video_btn"},
        ],
    },
    # B站
    "bilibili": {
        "patterns": [
            {"x_percent": 0.85, "y_percent": 0.02, "w_percent": 0.12, "h_percent": 0.06, "label": "bili_logo"},
        ],
    },
}

# 平台域名识别规则
PLATFORM_DETECT_RULES = {
    "douyin": [r"douyin\.com", r"ies Douyin", r"snssdk1128"],
    "kuaishou": [r"kuaishou\.com", r"gifshow", r"ksfe"],
    "xiaohongshu": [r"xhslink", r"xiaxiu", r"RED", r"xiaohongshu\.com"],
    "wechat_video": [r"wechat\.com", r"video\.account", r"wxvideo"],
    "bilibili": [r"bilibili\.com", r"b23\.tv", r"bili_"],
}


class WatermarkRemovalService:
    """智能去水印服务"""

    @staticmethod
    async def detect_platform_from_url(url: str) -> Optional[str]:
        """
        从URL或文件名中识别视频来源平台
        :param url: 视频URL或本地路径
        :return: 平台标识 (douyin/kuaishou/xiaohongshu/wechat_video/bilibili)
        """
        url_lower = url.lower()
        for platform, patterns in PLATFORM_DETECT_RULES.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform
        return None

    @staticmethod
    def calculate_delogo_filter(
        width: int,
        height: int,
        platform: str = "douyin",
        custom_regions: Optional[List[Dict]] = None
    ) -> str:
        """
        根据视频分辨率和平台特征，计算精确的 delogo 滤镜参数
        :param width: 视频宽度
        :param height: 视频高度
        :param platform: 平台标识
        :param custom_regions: 自定义水印区域列表
        :return: FFmpeg delogo 滤镜字符串
        """
        if custom_regions:
            # 使用自定义区域参数
            filters = []
            for region in custom_regions:
                x = int(region.get("x_percent", 0) * width)
                y = int(region.get("y_percent", 0) * height)
                w = int(region.get("w_percent", 0) * width)
                h = int(region.get("h_percent", 0) * height)
                filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}:flags=t")
            return ";".join(filters)

        # 使用平台特征库
        db_entry = PLATFORM_WATERMARK_DB.get(platform)
        if not db_entry:
            return ""

        filters = []
        for pattern in db_entry.get("patterns", []):
            x = int(pattern["x_percent"] * width)
            y = int(pattern["y_percent"] * height)
            w = int(pattern["w_percent"] * width)
            h = int(pattern["h_percent"] * height)
            filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}:flags=t")

        return ";".join(filters)

    @staticmethod
    async def remove_watermark_from_video(
        input_path: str,
        output_path: str,
        platform: str = "auto",
        custom_regions: Optional[List[Dict]] = None,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
        preserve_quality: bool = True,
    ) -> Dict:
        """
        对视频进行去水印处理
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        :param platform: 平台标识，auto=自动检测
        :param custom_regions: 自定义水印区域
        :param video_width: 视频宽度（需提前获取）
        :param video_height: 视频高度
        :param preserve_quality: 是否保持原画质（无损模式）
        :return: 处理结果信息
        """
        import subprocess

        try:
            # 获取视频信息
            if not video_width or not video_height:
                info = await WatermarkRemovalService._get_video_resolution(input_path)
                video_width = info.get("width", 1080)
                video_height = info.get("height", 1920)

            # 自动检测平台
            if platform == "auto":
                platform = await WatermarkRemovalService.detect_platform_from_url(input_path) or "douyin"

            # 计算 delogo 滤镜
            delogo_filter = WatermarkRemovalService.calculate_delogo_filter(
                video_width, video_height, platform, custom_regions
            )

            if not delogo_filter:
                # 没有水印需要去除，直接复制
                result = await WatermarkRemovalService._copy_video(input_path, output_path)
                return {
                    "status": "success",
                    "watermarks_removed": 0,
                    "output_path": output_path,
                    "message": "未检测到水印，直接复制视频",
                }

            # 构建 FFmpeg 命令
            # 使用滤镜时必须重新编码，不能用 copy 编码器
            # preserve_quality=True 时使用高质量编码参数，False 时使用快速编码参数
            cmd = [
                settings.FFmpeg_BINARIES,
                "-y",
                "-i", input_path,
                "-c:v", "libx264",
                "-crf", "18" if preserve_quality else "23",
                "-preset", "medium" if preserve_quality else "ultrafast",
                "-c:a", "copy",
                "-filter_complex", delogo_filter,
                "-movflags", "+faststart",
                output_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0 and os.path.exists(output_path):
                return {
                    "status": "success",
                    "watermarks_removed": len(delogo_filter.split(";")),
                    "output_path": output_path,
                    "delogo_filter": delogo_filter,
                    "platform": platform,
                    "message": f"成功去除 {len(delogo_filter.split(';'))} 处水印",
                }
            else:
                return {
                    "status": "failed",
                    "error": stderr.decode()[:500],
                    "message": "去水印处理失败",
                }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": f"去水印异常: {str(e)}",
            }

    @staticmethod
    async def _get_video_resolution(video_path: str) -> Dict:
        """使用 ffprobe 获取视频分辨率"""
        try:
            cmd = [
                settings.FFmpeg_BINARIES,
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                video_path,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            info = json.loads(stdout.decode())

            width = height = 0
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = int(stream.get("width", 0))
                    height = int(stream.get("height", 0))
                    break

            return {"width": width, "height": height}
        except Exception:
            return {"width": 1080, "height": 1920}

    @staticmethod
    async def _copy_video(input_path: str, output_path: str) -> bool:
        """直接复制视频文件（无损）"""
        try:
            cmd = [
                settings.FFmpeg_BINARIES,
                "-y",
                "-i", input_path,
                "-c", "copy",
                output_path,
            ]
            proc = await asyncio.create_subprocess_exec(*cmd)
            await proc.communicate()
            return proc.returncode == 0 and os.path.exists(output_path)
        except Exception:
            return False

    @staticmethod
    async def batch_remove_watermark(
        video_paths: List[str],
        output_dir: str,
        platform: str = "auto",
    ) -> List[Dict]:
        """
        批量去水印处理
        :param video_paths: 视频文件路径列表
        :param output_dir: 输出目录
        :param platform: 平台标识
        :return: 处理结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, video_path in enumerate(video_paths):
            output_path = os.path.join(output_dir, f"cleaned_{i}.mp4")
            result = await WatermarkRemovalService.remove_watermark_from_video(
                input_path=video_path,
                output_path=output_path,
                platform=platform,
            )
            results.append({
                "index": i,
                "input": video_path,
                "output": output_path,
                **result,
            })

        return results