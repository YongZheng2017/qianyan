"""
Token / 凭证加密工具

使用 Fernet 对称加密算法对数据源凭证进行加密存储
"""
import json
from cryptography.fernet import Fernet, InvalidToken
from ..core.config import settings


def _get_fernet() -> Fernet:
    """获取 Fernet 实例"""
    key = settings.ENC_KEY
    if not key:
        raise ValueError(
            "未配置数据源加密密钥 ENC_KEY，请在 .env 中设置。"
            "生成方式：python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_token(token: str) -> str:
    """
    加密 Token

    Args:
        token: 明文 Token

    Returns:
        str: 加密后的 Token 字符串
    """
    if not token:
        return ""
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """
    解密 Token

    Args:
        encrypted: 加密的 Token 字符串

    Returns:
        str: 明文 Token（解密失败返回空字符串）
    """
    if not encrypted:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted.encode()).decode()
    except (InvalidToken, Exception):
        return ""


def mask_token(token: str) -> str:
    """
    Token 脱敏

    Args:
        token: 明文 Token

    Returns:
        str: 脱敏后的 Token（只显示前4位和后4位）
    """
    if not token:
        return ""
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}****{token[-4:]}"


# ---------- 凭证（多字段）加密工具 ----------

def encrypt_json(data: dict) -> str:
    """加密 dict（序列化为 JSON 后加密）"""
    if not data:
        return ""
    f = _get_fernet()
    return f.encrypt(json.dumps(data, ensure_ascii=False).encode()).decode()


def decrypt_json(encrypted: str) -> dict:
    """解密为 dict（解密失败返回空 dict）"""
    if not encrypted:
        return {}
    try:
        f = _get_fernet()
        return json.loads(f.decrypt(encrypted.encode()).decode())
    except (InvalidToken, Exception):
        return {}


def mask_credentials(creds: dict) -> dict:
    """对凭证 dict 的每个字符串值脱敏"""
    result = {}
    for k, v in (creds or {}).items():
        if isinstance(v, str):
            result[k] = mask_token(v)
        else:
            result[k] = "****" if v else ""
    return result