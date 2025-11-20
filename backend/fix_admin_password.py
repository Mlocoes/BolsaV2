#!/usr/bin/env python3
"""
Script para actualizar la contraseña del usuario admin
"""
import asyncio
import sys
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import bcrypt

# Agregar el directorio de la aplicación al path
sys.path.insert(0, '/app')

from app.core.config import settings
from app.models.usuario import Usuario


async def update_admin_password():
    """Actualizar la contraseña del usuario admin"""

    # Crear engine async
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Buscar usuario admin
        result = await session.execute(
            select(Usuario).where(Usuario.username == 'admin')
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print("❌ Usuario admin no encontrado")
            return

        # Generar nuevo hash con bcrypt
        password = "admin123"
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        hashed_str = hashed.decode('utf-8')

        print(f"✓ Nuevo hash generado: {hashed_str[:50]}...")

        # Actualizar contraseña
        admin.hashed_password = hashed_str
        admin.is_admin = True
        admin.is_active = True

        await session.commit()

        print(f"✅ Contraseña del usuario 'admin' actualizada correctamente")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Is Admin: True")
        print(f"   Is Active: True")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(update_admin_password())
