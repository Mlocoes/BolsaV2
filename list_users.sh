#!/bin/bash
# Script wrapper para ejecutar manage_users.py dentro del contenedor de backend

docker-compose -f /home/mloco/Escritorio/BolsaV2/docker-compose.yml exec backend python -c "
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.usuario import Usuario

db = SessionLocal()
try:
    users = db.query(Usuario).all()
    print(f\"\\n{'Username':<20} {'Email':<30} {'Admin':<10} {'Activo':<10}\")
    print('-' * 70)
    for user in users:
        admin_status = '✓' if user.is_admin else ''
        active_status = '✓' if user.is_active else '✗'
        print(f\"{user.username:<20} {user.email:<30} {admin_status:<10} {active_status:<10}\")
    print(f\"\\nTotal: {len(users)} usuarios\\n\")
finally:
    db.close()
"
