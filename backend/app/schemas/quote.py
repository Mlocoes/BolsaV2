"""
Schemas para cotizaciones históricas
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import date as DateType, datetime
from typing import Optional, List
from uuid import UUID


class QuoteBase(BaseModel):
    """Schema base para Quote"""
    symbol: str = Field(..., max_length=20, description="Símbolo del activo")
    date: DateType = Field(..., description="Fecha de la cotización")
    open: float = Field(..., gt=0, description="Precio de apertura")
    high: float = Field(..., gt=0, description="Precio máximo")
    low: float = Field(..., gt=0, description="Precio mínimo")
    close: float = Field(..., gt=0, description="Precio de cierre")
    volume: Optional[int] = Field(None, ge=0, description="Volumen negociado")
    source: Optional[str] = Field(None, max_length=50, description="Fuente de datos")


class QuoteCreate(BaseModel):
    """Schema para crear una cotización"""
    symbol: str = Field(..., max_length=20)
    date: DateType
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)


class QuoteUpdate(BaseModel):
    """Schema para actualizar una cotización"""
    open: Optional[float] = Field(None, gt=0)
    high: Optional[float] = Field(None, gt=0)
    low: Optional[float] = Field(None, gt=0)
    close: Optional[float] = Field(None, gt=0)
    volume: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)


class QuoteResponse(BaseModel):
    """Schema de respuesta para Quote"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    symbol: str
    date: DateType
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int]
    source: Optional[str]
    created_at: datetime
    updated_at: datetime


class QuoteBulkCreate(BaseModel):
    """Schema para importación masiva de cotizaciones"""
    quotes: List[QuoteCreate] = Field(..., min_length=1, description="Lista de cotizaciones a importar")
    skip_duplicates: bool = Field(True, description="Si True, ignora duplicados. Si False, lanza error.")


class QuoteBulkResponse(BaseModel):
    """Schema de respuesta para importación masiva"""
    total: int = Field(..., description="Total de cotizaciones en la solicitud")
    created: int = Field(..., description="Cotizaciones creadas")
    updated: int = Field(..., description="Cotizaciones actualizadas")
    skipped: int = Field(..., description="Cotizaciones omitidas (duplicados)")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")


class QuoteHistoricalRequest(BaseModel):
    """Schema para solicitar datos históricos"""
    symbol: str = Field(..., max_length=20)
    start_date: DateType
    end_date: DateType
    source: Optional[str] = Field("finnhub", description="Fuente de datos")
