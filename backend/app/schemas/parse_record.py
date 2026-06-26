"""
解析记录 Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ParseRecordCreate(BaseModel):
    """创建解析记录"""
    video_url: str = Field(..., description="视频URL或本地路径")


class SceneItem(BaseModel):
    """分镜项"""
    start: float
    end: float
    duration: float


class ScriptItem(BaseModel):
    """文案脚本项"""
    type: str  # speech/subtitle
    start: float
    end: float
    text: str
    source: str  # whisper/ocr


class WatermarkInfo(BaseModel):
    """水印信息"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    delogo_filter: str


class VideoInfo(BaseModel):
    """视频基础信息"""
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    format: str
    video_codec: str
    audio_codec: str


class ParseResult(BaseModel):
    """完整解析结果"""
    video_info: VideoInfo
    script: List[ScriptItem]
    scenes: List[SceneItem]
    bgm_path: str
    watermark: WatermarkInfo
    status: str


class ParseRecordOut(BaseModel):
    """解析记录输出"""
    id: int
    user_id: int
    video_url: str
    result_json: Optional[str]
    status: str
    progress: float
    duration: Optional[float]
    error_message: str
    created_at: datetime

    class Config:
        from_attributes = True
