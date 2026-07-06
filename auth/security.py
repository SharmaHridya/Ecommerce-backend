from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# A single shared CryptContext for the whole app. "bcrypt" is the scheme;
# "auto" deprecation means if we ever add a stronger scheme later, passlib
# will know existing bcrypt hashes are still valid but "deprecated".
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """One-way hash. Used at registration time."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Used at login time: hashes the candidate password the same way
    and compares — we never decrypt the stored hash, because we can't."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Builds and signs a JWT.

    `data` typically looks like {"sub": str(user.id)}.
    "sub" (subject) is a standard JWT claim name for "who this token is about".
    We always store it as a string per the JWT spec, even though our user_id is an int.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    """
    Verifies the signature and expiry, returns the payload if valid,
    or None if the token is invalid/expired/tampered with.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
