import asyncio
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.security import hash_password
from app.models.usuario import Usuario
import logging

logger = logging.getLogger(__name__)

def create_admin():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)
    
    with SessionLocal() as session:
        result = session.execute(select(Usuario).where(Usuario.username == "admin"))
        if result.scalar_one_or_none():
            logger.info("Admin already exists")
            return
        
        admin = Usuario(
            username="admin",
            email="admin@bolsav2.com",
            password_hash=hash_password("admin123"),
            is_active=True
        )
        session.add(admin)
        session.commit()
        logger.info("Admin created successfully")

if __name__ == "__main__":
    create_admin()
