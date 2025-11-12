"""
Schemas para cotizaciones históricas
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from uuid import UUID


class QuoteBase(BaseModel):
    """Schema base para Quote"""
    symbol: str = Field(..., max_length=20, description="Símbolo del activo")
    date: date = Field(..., description="Fecha de la cotización")
    open: float = Field(..., gt=0, description="Precio de apertura")
    high: float = Field(..., gt=0, description="Precio máximo")
    low: float = Field(..., gt=0, description="Precio mínimo")
    close: float = Field(..., gt=0, description="Precio de cierre")
    volume: Optional[int] = Field(None, ge=0, description="Volumen negociado")
    source: Optional[str] = Field(None, max_length=50, description="Fuente de datos")


class QuoteCreate(QuoteBase):
    """Schema para crear una cotización"""
    pass


class QuoteUpdate(BaseModel):
    """Schema para actualizar una cotización"""
    open: Optional[float] = Field(None, gt=0)
    high: Optional[float] = Field(None, gt=0)
    low: Optional[float] = Field(None, gt=0)
    close: Optional[float] = Field(None, gt=0)
    volume: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)


class QuoteResponse(QuoteBase):
    """Schema de respuesta para Quote"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuoteBulkCreate(BaseModel):
    """Schema para importación masiva de cotizaciones"""
    quotes: list[QuoteCreate] = Field(..., min_length=1, description="Lista de cotizaciones a importar")
    skip_duplicates: bool = Field(True, description="Si True, ignora duplicados. Si False, lanza error.")


class QuoteBulkResponse(BaseModel):
    """Schema de respuesta para importación masiva"""
    total: int = Field(..., description="Total de cotizaciones en la solicitud")
    created: int = Field(..., description="Cotizaciones creadas")
    updated: int = Field(..., description="Cotizaciones actualizadas")
    skipped: int = Field(..., description="Cotizaciones omitidas (duplicados)")
    errors: list[str] = Field(default_factory=list, description="Errores encontrados")


class QuoteHistoricalRequest(BaseModel):
    """Schema para solicitar datos históricos"""
    symbol: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    source: Optional[str] = Field("finnhub", description="Fuente de datos")
