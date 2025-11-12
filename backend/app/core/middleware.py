"""
Middleware para gestión de sesiones HTTP
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from .session import session_manager

async def get_current_user_from_session(request: Request) -> Optional[dict]:
    """
    Obtener el usuario actual desde la sesión de la cookie o header
    
    Args:
        request: Request de FastAPI
    
    Returns:
        Datos del usuario o None
    """
    # Intentar obtener session_id desde cookie primero
    session_id = request.cookies.get("session_id")
    
    # Si no hay cookie, intentar desde header (para desarrollo cross-port)
    if not session_id:
        session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        return None
    
    # Obtener datos de la sesión desde Redis
    session_data = await session_manager.get_session(session_id)
    
    if not session_data:
        return None
    
    # Renovar el TTL de la sesión en cada request válido
    await session_manager.refresh_session(session_id)
    
    return session_data


async def require_auth(request: Request) -> dict:
    """
    Dependency para rutas que requieren autenticación
    
    Args:
        request: Request de FastAPI
    
    Returns:
        Datos del usuario
    
    Raises:
        HTTPException 401 si no está autenticado
    """
    user = await get_current_user_from_session(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Por favor inicia sesión.",
        )
    
    return user


async def optional_auth(request: Request) -> Optional[dict]:
    """
    Dependency para rutas que pueden tener usuario opcional
    
    Args:
        request: Request de FastAPI
    
    Returns:
        Datos del usuario o None
    """
    return await get_current_user_from_session(request)
