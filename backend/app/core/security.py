"""Security utilities: password hashing, JWT tokens, and encryption."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone  # noqa: UP017
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": TOKEN_TYPE_ACCESS,
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str | int) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": TOKEN_TYPE_REFRESH,
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


# AES-GCM encryption for API keys
def get_encryption_key() -> bytes:
    """Derive a 32-byte encryption key from the master key using SHA-256."""
    key = settings.app_master_key
    return hashlib.sha256(key.encode("utf-8")).digest()


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key using AES-256-GCM."""
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Return as hex: nonce + ciphertext
    return (nonce + ciphertext).hex()


def _get_legacy_encryption_key() -> bytes:
    """Legacy key derivation (zero-padded) for backward compatibility."""
    key = settings.app_master_key
    if len(key) < 32:
        key = key.ljust(32, "0")
    return key[:32].encode("utf-8")


def decrypt_api_key(encrypted_hex: str) -> str:
    """Decrypt an API key from AES-256-GCM. Tries new key first, falls back to legacy."""
    data = bytes.fromhex(encrypted_hex)
    nonce = data[:12]
    ciphertext = data[12:]

    # Try SHA-256 derived key first
    try:
        aesgcm = AESGCM(get_encryption_key())
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception:
        pass

    # Fall back to legacy zero-padded key
    aesgcm = AESGCM(_get_legacy_encryption_key())
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Mask an API key showing only the last N characters."""
    if len(key) <= visible_chars:
        return "*" * len(key)
    return "*" * (len(key) - visible_chars) + key[-visible_chars:]
