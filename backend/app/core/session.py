"""
Sistema de sesiones con Redis
Reemplaza JWT con sesiones efímeras seguras
"""
import uuid
import json
from typing import Optional, Dict, Any
from datetime import timedelta
import redis.asyncio as redis
from .config import settings

class SessionManager:
    """Gestor de sesiones con Redis"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.session_ttl = timedelta(hours=24)  # 24 horas por defecto
        self.prefix = "session:"
    
    async def connect(self):
        """Conectar a Redis"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def disconnect(self):
        """Desconectar de Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def create_session(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """
        Crear una nueva sesión
        
        Args:
            user_id: UUID del usuario
            user_data: Datos adicionales del usuario (username, email, etc)
        
        Returns:
            session_id: ID único de la sesión
        """
        await self.connect()
        
        # Generar un session_id único
        session_id = str(uuid.uuid4())
        
        # Preparar datos de la sesión
        session_data = {
            "user_id": user_id,
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "is_active": user_data.get("is_active", True),
            "created_at": user_data.get("created_at"),
        }
        
        # Guardar en Redis con TTL
        key = f"{self.prefix}{session_id}"
        await self.redis_client.setex(
            key,
            self.session_ttl,
            json.dumps(session_data)
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos de una sesión
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            session_data o None si no existe
        """
        await self.connect()
        
        key = f"{self.prefix}{session_id}"
        data = await self.redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def refresh_session(self, session_id: str) -> bool:
        """
        Renovar el TTL de una sesión existente
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            True si se renovó, False si no existe
        """
        await self.connect()
        
        key = f"{self.prefix}{session_id}"
        # Renovar TTL
        result = await self.redis_client.expire(key, self.session_ttl)
        return result == 1
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Eliminar una sesión (logout)
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            True si se eliminó, False si no existía
        """
        await self.connect()
        
        key = f"{self.prefix}{session_id}"
        result = await self.redis_client.delete(key)
        return result > 0
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Eliminar todas las sesiones de un usuario
        
        Args:
            user_id: UUID del usuario
        
        Returns:
            Número de sesiones eliminadas
        """
        await self.connect()
        
        # Buscar todas las sesiones del usuario
        pattern = f"{self.prefix}*"
        deleted_count = 0
        
        async for key in self.redis_client.scan_iter(match=pattern):
            data = await self.redis_client.get(key)
            if data:
                session_data = json.loads(data)
                if session_data.get("user_id") == user_id:
                    await self.redis_client.delete(key)
                    deleted_count += 1
        
        return deleted_count


# Instancia global del gestor de sesiones
session_manager = SessionManager()
