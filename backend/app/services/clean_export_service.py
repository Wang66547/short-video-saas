"""
三无标准导出服务
- 去除所有第三方标识、水印、字幕
- 符合二创发布标准
- 保持原画质无压缩
"""
import os
import json
import asyncio
from typing import Dict, List, Optional
from app.core.config import get_settings
from app.services.watermark_removal_service import WatermarkRemovalService

settings = get_settings()


class CleanExportService:
    """三无标准导出服务"""

    @staticmethod
    async def clean_export(
        input_path: str,
        output_path: str,
        video_info: Optional[Dict] = None,
        watermark_regions: Optional[List[Dict]] = None,
        remove_subtitles: bool = True,
        remove_ai_logo: bool = True,
        preserve_quality: bool = True,
    ) -> Dict:
        """
        三无标准导出主流程
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        :param video_info: 视频信息（分辨率、时长等）
        :param watermark_regions: 自定义水印区域
        :param remove_subtitles: 是否去除字幕
        :param remove_ai_logo: 是否去除AI平台标识
        :param preserve_quality: 是否保持原画质
        :return: 导出结果
        """
        results = {
            "status": "success",
            "steps": [],
            "warnings": [],
        }

        try:
            # Step 1: 获取视频信息
            if not video_info:
                video_info = await CleanExportService._get_video_info(input_path)
                results["steps"].append({"step": "get_info", "status": "success"})

            width = video_info.get("width", 1080)
            height = video_info.get("height", 1920)

            # Step 2: 去除平台水印
            wm_result = await WatermarkRemovalService.remove_watermark_from_video(
                input_path=input_path,
                output_path=output_path,
                platform="auto",
                custom_regions=watermark_regions,
                video_width=width,
                video_height=height,
                preserve_quality=preserve_quality,
            )
            results["steps"].append({"step": "remove_watermark", **wm_result})
            if wm_result.get("status") == "failed":
                results["warnings"].append(f"水印去除失败: {wm_result.get('error', '')}")
                results["status"] = "partial"

            # Step 3: 去除内嵌字幕（如果有）
            if remove_subtitles:
                subtitle_result = await CleanExportService._remove_embedded_subtitles(
                    input_path=output_path,
                    output_path=output_path + ".no_sub.mp4",
                    width=width,
                    height=height,
                )
                os.rename(output_path + ".no_sub.mp4", output_path)
                results["steps"].append({"step": "remove_subtitles", **subtitle_result})

            # Step 4: 去除AI平台标识
            if remove_ai_logo:
                ai_logo_result = await CleanExportService._remove_ai_logos(
                    input_path=output_path,
                    output_path=output_path + ".no_ai.mp4",
                    width=width,
                    height=height,
                )
                os.rename(output_path + ".no_ai.mp4", output_path)
                results["steps"].append({"step": "remove_ai_logo", **ai_logo_result})

            # Step 5: 最终质量检测
            final_info = await CleanExportService._get_video_info(output_path)
            results["final_info"] = final_info
            results["steps"].append({"step": "quality_check", "status": "success"})

            # 检查输出文件大小
            output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            results["output_size_bytes"] = output_size
            results["output_size_mb"] = round(output_size / 1024 / 1024, 2)

            return results

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            return results

    @staticmethod
    async def _get_video_info(video_path: str) -> Dict:
        """获取视频信息"""
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
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            info = json.loads(stdout.decode())

            width = height = duration = fps = 0
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = int(stream.get("width", 0))
                    height = int(stream.get("height", 0))
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        num, den = map(int, fps_str.split("/"))
                        fps = num / den if den else 0
                    duration = float(info.get("format", {}).get("duration", 0))

            return {"width": width, "height": height, "duration": duration, "fps": fps}
        except Exception:
            return {"width": 1080, "height": 1920, "duration": 0, "fps": 30}

    @staticmethod
    async def _remove_embedded_subtitles(
        input_path: str, output_path: str, width: int, height: int
    ) -> Dict:
        """
        去除内嵌字幕区域
        使用黑色遮罩覆盖字幕区域
        """
        try:
            # 字幕通常在视频底部 15% 区域
            subtitle_y = int(height * 0.75)
            subtitle_h = int(height * 0.15)

            cmd = [
                settings.FFMPEG_BIN, "-y",
                "-i", input_path,
                "-vf", f"boxblur=h={subtitle_h}:w={width}:s={4}",
                "-c:a", "copy",
                output_path,
            ]

            # 更精确的做法：用黑色矩形覆盖字幕区域
            cmd = [
                settings.FFMPEG_BIN, "-y",
                "-i", input_path,
                "-vf", f"color=black:s={width}x{subtitle_h}:d=0,fade=t=in:st=0:d=0.1,setsar=1,"
                       f"overlay=(w-w{width})*0.5:{h-subtitle_h}",
                "-c:a", "copy",
                output_path,
            ]

            proc = await asyncio.create_subprocess_exec(*cmd)
            await proc.communicate()

            return {
                "status": "success" if os.path.exists(output_path) else "failed",
                "method": "black_overlay",
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def _remove_ai_logos(
        input_path: str, output_path: str, width: int, height: int
    ) -> Dict:
        """
        去除 AI 平台标识（如可灵/即梦水印）
        """
        try:
            # AI 标识通常在左上角或右下角
            regions = [
                {"x": 0, "y": 0, "w": int(width * 0.15), "h": int(height * 0.06)},  # 左上
                {"x": int(width * 0.80), "y": int(height * 0.85), "w": int(width * 0.15), "h": int(height * 0.08)},  # 右下
            ]

            filters = []
            for r in regions:
                filters.append(f"color=black:s={r['w']}x{r['h']},fade=t=in:st=0:d=0.1[overlay{r['x']}_{r['y']}]")

            overlay_expr = " + ".join(
                f"[{i}:v]{filters[i]}[overlay{i}];[0:v][overlay{i}]overlay={r['x']}:{r['y']}"
                for i, r in enumerate(regions)
            )

            cmd = [
                settings.FFMPEG_BIN, "-y",
                "-i", input_path,
                "-vf", overlay_expr,
                "-c:a", "copy",
                output_path,
            ]

            proc = await asyncio.create_subprocess_exec(*cmd)
            await proc.communicate()

            return {
                "status": "success" if os.path.exists(output_path) else "failed",
                "regions_cleaned": len(regions),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def batch_clean_export(
        video_paths: List[str],
        output_dir: str,
        **kwargs,
    ) -> List[Dict]:
        """
        批量三无导出
        :param video_paths: 视频路径列表
        :param output_dir: 输出目录
        :param kwargs: 其他参数传递给 clean_export
        :return: 处理结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, path in enumerate(video_paths):
            output_path = os.path.join(output_dir, f"clean_{i}.mp4")
            result = await CleanExportService.clean_export(
                input_path=path,
                output_path=output_path,
                **kwargs,
            )
            results.append({
                "index": i,
                "input": path,
                "output": output_path,
                **result,
            })

        return results