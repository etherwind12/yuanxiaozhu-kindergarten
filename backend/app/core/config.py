"""全局配置。通过环境变量覆盖，默认值可直接本地运行。"""

import os
from pathlib import Path

# 后端根目录（backend/）。数据库等文件路径固定到项目内，
# 避免因启动目录（cwd）不同而连到/新建另一个数据库文件。
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "园小助")
    API_PREFIX: str = "/api"

    # 数据库：默认固定为 backend/kindergarten.db 的绝对路径
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'kindergarten.db').as_posix()}"
    )

    # 鉴权
    SECRET_KEY: str = os.getenv("SECRET_KEY", "yuanxiaozhu-dev-secret-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

    # 敏感字段加密密钥（AES）。生产环境务必通过环境变量注入，勿使用默认值。
    DATA_ENCRYPTION_KEY: str = os.getenv("DATA_ENCRYPTION_KEY", "yuanxiaozhu-dev-aes-key-change-me")

    # 允许跨域的前端地址
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    # 二维码落地页基地址（扫码后跳转的前端地址）
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:5173")

    # AI 助手：配置 DeepSeek 后用大模型对话，留空则走本地规则引擎
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


settings = Settings()
