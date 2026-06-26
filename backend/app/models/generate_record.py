"""
生成记录模型
- 关联解析记录
- 生成参数、成品视频地址、状态追踪
- 支持AI生成和本地合成两种模式
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base
from app.models.base import TimestampMixin


class GenerateStatus(str, enum.Enum):
    """生成状态枚举"""
    PENDING = "pending"           # 排队中
    EDITING = "editing"           # 编辑中
    PROCESSING = "processing"     # 处理中（AI生成/本地合成）
    SUCCESS = "success"           # 成功
    FAILED = "failed"             # 失败


class GenerateMode(str, enum.Enum):
    """生成模式枚举"""
    AI_GENERATE = "ai_generate"   # AI生成
    LOCAL_COMPOSE = "local_compose"  # 本地合成


class GenerateRecord(Base, TimestampMixin):
    """生成记录表"""
    __tablename__ = "generate_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    parse_id = Column(
        Integer, ForeignKey("parse_records.id"), nullable=False, comment="关联解析ID"
    )

    # 生成模式
    generate_mode = Column(
        SAEnum(GenerateMode), default=GenerateMode.AI_GENERATE, comment="生成模式: ai_generate/local_compose"
    )

    # 编辑参数
    edited_script = Column(Text, default="", comment="编辑后的文案脚本")
    edited_scenes = Column(Text, default="[]", comment="编辑后的分镜列表")
    voice_tone = Column(String(50), default="", comment="配音音色")
    replace_materials = Column(Text, default="[]", comment="替换素材列表")

    # AI生成参数
    aspect_ratio = Column(String(10), default="9:16", comment="画面比例: 9:16/16:9/1:1")
    ai_platform = Column(String(20), default="jimeng", comment="AI平台: jimeng/kling")
    generation_params = Column(Text, default="{}", comment="AI生成参数JSON")

    # 生成结果
    output_video_url = Column(String(1000), default="", comment="成品视频地址")
    output_local_path = Column(String(500), default="", comment="本地存储路径")
    output_thumbnail = Column(String(1000), default="", comment="成品缩略图地址")
    output_duration = Column(Float, default=0, comment="成品视频时长(秒)")

    # 状态
    status = Column(
        SAEnum(GenerateStatus), default=GenerateStatus.PENDING, comment="状态: pending/processing/success/failed"
    )
    progress = Column(Float, default=0.0, comment="进度 0-100")
    error_message = Column(String(500), default="", comment="错误信息")

    # 消耗
    cost_credits = Column(Integer, default=5, comment="消耗积分")

    # 完成时间
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 索引
    __table_args__ = (
        Index("idx_gen_user", "user_id", "created_at"),
        Index("idx_gen_status", "status"),
    )

    # 关系
    user = relationship("User", back_populates="generate_records")
    parse_record = relationship("ParseRecord", backref="generate_records")
