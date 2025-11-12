"""
Configuración de Celery para tareas asíncronas
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "bolsav2",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.celery_tasks"]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configuración de tareas periódicas (beat schedule)
celery_app.conf.beat_schedule = {
    "update-asset-prices-every-15-minutes": {
        "task": "app.services.celery_tasks.update_all_asset_prices",
        "schedule": crontab(minute="*/15"),  # Cada 15 minutos
        "options": {"expires": 600}  # La tarea expira en 10 minutos si no se ejecuta
    },
    "cleanup-old-sessions-daily": {
        "task": "app.services.celery_tasks.cleanup_expired_sessions",
        "schedule": crontab(hour=3, minute=0),  # Diariamente a las 3 AM
        "options": {"expires": 3600}
    },
}

# Configuración de rutas (queues)
celery_app.conf.task_routes = {
    "app.services.celery_tasks.update_all_asset_prices": {"queue": "prices"},
    "app.services.celery_tasks.update_single_asset_price": {"queue": "prices"},
    "app.services.celery_tasks.cleanup_expired_sessions": {"queue": "maintenance"},
}
