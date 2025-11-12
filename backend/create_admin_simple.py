import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario import Usuario

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        if admin:
            print("✓ Admin already exists")
            return
        
        # Create admin
        admin = Usuario(
            username="admin",
            email="admin@bolsav2.com",
            hashed_password=hash_password("admin123"),
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"✓ Admin created successfully with ID: {admin.id}")
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
