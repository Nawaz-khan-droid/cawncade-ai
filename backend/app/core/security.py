"""
Security Module.
Handles JWT authentication, password hashing, and input sanitization.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import re  # REFACTOR-06 FIX: module-level import, not inside function body
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config.settings import get_settings

import bcrypt

settings = get_settings()
security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> int:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return int(user_id)


def sanitize_input(text: str) -> str:
    """
    Sanitizes user input to reduce prompt injection surface.

    Defense-in-depth strategy (SEC-05):
      Layer 1 — Length cap: hard-limits input to prevent context flooding.
      Layer 2 — Unicode stripping: removes zero-width/lookalike chars used for obfuscation.
      Layer 3 — Keyword blocklist: strips common literal injection phrases.
      Layer 4 — Case-obfuscation regex: catches mixed-case variants like 'IgnOrE pReViOuS'.

    Note: The primary structural defense is that ALL user input is passed to the
    LLM wrapped inside explicit delimiters in the system prompt (e.g.,
    <user_claim>...</user_claim>). This sanitizer is a secondary hardening layer,
    not the only line of defense.
    """
    if not isinstance(text, str):
        return ""

    # Layer 1: Hard length cap (prevents context-window flooding)
    text = text[:4000]

    # Layer 2: Strip zero-width and unicode lookalike characters used for obfuscation.
    # These invisible characters can bypass simple string matching.
    import unicodedata
    text = "".join(
        c for c in text
        if not unicodedata.category(c).startswith("C")  # removes control/format chars
        or c in ("\n", "\r", "\t")  # but preserve normal whitespace
    )

    # Layer 3: Literal phrase blocklist (fast O(1) loop)
    blocked_literals = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard previous",
        "system prompt",
        "override",
        "you are now",
        "act as if you",
        "pretend you are",
        "pretend to be",
        "jailbreak",
        "developer mode",
        "dan mode",
    ]
    sanitized = text
    for pattern in blocked_literals:
        sanitized = re.sub(re.escape(pattern), "", sanitized, flags=re.IGNORECASE)

    # Layer 4: Catch mixed-case/spaced obfuscation (e.g. "i G n O r E p R e V i O u S")
    obfuscation_patterns = [
        r"i\W*g\W*n\W*o\W*r\W*e\W+p\W*r\W*e\W*v\W*i\W*o\W*u\W*s",
        r"d\W*i\W*s\W*r\W*e\W*g\W*a\W*r\W*d",
        r"s\W*y\W*s\W*t\W*e\W*m\W+p\W*r\W*o\W*m\W*p\W*t",
        r"j\W*a\W*i\W*l\W*b\W*r\W*e\W*a\W*k",
    ]
    for obf_pattern in obfuscation_patterns:
        sanitized = re.sub(obf_pattern, "", sanitized, flags=re.IGNORECASE)

    return sanitized.strip()
