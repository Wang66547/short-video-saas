"""
生成记录 Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SceneEditItem(BaseModel):
    """分镜编辑项"""
    start: float
    end: float
    duration: float
    script: str
    material_url: Optional[str] = None


class VoiceToneSelect(BaseModel):
    """配音音色选择"""
    voice_id: str
    voice_name: str
    speed: float = 1.0
    pitch: float = 0


class MaterialReplace(BaseModel):
    """素材替换"""
    scene_index: int
    original_url: str
    replace_url: str


class AIGenerationParams(BaseModel):
    """AI生成参数"""
    aspect_ratio: str = "9:16"
    ai_platform: str = "jimeng"
    prompt: str = ""
    negative_prompt: str = ""
    seed: Optional[int] = None
    steps: int = 25
    guidance_scale: float = 7.5


class GenerateRecordCreate(BaseModel):
    """创建生成记录"""
    parse_id: int
    generate_mode: str = "ai_generate"
    edited_script: Optional[str] = ""
    edited_scenes: Optional[str] = "[]"
    voice_tone: Optional[str] = ""
    replace_materials: Optional[str] = "[]"
    aspect_ratio: str = "9:16"
    ai_platform: str = "jimeng"
    generation_params: Optional[str] = "{}"


class GenerateRecordEdit(BaseModel):
    """编辑生成参数"""
    edited_script: Optional[str] = None
    edited_scenes: Optional[List[SceneEditItem]] = None
    voice_tone: Optional[VoiceToneSelect] = None
    replace_materials: Optional[List[MaterialReplace]] = None
    aspect_ratio: Optional[str] = None
    generation_params: Optional[AIGenerationParams] = None


class GenerateRecordOut(BaseModel):
    """生成记录输出"""
    id: int
    user_id: int
    parse_id: int
    generate_mode: str
    edited_script: Optional[str]
    edited_scenes: Optional[str]
    voice_tone: Optional[str]
    replace_materials: Optional[str]
    aspect_ratio: str
    ai_platform: str
    generation_params: Optional[str]
    output_video_url: str
    output_local_path: str
    output_thumbnail: str
    output_duration: float
    status: str
    progress: float
    cost_credits: int
    error_message: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GenerateResult(BaseModel):
    """生成结果"""
    record_id: int
    output_video_url: str
    output_thumbnail: str
    output_duration: float
    cost_credits: int
    status: str
