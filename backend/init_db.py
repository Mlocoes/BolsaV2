"""
Script para inicializar la base de datos con las tablas y el usuario admin
"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base, SessionLocal
from app.models.usuario import Usuario
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.position import Position
from app.models.transaction import Transaction
from app.core.auth import get_password_hash

def init_db():
    """Crear las tablas en la base de datos"""
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas")
    
    # Crear usuario admin si no existe
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        if not admin:
            print("Creando usuario admin...")
            # La contraseña no debe ser muy larga para bcrypt (máx 72 bytes)
            password = "admin123"
            admin = Usuario(
                username="admin",
                email="admin@bolsav2.com",
                hashed_password=get_password_hash(password),
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("✓ Usuario admin creado")
            print(f"  Username: admin")
            print(f"  Password: {password}")
        else:
            print("✓ Usuario admin ya existe")
    except Exception as e:
        print(f"Error al crear usuario admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
