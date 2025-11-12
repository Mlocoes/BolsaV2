"""
Script para agregar la tabla quotes a la base de datos existente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.quote import Quote

def add_quotes_table():
    """Crear solo la tabla quotes"""
    print("Creando tabla quotes...")
    
    try:
        Quote.__table__.create(engine, checkfirst=True)
        print("✓ Tabla quotes creada exitosamente")
        print(f"  - Columnas: id, symbol, date, open, high, low, close, volume, source, created_at, updated_at")
        print(f"  - Constraint: uq_quote_symbol_date (symbol, date)")
        print(f"  - Índices: idx_quote_symbol_date, idx_quote_date")
    except Exception as e:
        print(f"✗ Error al crear tabla: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_quotes_table()
    if success:
        print("\n✅ Tabla quotes lista para usar")
        print("\nPróximos pasos:")
        print("1. Usar POST /api/quotes/import-historical para importar datos desde Finnhub")
        print("2. Usar POST /api/quotes/bulk para importar datos en masa")
        print("3. Usar GET /api/quotes para consultar cotizaciones")
    else:
        sys.exit(1)
