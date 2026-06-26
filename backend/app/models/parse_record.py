"""
解析记录模型
- 用户视频解析任务记录
- 来源URL、解析结果、状态追踪
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base
from app.models.base import TimestampMixin


class ParseStatus(str, enum.Enum):
    """解析状态枚举"""
    PENDING = "pending"       # 排队中
    PROCESSING = "processing" # 处理中
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败


class ParseRecord(Base, TimestampMixin):
    """解析记录表"""
    __tablename__ = "parse_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    video_url = Column(String(1000), nullable=False, comment="原视频地址")
    # 解析结果JSON（视频信息、音轨、字幕等）
    result_json = Column(Text, default="", comment="解析结果JSON")
    status = Column(
        SAEnum(ParseStatus), default=ParseStatus.PENDING, comment="状态: pending/processing/success/failed"
    )
    # 处理进度
    progress = Column(Float, default=0.0, comment="进度 0-100")
    # 处理耗时（秒）
    duration = Column(Float, default=0, comment="耗时(秒)")
    error_message = Column(String(500), default="", comment="错误信息")

    # 关系
    user = relationship("User", back_populates="parse_records")
