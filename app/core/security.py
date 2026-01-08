from datetime import datetime, timedelta
from jose import jwt
import bcrypt
import hashlib
import base64
from app.core.config import settings


def _hash_password_input(password: str) -> bytes:
    # Hash with SHA-256 first to allow unlimited password length
    # Convert to base64 to ensure it's within bcrypt's 72-byte limit
    # base64 encoding of 32 bytes = 44 characters, well under 72
    sha_hash = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(sha_hash)[:72]


def hash_password(password: str) -> str:
    hashed_input = _hash_password_input(password)
    return bcrypt.hashpw(hashed_input, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    hashed_input = _hash_password_input(password)
    return bcrypt.checkpw(hashed_input, hashed.encode("utf-8"))


def create_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
