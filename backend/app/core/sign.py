"""统一签名工具。

基于 `SECRET_KEY` 派生 HMAC-SHA256，供导出水印、资产二维码、扫码令牌共用，
实现「服务端签名、客户端可校验」的防伪溯源能力。
"""

import base64
import hashlib
import hmac

from app.core.config import settings

# 与加密密钥域隔离，避免同一把钥匙两用
_KEY_SALT = b"yuanxiaozhu-sign-v1"


def _key() -> bytes:
    return hashlib.sha256(_KEY_SALT + settings.SECRET_KEY.encode("utf-8")).digest()


def sign(data: str) -> str:
    """返回 URL 安全的 HMAC 签名串（完整 43 字符）。"""
    digest = hmac.new(_key(), data.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify(data: str, signature: str) -> bool:
    """常量时间比对，防时序侧信道。"""
    return hmac.compare_digest(sign(data), signature)


def short_code(data: str, length: int = 16) -> str:
    """便于人工核对的大写短码，用于报表水印（可读、可追溯）。"""
    digest = hmac.new(_key(), data.encode("utf-8"), hashlib.sha256).hexdigest().upper()
    return digest[:length]
