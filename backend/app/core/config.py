"""
核心配置模块
使用 pydantic-settings 加载 .env 文件和环境变量
所有配置集中管理，支持多环境覆盖
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """应用全局配置"""

    # ==================== 应用基础 ====================
    APP_NAME: str = "爆款短视频复刻SaaS平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS 允许的源域名列表
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ==================== 数据库 ====================
    DATABASE_URL: str = "sqlite+aiosqlite:///./short_video_saas.db"
    DATABASE_SYNC_URL: str = "sqlite:///./short_video_saas.db"

    # ==================== Redis ====================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==================== Celery 异步任务 ====================
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ==================== JWT 认证 ====================
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== 接口限流配置 ====================
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_DAY: int = 10000

    # ==================== 视频处理 ====================
    FFmpeg_BINARIES: str = "ffmpeg"
    TEMP_DIR: str = "./temp"
    VIDEO_STORAGE_PATH: str = "./videos"
    MAX_VIDEO_SIZE_MB: int = 500

    # ==================== AI 视频生成 ====================
    JIMENG_API_KEY: str = ""
    JIMENG_BASE_URL: str = "https://api.jimeng.jianying.com/visual/api"
    KLING_API_KEY: str = ""
    KLING_BASE_URL: str = "https://klingai.com/api"
    DEFAULT_AI_PLATFORM: str = "jimeng"

    # ==================== Whisper 语音识别 ====================
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_LANGUAGE: str = "zh"

    # ==================== TTS 语音合成 ====================
    DEFAULT_TTS_PROVIDER: str = "ali"
    ALIYUN_TTS_API_KEY: str = ""
    ALIYUN_TTS_APP_KEY: str = ""
    TENCENT_TTS_SECRET_ID: str = ""
    TENCENT_TTS_SECRET_KEY: str = ""

    # ==================== 大模型（文案改写） ====================
    OPENAI_API_BASE: str = "https://apihub.agnes-ai.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "agnes-2.0-flash"

    # ==================== 支付配置 ====================
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    WECHAT_MCH_ID: str = ""
    WECHAT_API_KEY: str = ""
    WECHAT_NOTIFY_URL: str = "/api/payments/wechat/notify"
    WECHAT_CERT_PATH: str = ""
    WECHAT_CERT_SERIAL_NO: str = ""
    WECHAT_PRIVATE_KEY_PATH: str = ""

    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_NOTIFY_URL: str = "/api/payments/alipay/notify"
    ALIPAY_GATEWAY: str = "https://openapi.alipay.com/gateway.do"

    # ==================== 短信服务 ====================
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = ""
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: str = ""
    ALIBABA_CLOUD_SMS_TEMPLATE_ID: str = ""
    ALIBABA_CLOUD_SIGN_NAME: str = ""

    # ==================== 每日次数配置 ====================
    FREE_DAILY_PARSE_LIMIT: int = 3
    FREE_DAILY_GENERATE_LIMIT: int = 1
    BASIC_DAILY_PARSE_LIMIT: int = 10
    BASIC_DAILY_GENERATE_LIMIT: int = 5
    PREMIUM_DAILY_PARSE_LIMIT: int = 50
    PREMIUM_DAILY_GENERATE_LIMIT: int = 20

    # ==================== 其他 ====================
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024
    PAGE_SIZE: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """生产环境禁止使用弱默认密钥"""
        import os
        is_production = os.environ.get("ENV", "").lower() in ("production", "prod")
        if v == "your-super-secret-key-change-in-production-min-32-chars":
            if is_production:
                import sys
                print("[FATAL] SECRET_KEY 未修改，生产环境必须设置强随机密钥！", file=sys.stderr)
                sys.exit(1)
            # 开发环境仅警告
            import sys
            print("[WARNING] 使用默认 SECRET_KEY，请修改为随机字符串", file=sys.stderr)
        elif len(v) < 32:
            if is_production:
                import sys
                print("[FATAL] SECRET_KEY 长度不足 32 字符！", file=sys.stderr)
                sys.exit(1)
            import sys
            print(f"[WARNING] SECRET_KEY 长度仅 {len(v)} 字符，建议使用 32+ 字符随机密钥", file=sys.stderr)
        return v

    @field_validator("DEBUG")
    @classmethod
    def validate_debug_production(cls, v: bool) -> bool:
        """生产环境强制 DEBUG=False"""
        import os
        is_production = os.environ.get("ENV", "").lower() in ("production", "prod")
        if is_production and v:
            import sys
            print("[FATAL] 生产环境 DEBUG 必须为 False！", file=sys.stderr)
            sys.exit(1)
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_password(cls, v: str) -> str:
        """检测弱密码并给出警告"""
        if "root:root123" in v:
            import sys
            print("[WARNING] 数据库使用默认弱密码 root:root123，生产环境请修改！", file=sys.stderr)
        return v


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
