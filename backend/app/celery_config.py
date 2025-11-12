"""
Entry point for Celery CLI
Import from this module: celery -A app.celery_config
"""
from app.services.celery_app import celery_app as app

__all__ = ['app']
