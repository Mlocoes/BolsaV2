"""
Schemas para import/export de datos
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as DateType


class ImportStats(BaseModel):
    """Estadísticas de importación"""
    total: int = Field(..., description="Total de registros procesados")
    created: int = Field(..., description="Registros creados")
    updated: int = Field(0, description="Registros actualizados")
    skipped: int = Field(0, description="Registros omitidos (duplicados)")
    assets_created: int = Field(0, description="Activos nuevos creados automáticamente")
    errors: List[str] = Field(default_factory=list, description="Lista de errores")


class ExportFormat(BaseModel):
    """Formato de exportación"""
    format: str = Field(..., pattern="^(csv|xlsx)$", description="Formato: csv o xlsx")


class ExportQuotesRequest(BaseModel):
    """Request para exportar cotizaciones"""
    symbol: Optional[str] = Field(None, description="Filtrar por símbolo")
    start_date: Optional[DateType] = Field(None, description="Fecha de inicio")
    end_date: Optional[DateType] = Field(None, description="Fecha de fin")
    format: str = Field("csv", pattern="^(csv|xlsx)$", description="Formato: csv o xlsx")
