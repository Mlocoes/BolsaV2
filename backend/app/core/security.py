import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, password)
        return True
    except:
        return False

def generate_token() -> str:
    return secrets.token_hex(32)

def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    token = generate_token()
    return token, expire
