"""敏感字段加密与脱敏。

- 加密算法：AES-256-GCM（对称、带认证标签）。
- 密钥来源：`settings.DATA_ENCRYPTION_KEY`，经 SHA-256 派生为 32 字节密钥。
- 落库格式：base64(nonce(12B) + ciphertext + tag)。
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

_NONCE_LEN = 12


def _key() -> bytes:
    return hashlib.sha256(settings.DATA_ENCRYPTION_KEY.encode("utf-8")).digest()


def encrypt_field(value: str | None) -> str | None:
    """加密敏感字段；空值原样返回。"""
    if value is None or value == "":
        return value
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = AESGCM(_key()).encrypt(nonce, value.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_field(value: str | None) -> str | None:
    """解密敏感字段；空值或非密文（历史明文）原样返回，保证兼容。"""
    if value is None or value == "":
        return value
    try:
        raw = base64.b64decode(value)
        nonce, ciphertext = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
        return AESGCM(_key()).decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception:
        return value


def mask_value(value: str | None, keep_head: int = 3, keep_tail: int = 4) -> str:
    """通用脱敏：保留首尾，中间以 * 代替。"""
    if not value:
        return value or ""
    if len(value) <= keep_head + keep_tail:
        return "*" * len(value)
    return f"{value[:keep_head]}{'*' * (len(value) - keep_head - keep_tail)}{value[-keep_tail:]}"


def mask_phone(phone_cipher: str | None) -> str:
    """手机号脱敏展示（先解密再脱敏，如 138****1234）。"""
    plain = decrypt_field(phone_cipher)
    return mask_value(plain)
