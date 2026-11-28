# 文件：app/identity/services/credential.py
"""Doris 查询密码的加密与解密。"""

from cryptography.fernet import Fernet, InvalidToken

from app.identity.errors import DorisCredentialError


class DorisCredentialCipher:
    """使用 Fernet 加密与解密 Doris 查询密码。"""

    def __init__(self, encryption_key: str) -> None:
        """使用 Fernet 密钥初始化凭据加密器。"""
        try:
            # 密钥必须是 44 字符 url-safe base64；格式错在初始化时就炸，不等第一次解密
            self._fernet = Fernet(encryption_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise ValueError("Doris 凭据加密主密钥格式无效") from exc

    def encrypt(self, password: str) -> str:
        """加密 Doris 查询密码。"""
        if not password:
            raise ValueError("Doris 查询密码不能为空")
        # 密文是 ASCII 的 url-safe base64，decode 成 str 存 text 列
        return self._fernet.encrypt(password.encode("utf-8")).decode("ascii")

    def decrypt(self, encrypted_password: str) -> str:
        """解密 Doris 查询密码。"""
        try:
            return self._fernet.decrypt(encrypted_password.encode("ascii")).decode(
                "utf-8"
            )
        except (InvalidToken, UnicodeDecodeError, UnicodeEncodeError) as exc:
            # 密钥不对、密文被篡改、编码异常统一转成本模块异常，上层不认识 cryptography
            raise DorisCredentialError("Doris 查询凭据解密失败") from exc