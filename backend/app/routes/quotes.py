"""
Rutas para gestión de cotizaciones históricas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

from app.core.database import get_db
from app.core.middleware import require_auth
from app.services.quote_service import QuoteService
from app.schemas.quote import (
    QuoteCreate,
    QuoteResponse,
    QuoteBulkCreate,
    QuoteBulkResponse,
    QuoteHistoricalRequest
)

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


@router.get("", response_model=List[QuoteResponse])
async def get_quotes(
    symbol: Optional[str] = Query(None, description="Filtrar por símbolo"),
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Obtener cotizaciones con filtros opcionales
    
    Requiere autenticación.
    """
    service = QuoteService(db)
    quotes = service.get_quotes(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return quotes


@router.get("/latest/{symbol}", response_model=QuoteResponse)
async def get_latest_quote(
    symbol: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Obtener la cotización más reciente de un símbolo
    
    Requiere autenticación.
    """
    service = QuoteService(db)
    quote = service.get_latest_quote(symbol)
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron cotizaciones para {symbol}"
        )
    
    return quote


@router.get("/{symbol}/{quote_date}", response_model=QuoteResponse)
async def get_quote_by_date(
    symbol: str,
    quote_date: date,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Obtener una cotización específica por símbolo y fecha
    
    Requiere autenticación.
    """
    service = QuoteService(db)
    quote = service.get_quote_by_symbol_date(symbol, quote_date)
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró cotización para {symbol} en {quote_date}"
        )
    
    return quote


@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Crear una cotización manualmente
    
    Requiere autenticación.
    Lanza error 409 si ya existe una cotización para ese símbolo y fecha.
    """
    service = QuoteService(db)
    
    # Verificar si ya existe
    existing = service.get_quote_by_symbol_date(quote_data.symbol, quote_data.date)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una cotización para {quote_data.symbol} en {quote_data.date}"
        )
    
    try:
        quote = service.create_quote(quote_data)
        return quote
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear cotización: {str(e)}"
        )


@router.post("/bulk", response_model=QuoteBulkResponse)
async def bulk_import_quotes(
    bulk_data: QuoteBulkCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Importar cotizaciones en masa
    
    Requiere autenticación.
    Permite manejar duplicados (actualizar o omitir según skip_duplicates).
    """
    service = QuoteService(db)
    result = service.bulk_import_quotes(bulk_data)
    return result


@router.post("/import-historical", response_model=QuoteBulkResponse)
async def import_historical(
    request: QuoteHistoricalRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Importar datos históricos desde Finnhub
    
    Requiere autenticación.
    Obtiene datos OHLCV desde Finnhub para el rango de fechas especificado.
    """
    service = QuoteService(db)
    
    # Validar rango de fechas (máximo 1 año)
    date_diff = (request.end_date - request.start_date).days
    if date_diff > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rango de fechas no puede ser mayor a 1 año"
        )
    
    if date_diff < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    result = service.import_historical_from_finnhub(
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    return result


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Eliminar una cotización
    
    Requiere autenticación.
    """
    from app.models.quote import Quote
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada"
        )
    
    db.delete(quote)
    db.commit()
    
    return {"message": "Cotización eliminada exitosamente"}


# ============================================
# Nuevos Endpoints: Importación Inteligente y Actualización Automática
# ============================================

@router.post("/import-historical-smart", response_model=QuoteBulkResponse)
async def import_historical_smart(
    symbol: str = Query(..., description="Símbolo del activo"),
    start_date: date = Query(..., description="Fecha de inicio"),
    end_date: date = Query(..., description="Fecha de fin"),
    force_refresh: bool = Query(False, description="Re-importar datos existentes"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Importar datos históricos de forma inteligente
    
    Solo importa rangos de fechas faltantes (gaps).
    Con force_refresh=True, re-importa todos los datos.
    
    Máximo permitido: 2 años por solicitud.
    """
    # Validar rango máximo
    date_diff = (end_date - start_date).days
    max_days = 730  # 2 años
    
    if date_diff > max_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rango máximo permitido: {max_days} días (2 años)"
        )
    
    if date_diff < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la de inicio"
        )
    
    service = QuoteService(db)
    result = service.import_historical_smart(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh
    )
    
    # Log del resultado para debug
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Import result for {symbol}: created={result.created}, updated={result.updated}, skipped={result.skipped}, errors={result.errors}, message={getattr(result, 'message', None)}")
    
    return result


@router.get("/coverage/{symbol}")
async def get_quote_coverage(
    symbol: str,
    start_date: date = Query(..., description="Fecha de inicio"),
    end_date: date = Query(..., description="Fecha de fin"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Obtener cobertura de datos para un símbolo
    
    Retorna información sobre qué fechas tienen datos y cuáles faltan.
    """
    service = QuoteService(db)
    
    total_days = (end_date - start_date).days + 1
    missing_ranges = service.get_missing_date_ranges(symbol, start_date, end_date)
    
    missing_days = sum((r[1] - r[0]).days + 1 for r in missing_ranges)
    coverage_percent = ((total_days - missing_days) / total_days) * 100 if total_days > 0 else 0
    
    return {
        "symbol": symbol.upper(),
        "total_days": total_days,
        "missing_days": missing_days,
        "coverage_percent": round(coverage_percent, 2),
        "missing_ranges": [
            {
                "start": r[0].isoformat(),
                "end": r[1].isoformat(),
                "days": (r[1] - r[0]).days + 1
            }
            for r in missing_ranges
        ]
    }


@router.post("/update-latest/{symbol}")
async def update_latest_quote(
    symbol: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Actualizar con la última cotización en tiempo real
    
    Obtiene el precio actual desde Finnhub y lo guarda/actualiza.
    """
    service = QuoteService(db)
    result = service.update_latest_quote_realtime(symbol)
    
    if not result or not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Error al actualizar cotización") if result else "Sin respuesta"
        )
    
    return result


@router.post("/update-all-latest")
async def update_all_latest_quotes(
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Actualizar cotizaciones de todos los activos
    
    Obtiene precios actuales de todos los activos desde Finnhub.
    Respeta rate limits con delays automáticos.
    
    ADVERTENCIA: Puede tardar varios minutos con muchos activos.
    """
    from app.models.asset import Asset
    import asyncio
    
    # Obtener todos los activos
    assets = db.query(Asset).all()
    
    if not assets:
        return {
            "success": True,
            "message": "No hay activos para actualizar",
            "updated": 0,
            "failed": 0
        }
    
    service = QuoteService(db)
    updated = 0
    failed = 0
    errors = []
    
    for asset in assets:
        result = service.update_latest_quote_realtime(asset.symbol)
        
        if result and result.get("success"):
            updated += 1
        else:
            failed += 1
            errors.append({
                "symbol": asset.symbol,
                "error": result.get("error", "Unknown error") if result else "No response"
            })
        
        # Delay para respetar rate limits
        await asyncio.sleep(1.1)
    
    return {
        "success": True,
        "total_assets": len(assets),
        "updated": updated,
        "failed": failed,
        "errors": errors[:10],  # Solo primeros 10 errores
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# Scheduler Control Endpoints (Admin only)
# ============================================

@router.get("/scheduler/status")
async def get_scheduler_status(
    user: dict = Depends(require_auth)
):
    """
    Obtener estado del scheduler de actualización automática
    
    Muestra si está activo, intervalo configurado y próxima ejecución.
    """
    from app.services.quote_scheduler import quote_scheduler
    return quote_scheduler.get_status()


@router.post("/scheduler/trigger")
async def trigger_scheduler_now(
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Ejecutar actualización manual inmediata
    
    Dispara una actualización de todas las cotizaciones sin esperar al intervalo programado.
    """
    from app.services.quote_scheduler import quote_scheduler
    await quote_scheduler.trigger_update_now()
    
    return {
        "success": True,
        "message": "Actualización manual ejecutada",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.put("/scheduler/configure")
async def configure_scheduler(
    update_interval_minutes: int = Query(..., ge=5, le=1440, description="Intervalo en minutos (5-1440)"),
    user: dict = Depends(require_auth)
):
    """
    Configurar intervalo de actualización automática
    
    Cambia el intervalo entre actualizaciones automáticas.
    Rango: 5 minutos (mínimo) a 1440 minutos (24 horas).
    """
    from app.services.quote_scheduler import quote_scheduler
    quote_scheduler.configure(update_interval_minutes)
    
    return {
        "success": True,
        "message": f"Intervalo actualizado a {update_interval_minutes} minutos",
        "new_interval": update_interval_minutes
    }
