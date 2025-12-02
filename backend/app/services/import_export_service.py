"""
Servicio para importación y exportación de datos (CSV/XLSX)
"""
import io
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date as DateType
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID

from app.models.transaction import Transaction
from app.models.quote import Quote
from app.models.portfolio import Portfolio
from app.models.asset import Asset


class ImportExportService:
    """Servicio para import/export de transacciones y cotizaciones"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== EXPORTACIÓN ====================
    
    def export_transactions_csv(self, portfolio_id: UUID) -> str:
        """
        Exportar transacciones de un portfolio a CSV
        
        Args:
            portfolio_id: ID del portfolio
            
        Returns:
            String con contenido CSV
        """
        transactions = (
            self.db.query(Transaction)
            .join(Asset, Transaction.asset_id == Asset.id)
            .filter(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )
        
        # Convertir a diccionarios
        data = []
        for tx in transactions:
            data.append({
                'date': tx.transaction_date.strftime('%Y-%m-%d'),
                'type': tx.transaction_type,
                'asset_symbol': tx.asset.symbol,
                'quantity': tx.quantity,
                'price': tx.price,
                'fees': tx.fees or 0,
                'notes': tx.notes or ''
            })
        
        # Crear DataFrame y exportar
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    def export_transactions_xlsx(self, portfolio_id: UUID) -> bytes:
        """
        Exportar transacciones de un portfolio a XLSX
        
        Args:
            portfolio_id: ID del portfolio
            
        Returns:
            Bytes con archivo XLSX
        """
        transactions = (
            self.db.query(Transaction)
            .join(Asset, Transaction.asset_id == Asset.id)
            .filter(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )
        
        data = []
        for tx in transactions:
            data.append({
                'date': tx.transaction_date.strftime('%Y-%m-%d'),
                'type': tx.transaction_type,
                'asset_symbol': tx.asset.symbol,
                'quantity': tx.quantity,
                'price': tx.price,
                'fees': tx.fees or 0,
                'notes': tx.notes or ''
            })
        
        df = pd.DataFrame(data)
        
        # Exportar a bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
        
        return output.getvalue()
    
    def export_quotes_csv(
        self, 
        symbol: Optional[str] = None,
        start_date: Optional[DateType] = None,
        end_date: Optional[DateType] = None
    ) -> str:
        """
        Exportar cotizaciones a CSV
        
        Args:
            symbol: Filtrar por símbolo (opcional)
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)
            
        Returns:
            String con contenido CSV
        """
        query = self.db.query(Quote)
        
        if symbol:
            query = query.filter(Quote.symbol == symbol.upper())
        if start_date:
            query = query.filter(Quote.date >= start_date)
        if end_date:
            query = query.filter(Quote.date <= end_date)
        
        quotes = query.order_by(Quote.date.desc()).all()
        
        data = []
        for quote in quotes:
            data.append({
                'symbol': quote.symbol,
                'date': quote.date.strftime('%Y-%m-%d'),
                'open': quote.open,
                'high': quote.high,
                'low': quote.low,
                'close': quote.close,
                'volume': quote.volume or 0,
                'source': quote.source or 'manual'
            })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    def export_quotes_xlsx(
        self, 
        symbol: Optional[str] = None,
        start_date: Optional[DateType] = None,
        end_date: Optional[DateType] = None
    ) -> bytes:
        """
        Exportar cotizaciones a XLSX
        
        Args:
            symbol: Filtrar por símbolo (opcional)
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)
            
        Returns:
            Bytes con archivo XLSX
        """
        query = self.db.query(Quote)
        
        if symbol:
            query = query.filter(Quote.symbol == symbol.upper())
        if start_date:
            query = query.filter(Quote.date >= start_date)
        if end_date:
            query = query.filter(Quote.date <= end_date)
        
        quotes = query.order_by(Quote.date.desc()).all()
        
        data = []
        for quote in quotes:
            data.append({
                'symbol': quote.symbol,
                'date': quote.date.strftime('%Y-%m-%d'),
                'open': quote.open,
                'high': quote.high,
                'low': quote.low,
                'close': quote.close,
                'volume': quote.volume or 0,
                'source': quote.source or 'manual'
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Quotes', index=False)
        
        return output.getvalue()
    
    # ==================== IMPORTACIÓN ====================
    
    # ==================== IMPORTACIÓN ====================
    
    def _process_transactions_df(
        self,
        df: pd.DataFrame,
        portfolio_id: UUID,
        skip_duplicates: bool
    ) -> Dict[str, any]:
        """Helper para procesar DataFrame de transacciones"""
        # Normalizar columnas (strip whitespace y lower case para comparación flexible)
        df.columns = df.columns.str.strip()
        
        # Definir mapeo de columnas (Aliases)
        column_mapping = {
            'date': ['date', 'data', 'fecha'],
            'type': ['type', 'c/v', 'tipo'],
            'asset_symbol': ['asset_symbol', 'activo', 'symbol', 'simbolo'],
            'quantity': ['quantity', 'cantidad', 'cuantida', 'cuantidad', 'unidades'],
            'price': ['price', 'precio'],
            'fees': ['fees', 'fee', 'comision'],
            'notes': ['notes', 'nota', 'notas', 'comentarios']
        }
        
        # Normalizar nombres de columnas en el DataFrame
        # Crear un mapa inverso: alias -> nombre_canonico
        alias_to_canonical = {}
        for canonical, aliases in column_mapping.items():
            for alias in aliases:
                alias_to_canonical[alias.lower()] = canonical
        
        # Renombrar columnas del DF si coinciden con algún alias
        new_columns = []
        found_canonical = set()
        
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in alias_to_canonical:
                canonical = alias_to_canonical[col_lower]
                new_columns.append(canonical)
                found_canonical.add(canonical)
            else:
                new_columns.append(col)
        
        df.columns = new_columns

        # Validar columnas requeridas (Canonical names)
        required_columns = ['date', 'type', 'asset_symbol', 'quantity', 'price']
        missing_columns = [col for col in required_columns if col not in found_canonical]
        
        if missing_columns:
            found_columns = list(df.columns)
            raise ValueError(f"Columnas requeridas faltantes (o no reconocidas): {', '.join(missing_columns)}. Columnas encontradas: {', '.join(found_columns)}")
        
        # Verificar que el portfolio existe
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} no encontrado")
        
        stats = {
            'total': len(df),
            'created': 0,
            'skipped': 0,
            'assets_created': 0,  # Nuevos activos creados
            'errors': [],
            'min_date': None  # Para snapshot recalculation
        }
        
        def parse_spanish_float(val):
            if pd.isna(val):
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            val_str = str(val).strip()
            # Reemplazar punto de miles por nada y coma decimal por punto
            val_str = val_str.replace('.', '').replace(',', '.')
            return float(val_str)

        for idx, row in df.iterrows():
            try:
                # Buscar o crear asset
                asset_symbol = str(row['asset_symbol']).upper().strip()
                asset = self.db.query(Asset).filter(Asset.symbol == asset_symbol).first()
                
                if not asset:
                    # Crear asset si no existe
                    # Intentar obtener información adicional del símbolo
                    asset_name = asset_symbol
                    asset_type = 'stock'  # Default
                    
                    # Intentar detectar el tipo por el símbolo
                    if asset_symbol.endswith('.L') or asset_symbol.endswith('.LON'):
                        asset_type = 'stock'
                        asset_name = asset_symbol
                    elif asset_symbol.startswith('EUR') or asset_symbol.startswith('USD'):
                        asset_type = 'forex'
                    elif len(asset_symbol) <= 5 and asset_symbol.isalpha():
                        asset_type = 'stock'
                    
                    asset = Asset(
                        symbol=asset_symbol,
                        name=asset_name,
                        asset_type=asset_type,
                        currency='USD',  # Default currency
                        market=None
                    )
                    self.db.add(asset)
                    self.db.flush()
                    
                    # Incrementar contador de activos creados
                    stats['assets_created'] += 1
                    
                    # Log para tracking
                    print(f"✨ Activo creado automáticamente: {asset_symbol} ({asset_type})")
                
                # Parsear fecha (DD/MM/YYYY o YYYY-MM-DD)
                date_val = row['date']
                if isinstance(date_val, str):
                    # Intentar varios formatos
                    try:
                        transaction_date = datetime.strptime(date_val, '%d/%m/%Y').date()
                    except ValueError:
                        try:
                            transaction_date = datetime.strptime(date_val, '%Y-%m-%d').date()
                        except ValueError:
                             transaction_date = pd.to_datetime(date_val).date()
                else:
                    # Si pandas ya lo parseó (ej: desde Excel)
                    transaction_date = pd.to_datetime(date_val).date()
                
                # Parsear valores numéricos
                quantity = parse_spanish_float(row['quantity'])
                price = parse_spanish_float(row['price'])
                fees = parse_spanish_float(row.get('fees', 0))
                notes = str(row.get('notes', '')) if pd.notna(row.get('notes')) else None

                # Parsear tipo (C/V o BUY/SELL)
                raw_type = str(row['type']).upper().strip()
                type_map = {
                    'C': 'buy', 'V': 'sell',
                    'BUY': 'buy', 'SELL': 'sell',
                    'COMPRA': 'buy', 'VENTA': 'sell'
                }
                
                if raw_type not in type_map:
                    raise ValueError(f"Tipo desconocido: {raw_type}. Use C/V o BUY/SELL.")
                tx_type = type_map[raw_type]

                # Verificar duplicado
                if skip_duplicates:
                    existing = self.db.query(Transaction).filter(
                        and_(
                            Transaction.portfolio_id == portfolio_id,
                            Transaction.asset_id == asset.id,
                            Transaction.transaction_date == transaction_date,
                            Transaction.transaction_type == tx_type,
                            Transaction.quantity == quantity,
                            Transaction.price == price
                        )
                    ).first()
                    
                    if existing:
                        stats['skipped'] += 1
                        continue
                
                # Crear transacción
                transaction = Transaction(
                    portfolio_id=portfolio_id,
                    asset_id=asset.id,
                    transaction_type=tx_type,
                    transaction_date=transaction_date,
                    quantity=quantity,
                    price=price,
                    fees=fees,
                    notes=notes
                )
                
                self.db.add(transaction)
                stats['created'] += 1
                
                # Track min date for snapshot recalculation
                if stats['min_date'] is None or transaction_date < stats['min_date']:
                    stats['min_date'] = transaction_date
                
            except Exception as e:
                stats['errors'].append(f"Fila {idx + 2}: {str(e)}")
        
        self.db.commit()
        
        # Recalcular posiciones para los assets afectados
        # Optimizacion: Recolectar assets afectados y recalcular solo esos
        from app.services.position_service import PositionService
        position_service = PositionService(self.db)
        
        affected_assets = set()
        for idx, row in df.iterrows():
             try:
                asset_symbol = str(row['asset_symbol']).upper()
                asset = self.db.query(Asset).filter(Asset.symbol == asset_symbol).first()
                if asset:
                    affected_assets.add(asset.id)
             except:
                 pass
                 
        for asset_id in affected_assets:
            position_service.recalculate_position(portfolio_id, asset_id)
            
        self.db.commit()
        return stats

    def import_transactions_csv(
        self, 
        portfolio_id: UUID,
        csv_content: str,
        skip_duplicates: bool = True
    ) -> Dict[str, any]:
        """Importar transacciones desde CSV"""
        df = pd.read_csv(io.StringIO(csv_content))
        stats = self._process_transactions_df(df, portfolio_id, skip_duplicates)
        
        # Trigger snapshot recalculation if transactions were created
        if stats.get('created', 0) > 0 and stats.get('min_date'):
            from datetime import datetime
            from app.services.snapshot_service import SnapshotService
            
            today = datetime.now().date()
            min_date = stats['min_date']
            
            # Create a new session for the background task
            # This is a placeholder for actual background task handling in a web framework
            # In a real FastAPI app, this would be passed to background_tasks.add_task
            def run_recalculation_in_background(pid, start_date, end_date):
                from app.core.database import SessionLocal
                db_bg = SessionLocal()
                try:
                    snapshot_service_bg = SnapshotService(db_bg)
                    snapshot_service_bg.create_daily_snapshots_for_portfolio(
                        pid, start_date, end_date, overwrite=True
                    )
                finally:
                    db_bg.close()
            
            # In a service layer, we can't directly add to FastAPI's BackgroundTasks.
            # This is a conceptual trigger. The actual background task execution
            # would happen in the API endpoint that calls this service method.
            # For now, we'll just return the stats. The API layer would handle the task.
            # If this service method were to directly trigger it, it would need a way
            # to manage background processes, which is usually handled by the framework.
            pass # The actual background task logic is moved to the API layer.
        
        return stats

    def import_transactions_xlsx(
        self, 
        portfolio_id: UUID,
        file_content: bytes,
        skip_duplicates: bool = True
    ) -> Dict[str, any]:
        """Importar transacciones desde XLSX"""
        df = pd.read_excel(io.BytesIO(file_content))
        stats = self._process_transactions_df(df, portfolio_id, skip_duplicates)

        # Trigger snapshot recalculation if transactions were created
        if stats.get('created', 0) > 0 and stats.get('min_date'):
            from datetime import datetime
            from app.services.snapshot_service import SnapshotService
            
            today = datetime.now().date()
            min_date = stats['min_date']
            
            def run_recalculation_in_background(pid, start_date, end_date):
                from app.core.database import SessionLocal
                db_bg = SessionLocal()
                try:
                    snapshot_service_bg = SnapshotService(db_bg)
                    snapshot_service_bg.create_daily_snapshots_for_portfolio(
                        pid, start_date, end_date, overwrite=True
                    )
                finally:
                    db_bg.close()
            
            pass # The actual background task logic is moved to the API layer.
        
        return stats
    
    def import_quotes_csv(
        self,
        csv_content: str,
        skip_duplicates: bool = True
    ) -> Dict[str, any]:
        """
        Importar cotizaciones desde CSV
        """
        # Leer CSV
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Validar columnas requeridas
        required_columns = ['symbol', 'date', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Columnas requeridas faltantes: {', '.join(missing_columns)}")
        
        stats = {
            'total': len(df),
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        from decimal import Decimal
        
        for idx, row in df.iterrows():
            try:
                symbol = str(row['symbol']).upper()
                quote_date = pd.to_datetime(row['date']).date()
                timestamp = datetime.combine(quote_date, datetime.min.time())
                
                # Buscar asset
                asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
                if not asset:
                    stats['errors'].append(f"Fila {idx + 2}: Asset {symbol} no encontrado")
                    stats['skipped'] += 1
                    continue

                # Verificar si existe
                existing = self.db.query(Quote).filter(
                    and_(
                        Quote.asset_id == asset.id,
                        Quote.timestamp == timestamp
                    )
                ).first()
                
                if existing:
                    if skip_duplicates:
                        stats['skipped'] += 1
                        continue
                    else:
                        # Actualizar
                        existing.open = Decimal(str(row['open']))
                        existing.high = Decimal(str(row['high']))
                        existing.low = Decimal(str(row['low']))
                        existing.close = Decimal(str(row['close']))
                        existing.volume = int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None
                        existing.source = str(row.get('source', 'manual'))
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                else:
                    # Crear nueva
                    quote = Quote(
                        asset_id=asset.id,
                        timestamp=timestamp,
                        open=Decimal(str(row['open'])),
                        high=Decimal(str(row['high'])),
                        low=Decimal(str(row['low'])),
                        close=Decimal(str(row['close'])),
                        volume=int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
                        source=str(row.get('source', 'manual'))
                    )
                    self.db.add(quote)
                    stats['created'] += 1
                    
            except Exception as e:
                stats['errors'].append(f"Fila {idx + 2}: {str(e)}")
        
        self.db.commit()
        return stats
