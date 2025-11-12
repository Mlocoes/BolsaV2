"""
Script para recrear la base de datos con UUIDs
ADVERTENCIA: Este script elimina todos los datos existentes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models import usuario, portfolio, asset, position, transaction, quote

def recreate_database():
    print("⚠️  ADVERTENCIA: Esta operación eliminará todos los datos existentes")
    print("¿Estás seguro de que deseas continuar? (yes/no)")
    
    # En un script automatizado, puedes comentar esta verificación
    response = input().lower()
    if response != 'yes':
        print("Operación cancelada")
        return
    
    print("\n1. Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Tablas eliminadas")
    
    print("\n2. Creando tablas con UUIDs...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas")
    
    print("\n✅ Base de datos recreada exitosamente con UUIDs")
    print("\nPróximos pasos:")
    print("1. Ejecutar create_admin.py para crear usuario administrador")
    print("2. Ejecutar seed_assets.py para poblar activos de ejemplo")

if __name__ == "__main__":
    recreate_database()
