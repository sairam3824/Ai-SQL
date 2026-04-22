import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _build_key(raw_key: str | None) -> bytes:
    if raw_key:
        digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)
    return _load_or_create_local_key()


def _local_key_path() -> Path:
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings.storage_dir / ".config.key"


def _load_or_create_local_key() -> bytes:
    key_path = _local_key_path()
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip().encode("utf-8")

    generated = Fernet.generate_key()
    # Atomic creation with restricted permissions to avoid race conditions
    fd = os.open(str(key_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, generated)
    finally:
        os.close(fd)
    return generated


class ConfigCipher:
    def __init__(self) -> None:
        settings = get_settings()
        self._fernet = Fernet(_build_key(settings.app_encryption_key))

    def encrypt_json(self, payload: dict[str, Any]) -> str:
        return self._fernet.encrypt(json.dumps(payload).encode("utf-8")).decode("utf-8")

    def decrypt_json(self, token: str) -> dict[str, Any]:
        return json.loads(self._fernet.decrypt(token.encode("utf-8")).decode("utf-8"))


def redact_config(payload: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if any(secret in key.lower() for secret in ("password", "secret", "token")):
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted
