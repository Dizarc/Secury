import jwt

from pwdlib import PasswordHash
from typing import Any
from datetime import timedelta, datetime

from backend.app.core.config import settings


ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

def create_access_token(data: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now() + expires_delta
    to_encode = {"exp": expire, "sub": str(data)}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

