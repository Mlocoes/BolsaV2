import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import hash_password
from app.models.usuario import Usuario

async def create_admin():
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario).where(Usuario.username == "admin"))
        if result.scalar_one_or_none():
            print("Admin already exists")
            return
        
        admin = Usuario(
            username="admin",
            email="admin@bolsav2.com",
            password_hash=hash_password("admin123"),
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print("Admin created successfully")

if __name__ == "__main__":
    asyncio.run(create_admin())
