"""
Entry point for Celery worker
"""
from app.services.celery_app import celery_app

# Hacer disponible la app para Celery CLI
app = celery_app

if __name__ == "__main__":
    app.start()
