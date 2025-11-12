#!/usr/bin/env python3
"""
Script para administrar usuarios del sistema BolsaV2
"""
import sys
from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.core.auth import get_password_hash


def make_admin(username: str):
    """Hacer a un usuario administrador"""
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return False
        
        user.is_admin = True
        db.commit()
        print(f"✅ Usuario '{username}' ahora es administrador")
        return True
    finally:
        db.close()


def remove_admin(username: str):
    """Quitar privilegios de administrador"""
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return False
        
        user.is_admin = False
        db.commit()
        print(f"✅ Privilegios de administrador removidos de '{username}'")
        return True
    finally:
        db.close()


def list_users():
    """Listar todos los usuarios"""
    db = SessionLocal()
    try:
        users = db.query(Usuario).all()
        print(f"\n{'Username':<20} {'Email':<30} {'Admin':<10} {'Activo':<10}")
        print("-" * 70)
        for user in users:
            admin_status = "✓" if user.is_admin else ""
            active_status = "✓" if user.is_active else "✗"
            print(f"{user.username:<20} {user.email:<30} {admin_status:<10} {active_status:<10}")
        print(f"\nTotal: {len(users)} usuarios\n")
    finally:
        db.close()


def create_user(username: str, email: str, password: str, is_admin: bool = False):
    """Crear un nuevo usuario"""
    db = SessionLocal()
    try:
        # Verificar si ya existe
        existing = db.query(Usuario).filter(
            (Usuario.username == username) | (Usuario.email == email)
        ).first()
        
        if existing:
            print(f"❌ Usuario con ese username o email ya existe")
            return False
        
        # Crear nuevo usuario
        new_user = Usuario(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_admin=is_admin,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        
        admin_text = " (admin)" if is_admin else ""
        print(f"✅ Usuario '{username}' creado exitosamente{admin_text}")
        return True
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("""
Uso:
    python manage_users.py list                           - Listar todos los usuarios
    python manage_users.py make-admin <username>          - Hacer administrador
    python manage_users.py remove-admin <username>        - Quitar permisos admin
    python manage_users.py create <username> <email> <password> [--admin]  - Crear usuario
        """)
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_users()
    
    elif command == "make-admin":
        if len(sys.argv) < 3:
            print("❌ Falta el username")
            return
        make_admin(sys.argv[2])
    
    elif command == "remove-admin":
        if len(sys.argv) < 3:
            print("❌ Falta el username")
            return
        remove_admin(sys.argv[2])
    
    elif command == "create":
        if len(sys.argv) < 5:
            print("❌ Faltan argumentos: username email password")
            return
        
        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        is_admin = "--admin" in sys.argv
        
        create_user(username, email, password, is_admin)
    
    else:
        print(f"❌ Comando desconocido: {command}")


if __name__ == "__main__":
    main()
