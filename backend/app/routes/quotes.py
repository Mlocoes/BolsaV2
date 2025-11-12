"""
Rutas para gestión de cotizaciones históricas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
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


@router.get("/", response_model=list[QuoteResponse])
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


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
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
