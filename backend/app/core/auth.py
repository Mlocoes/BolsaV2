from typing import Optional
from fastapi import HTTPException, status
from .session import session_manager
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar si la contraseña coincide con el hash"""
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Obtener el hash de una contraseña"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    
    return hashed.decode('utf-8')

async def create_user_session(user_id: str, user_data: dict) -> str:
    """Crear una sesión de usuario"""
    return await session_manager.create_session(str(user_id), user_data)

async def get_current_user_session(session_id: str) -> Optional[dict]:
    """Obtener sesión actual"""
    return await session_manager.get_session(session_id)

async def end_user_session(session_id: str) -> bool:
    """Cerrar sesión"""
    return await session_manager.delete_session(session_id)

