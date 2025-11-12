"""
Rutas para importación y exportación de datos
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date as DateType
from uuid import UUID
import io

from app.core.database import get_db
from app.core.middleware import require_auth
from app.services.import_export_service import ImportExportService
from app.schemas.import_export import ImportStats, ExportQuotesRequest

router = APIRouter(prefix="/api/import-export", tags=["import-export"])


# ==================== EXPORTACIÓN ====================

@router.get("/transactions/{portfolio_id}/export")
async def export_transactions(
    portfolio_id: UUID,
    format: str = Query("csv", pattern="^(csv|xlsx)$", description="Formato: csv o xlsx"),
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Exportar transacciones de un portfolio
    
    Args:
        portfolio_id: ID del portfolio
        format: Formato de exportación (csv o xlsx)
    
    Returns:
        Archivo CSV o XLSX con las transacciones
    """
    service = ImportExportService(db)
    
    try:
        if format == "csv":
            content = service.export_transactions_csv(portfolio_id)
            return Response(
                content=content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=transactions_{portfolio_id}.csv"
                }
            )
        else:  # xlsx
            content = service.export_transactions_xlsx(portfolio_id)
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=transactions_{portfolio_id}.xlsx"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar transacciones: {str(e)}"
        )


@router.get("/quotes/export")
async def export_quotes(
    symbol: Optional[str] = Query(None, description="Filtrar por símbolo"),
    start_date: Optional[DateType] = Query(None, description="Fecha de inicio"),
    end_date: Optional[DateType] = Query(None, description="Fecha de fin"),
    format: str = Query("csv", pattern="^(csv|xlsx)$", description="Formato: csv o xlsx"),
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Exportar cotizaciones históricas
    
    Args:
        symbol: Filtrar por símbolo (opcional)
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        format: Formato de exportación (csv o xlsx)
    
    Returns:
        Archivo CSV o XLSX con las cotizaciones
    """
    service = ImportExportService(db)
    
    try:
        if format == "csv":
            content = service.export_quotes_csv(symbol, start_date, end_date)
            filename = f"quotes_{symbol if symbol else 'all'}.csv"
            return Response(
                content=content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        else:  # xlsx
            content = service.export_quotes_xlsx(symbol, start_date, end_date)
            filename = f"quotes_{symbol if symbol else 'all'}.xlsx"
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar cotizaciones: {str(e)}"
        )


# ==================== IMPORTACIÓN ====================

@router.post("/transactions/{portfolio_id}/import", response_model=ImportStats)
async def import_transactions(
    portfolio_id: UUID,
    file: UploadFile = File(..., description="Archivo CSV con transacciones"),
    skip_duplicates: bool = Query(True, description="Omitir duplicados"),
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Importar transacciones desde archivo CSV
    
    Formato CSV esperado:
    ```
    date,type,asset_symbol,quantity,price,fees,notes
    2025-01-15,BUY,AAPL,10,150.50,9.99,Initial purchase
    ```
    
    Columnas requeridas: date, type, asset_symbol, quantity, price
    Columnas opcionales: fees, notes
    
    Args:
        portfolio_id: ID del portfolio destino
        file: Archivo CSV
        skip_duplicates: Si True, ignora transacciones duplicadas
    
    Returns:
        Estadísticas de importación
    """
    # Validar tipo de archivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos CSV"
        )
    
    try:
        # Leer contenido
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Importar
        service = ImportExportService(db)
        stats = service.import_transactions_csv(portfolio_id, csv_content, skip_duplicates)
        
        return stats
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al importar transacciones: {str(e)}"
        )


@router.post("/quotes/import", response_model=ImportStats)
async def import_quotes(
    file: UploadFile = File(..., description="Archivo CSV con cotizaciones"),
    skip_duplicates: bool = Query(True, description="Omitir duplicados"),
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Importar cotizaciones desde archivo CSV
    
    Formato CSV esperado:
    ```
    symbol,date,open,high,low,close,volume,source
    AAPL,2025-01-15,150.00,152.00,149.50,151.50,1000000,manual
    ```
    
    Columnas requeridas: symbol, date, open, high, low, close
    Columnas opcionales: volume, source
    
    Args:
        file: Archivo CSV
        skip_duplicates: Si True, ignora duplicados. Si False, actualiza existentes.
    
    Returns:
        Estadísticas de importación
    """
    # Validar tipo de archivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos CSV"
        )
    
    try:
        # Leer contenido
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Importar
        service = ImportExportService(db)
        stats = service.import_quotes_csv(csv_content, skip_duplicates)
        
        return stats
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al importar cotizaciones: {str(e)}"
        )


@router.get("/templates/transactions")
async def download_transactions_template(
    user: dict = Depends(require_auth)
):
    """
    Descargar plantilla CSV para importar transacciones
    
    Returns:
        Archivo CSV de ejemplo
    """
    template = """date,type,asset_symbol,quantity,price,fees,notes
2025-01-15,BUY,AAPL,10,150.50,9.99,Initial purchase
2025-02-20,SELL,AAPL,5,155.00,9.99,Partial sale
2025-03-10,BUY,TSLA,20,200.00,19.99,Tesla investment"""
    
    return Response(
        content=template,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=transactions_template.csv"
        }
    )


@router.get("/templates/quotes")
async def download_quotes_template(
    user: dict = Depends(require_auth)
):
    """
    Descargar plantilla CSV para importar cotizaciones
    
    Returns:
        Archivo CSV de ejemplo
    """
    template = """symbol,date,open,high,low,close,volume,source
AAPL,2025-01-15,150.00,152.00,149.50,151.50,1000000,manual
TSLA,2025-01-15,200.00,205.00,198.00,203.00,500000,manual
MSFT,2025-01-15,300.00,305.00,299.00,304.00,800000,manual"""
    
    return Response(
        content=template,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=quotes_template.csv"
        }
    )
