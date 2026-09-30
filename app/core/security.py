from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import get_settings


settings = get_settings()

ALGORITHM = "HS256"

password_hash = PasswordHash(
    (
        Argon2Hasher(),
    )
)


def hash_password(password: str) -> str:
    """
    Securely hash a password using Argon2.
    """
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plain password against a stored hash.
    """
    return password_hash.verify(password, hashed)


def create_access_token(subject: str) -> str:
    """
    Create a JWT access token.
    """
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": subject,
        "exp": expires,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> int | None:
    """
    Decode JWT and return the user ID.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )

        subject = payload.get("sub")

        if not subject:
            return None

        return int(subject)

    except (JWTError, ValueError, TypeError):
        return None