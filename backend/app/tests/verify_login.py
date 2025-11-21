import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.core.auth import verify_password, get_password_hash

def verify_login(username, password):
    print(f"Verifying login for user: {username}")
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user:
            print(f"❌ User '{username}' NOT FOUND.")
            # Create it for convenience
            print(f"Creating user '{username}' with password '{password}'...")
            new_user = Usuario(
                username=username,
                email=f"{username}@example.com",
                hashed_password=get_password_hash(password),
                is_active=True,
                is_admin=True
            )
            db.add(new_user)
            db.commit()
            print("✅ User created.")
            return

        print(f"User found. ID: {user.id}")
        print(f"Stored Hash: {user.hashed_password}")
        
        if verify_password(password, user.hashed_password):
            print("✅ Password verification SUCCESS.")
        else:
            print("❌ Password verification FAILED.")
            print(f"Updating password to '{password}'...")
            user.hashed_password = get_password_hash(password)
            db.commit()
            print("✅ Password updated.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_login("admin", "admin123")
