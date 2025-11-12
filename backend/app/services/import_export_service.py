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
    
    def import_transactions_csv(
        self, 
        portfolio_id: UUID,
        csv_content: str,
        skip_duplicates: bool = True
    ) -> Dict[str, any]:
        """
        Importar transacciones desde CSV
        
        Args:
            portfolio_id: ID del portfolio destino
            csv_content: Contenido del archivo CSV
            skip_duplicates: Si True, ignora duplicados
            
        Returns:
            Dict con estadísticas de importación
        """
        # Leer CSV
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Validar columnas requeridas
        required_columns = ['date', 'type', 'asset_symbol', 'quantity', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Columnas requeridas faltantes: {', '.join(missing_columns)}")
        
        # Verificar que el portfolio existe
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} no encontrado")
        
        stats = {
            'total': len(df),
            'created': 0,
            'skipped': 0,
            'errors': []
        }
        
        for idx, row in df.iterrows():
            try:
                # Buscar o crear asset
                asset_symbol = str(row['asset_symbol']).upper()
                asset = self.db.query(Asset).filter(Asset.symbol == asset_symbol).first()
                
                if not asset:
                    # Crear asset si no existe
                    asset = Asset(
                        symbol=asset_symbol,
                        name=asset_symbol,
                        type='stock'
                    )
                    self.db.add(asset)
                    self.db.flush()
                
                # Parsear fecha
                transaction_date = pd.to_datetime(row['date']).date()
                
                # Verificar duplicado
                if skip_duplicates:
                    existing = self.db.query(Transaction).filter(
                        and_(
                            Transaction.portfolio_id == portfolio_id,
                            Transaction.asset_id == asset.id,
                            Transaction.transaction_date == transaction_date,
                            Transaction.transaction_type == row['type'].upper(),
                            Transaction.quantity == float(row['quantity']),
                            Transaction.price == float(row['price'])
                        )
                    ).first()
                    
                    if existing:
                        stats['skipped'] += 1
                        continue
                
                # Crear transacción
                transaction = Transaction(
                    portfolio_id=portfolio_id,
                    asset_id=asset.id,
                    transaction_type=str(row['type']).upper(),
                    transaction_date=transaction_date,
                    quantity=float(row['quantity']),
                    price=float(row['price']),
                    fees=float(row.get('fees', 0)),
                    notes=str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
                )
                
                self.db.add(transaction)
                stats['created'] += 1
                
            except Exception as e:
                stats['errors'].append(f"Fila {idx + 2}: {str(e)}")
        
        self.db.commit()
        return stats
    
    def import_quotes_csv(
        self,
        csv_content: str,
        skip_duplicates: bool = True
    ) -> Dict[str, any]:
        """
        Importar cotizaciones desde CSV
        
        Args:
            csv_content: Contenido del archivo CSV
            skip_duplicates: Si True, ignora duplicados
            
        Returns:
            Dict con estadísticas de importación
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
        
        for idx, row in df.iterrows():
            try:
                symbol = str(row['symbol']).upper()
                quote_date = pd.to_datetime(row['date']).date()
                
                # Verificar si existe
                existing = self.db.query(Quote).filter(
                    and_(
                        Quote.symbol == symbol,
                        Quote.date == quote_date
                    )
                ).first()
                
                if existing:
                    if skip_duplicates:
                        stats['skipped'] += 1
                        continue
                    else:
                        # Actualizar
                        existing.open = float(row['open'])
                        existing.high = float(row['high'])
                        existing.low = float(row['low'])
                        existing.close = float(row['close'])
                        existing.volume = int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None
                        existing.source = str(row.get('source', 'manual'))
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                else:
                    # Crear nueva
                    quote = Quote(
                        symbol=symbol,
                        date=quote_date,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
                        source=str(row.get('source', 'manual'))
                    )
                    self.db.add(quote)
                    stats['created'] += 1
                    
            except Exception as e:
                stats['errors'].append(f"Fila {idx + 2}: {str(e)}")
        
        self.db.commit()
        return stats
