from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

import jwt

from app.core.config import settings

PBKDF2_ITERATIONS = 200_000


def _pbkdf2_hash(password: str, salt: str, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return digest.hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    checksum = _pbkdf2_hash(password=password, salt=salt, iterations=PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${checksum}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iteration_raw, salt, expected_checksum = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iteration_raw)
    except (ValueError, TypeError):
        return False

    actual_checksum = _pbkdf2_hash(password=password, salt=salt, iterations=iterations)
    return hmac.compare_digest(actual_checksum, expected_checksum)


def create_access_token(user_id: int, role: str) -> str:
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
