"""
Schemas para cotizaciones históricas
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date as DateType, datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal


class QuoteBase(BaseModel):
    """Schema base para Quote"""
    asset_id: Optional[UUID] = Field(None, description="ID del activo")
    symbol: Optional[str] = Field(None, max_length=20, description="Símbolo del activo (opcional si se provee asset_id)")
    timestamp: datetime = Field(..., description="Fecha y hora de la cotización")
    open: Decimal = Field(..., gt=0, description="Precio de apertura")
    high: Decimal = Field(..., gt=0, description="Precio máximo")
    low: Decimal = Field(..., gt=0, description="Precio mínimo")
    close: Decimal = Field(..., gt=0, description="Precio de cierre")
    volume: Optional[int] = Field(None, ge=0, description="Volumen negociado")
    source: Optional[str] = Field(None, max_length=50, description="Fuente de datos")


class QuoteCreate(BaseModel):
    """Schema para crear una cotización"""
    asset_id: Optional[UUID] = None
    symbol: Optional[str] = Field(None, max_length=20)
    timestamp: datetime
    open: Decimal = Field(..., gt=0)
    high: Decimal = Field(..., gt=0)
    low: Decimal = Field(..., gt=0)
    close: Decimal = Field(..., gt=0)
    volume: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol_or_id(cls, v, info):
        if not v and not info.data.get('asset_id'):
            raise ValueError('Debe proporcionar symbol o asset_id')
        return v


class QuoteUpdate(BaseModel):
    """Schema para actualizar una cotización"""
    open: Optional[Decimal] = Field(None, gt=0)
    high: Optional[Decimal] = Field(None, gt=0)
    low: Optional[Decimal] = Field(None, gt=0)
    close: Optional[Decimal] = Field(None, gt=0)
    volume: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)


class QuoteResponse(BaseModel):
    """Schema de respuesta para Quote"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    asset_id: UUID
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
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
