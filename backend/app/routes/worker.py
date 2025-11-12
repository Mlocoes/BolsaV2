"""
Rutas para gestión de workers y tareas de Celery
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.middleware import require_auth
from app.services.celery_app import celery_app
from app.services.celery_tasks import (
    update_all_asset_prices,
    update_single_asset_price,
    import_historical_quotes
)

router = APIRouter(prefix="/api/worker", tags=["worker"])


class TaskResponse(BaseModel):
    """Schema de respuesta para tareas"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Schema de respuesta para estado de tarea"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


class WorkerHealthResponse(BaseModel):
    """Schema de respuesta para health check"""
    status: str
    workers_available: int
    active_tasks: int
    scheduled_tasks: int
    timestamp: datetime


class TriggerPriceUpdateRequest(BaseModel):
    """Schema para trigger manual de actualización de precios"""
    symbol: Optional[str] = None  # Si es None, actualiza todos


class ImportHistoricalRequest(BaseModel):
    """Schema para trigger de importación histórica"""
    symbol: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD


@router.get("/health", response_model=WorkerHealthResponse)
async def worker_health():
    """
    Health check del worker de Celery
    No requiere autenticación (útil para monitoring)
    """
    try:
        # Inspeccionar workers activos
        inspect = celery_app.control.inspect()
        
        active_workers = inspect.active()
        scheduled = inspect.scheduled()
        
        workers_count = len(active_workers) if active_workers else 0
        
        # Contar tareas activas
        active_count = 0
        if active_workers:
            for worker_tasks in active_workers.values():
                active_count += len(worker_tasks)
        
        # Contar tareas programadas
        scheduled_count = 0
        if scheduled:
            for worker_tasks in scheduled.values():
                scheduled_count += len(worker_tasks)
        
        return WorkerHealthResponse(
            status="healthy" if workers_count > 0 else "no_workers",
            workers_available=workers_count,
            active_tasks=active_count,
            scheduled_tasks=scheduled_count,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Worker no disponible: {str(e)}"
        )


@router.get("/stats")
async def worker_stats(user: dict = Depends(require_auth)):
    """
    Estadísticas detalladas del worker
    Requiere autenticación
    """
    try:
        inspect = celery_app.control.inspect()
        
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()
        
        return {
            "stats": stats,
            "active_tasks": active,
            "scheduled_tasks": scheduled,
            "reserved_tasks": reserved,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.post("/trigger/prices", response_model=TaskResponse)
async def trigger_price_update(
    request: TriggerPriceUpdateRequest,
    user: dict = Depends(require_auth)
):
    """
    Trigger manual de actualización de precios
    Requiere autenticación
    """
    try:
        if request.symbol:
            # Actualizar un solo asset
            task = update_single_asset_price.delay(request.symbol)
            message = f"Actualización de precio iniciada para {request.symbol}"
        else:
            # Actualizar todos los assets
            task = update_all_asset_prices.delay()
            message = "Actualización masiva de precios iniciada"
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar tarea: {str(e)}"
        )


@router.post("/trigger/import-historical", response_model=TaskResponse)
async def trigger_import_historical(
    request: ImportHistoricalRequest,
    user: dict = Depends(require_auth)
):
    """
    Trigger manual de importación histórica
    Requiere autenticación
    """
    try:
        task = import_historical_quotes.delay(
            request.symbol,
            request.start_date,
            request.end_date
        )
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Importación histórica iniciada para {request.symbol}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar importación: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    user: dict = Depends(require_auth)
):
    """
    Obtener el estado de una tarea
    Requiere autenticación
    """
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
            result=task_result.result if task_result.successful() else None,
            error=str(task_result.info) if task_result.failed() else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado de tarea: {str(e)}"
        )


@router.post("/task/{task_id}/revoke")
async def revoke_task(
    task_id: str,
    user: dict = Depends(require_auth)
):
    """
    Cancelar una tarea pendiente
    Requiere autenticación
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "message": f"Tarea {task_id} cancelada",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar tarea: {str(e)}"
        )
