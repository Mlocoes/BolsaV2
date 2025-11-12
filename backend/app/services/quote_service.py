"""
Servicio para gestión de cotizaciones históricas
Incluye importación desde Finnhub y validación de duplicados
"""
from __future__ import annotations
from typing import Optional, Dict
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import finnhub

from app.core.config import settings
from app.models.quote import Quote
from app.schemas.quote import QuoteCreate, QuoteBulkCreate, QuoteBulkResponse


class QuoteService:
    """Servicio para gestión de cotizaciones"""
    
    def __init__(self, db: Session):
        self.db = db
        self.finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
    
    def get_quotes(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> list[Quote]:
        """
        Obtener cotizaciones con filtros opcionales
        
        Args:
            symbol: Filtrar por símbolo
            start_date: Fecha inicio
            end_date: Fecha fin
            limit: Límite de resultados
        
        Returns:
            Lista de Quote
        """
        query = self.db.query(Quote)
        
        if symbol:
            query = query.filter(Quote.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(Quote.date >= start_date)
        
        if end_date:
            query = query.filter(Quote.date <= end_date)
        
        query = query.order_by(Quote.date.desc())
        
        return query.limit(limit).all()
    
    def get_quote_by_symbol_date(self, symbol: str, quote_date: date) -> Optional[Quote]:
        """
        Obtener una cotización específica por símbolo y fecha
        
        Args:
            symbol: Símbolo del activo
            quote_date: Fecha de la cotización
        
        Returns:
            Quote o None
        """
        return self.db.query(Quote).filter(
            and_(
                Quote.symbol == symbol.upper(),
                Quote.date == quote_date
            )
        ).first()
    
    def create_quote(self, quote_data: QuoteCreate) -> Quote:
        """
        Crear una cotización (lanza error si ya existe)
        
        Args:
            quote_data: Datos de la cotización
        
        Returns:
            Quote creado
        
        Raises:
            IntegrityError si ya existe
        """
        quote = Quote(
            symbol=quote_data.symbol.upper(),
            date=quote_data.date,
            open=quote_data.open,
            high=quote_data.high,
            low=quote_data.low,
            close=quote_data.close,
            volume=quote_data.volume,
            source=quote_data.source or "manual"
        )
        
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        
        return quote
    
    def update_quote(self, quote_id: str, quote_data: Dict) -> Optional[Quote]:
        """
        Actualizar una cotización existente
        
        Args:
            quote_id: UUID de la cotización
            quote_data: Datos a actualizar
        
        Returns:
            Quote actualizado o None
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        
        if not quote:
            return None
        
        for key, value in quote_data.items():
            if value is not None and hasattr(quote, key):
                setattr(quote, key, value)
        
        quote.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(quote)
        
        return quote
    
    def bulk_import_quotes(self, bulk_data: QuoteBulkCreate) -> QuoteBulkResponse:
        """
        Importar cotizaciones en masa con manejo de duplicados
        
        Args:
            bulk_data: Datos de importación masiva
        
        Returns:
            QuoteBulkResponse con estadísticas
        """
        total = len(bulk_data.quotes)
        created = 0
        updated = 0
        skipped = 0
        errors = []
        
        for quote_data in bulk_data.quotes:
            try:
                # Verificar si ya existe
                existing = self.get_quote_by_symbol_date(
                    quote_data.symbol,
                    quote_data.date
                )
                
                if existing:
                    if bulk_data.skip_duplicates:
                        # Actualizar existente
                        self.update_quote(str(existing.id), {
                            'open': quote_data.open,
                            'high': quote_data.high,
                            'low': quote_data.low,
                            'close': quote_data.close,
                            'volume': quote_data.volume,
                            'source': quote_data.source,
                        })
                        updated += 1
                    else:
                        # Reportar como error
                        errors.append(
                            f"Duplicado: {quote_data.symbol} en {quote_data.date}"
                        )
                        skipped += 1
                else:
                    # Crear nuevo
                    self.create_quote(quote_data)
                    created += 1
                    
            except Exception as e:
                errors.append(f"Error en {quote_data.symbol} {quote_data.date}: {str(e)}")
                skipped += 1
        
        return QuoteBulkResponse(
            total=total,
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors
        )
    
    def import_historical_from_finnhub(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> QuoteBulkResponse:
        """
        Importar datos históricos desde Finnhub
        
        Args:
            symbol: Símbolo del activo
            start_date: Fecha de inicio
            end_date: Fecha de fin
        
        Returns:
            QuoteBulkResponse con estadísticas
        """
        try:
            # Convertir fechas a timestamps Unix
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            # Obtener datos de Finnhub (candles endpoint)
            candles = self.finnhub_client.stock_candles(
                symbol=symbol.upper(),
                resolution='D',  # Daily
                _from=start_timestamp,
                to=end_timestamp
            )
            
            if candles.get('s') != 'ok':
                return QuoteBulkResponse(
                    total=0,
                    created=0,
                    updated=0,
                    skipped=0,
                    errors=[f"Finnhub error: {candles.get('s', 'unknown')}"]
                )
            
            # Convertir respuesta de Finnhub a QuoteCreate
            quotes = []
            timestamps = candles.get('t', [])
            opens = candles.get('o', [])
            highs = candles.get('h', [])
            lows = candles.get('l', [])
            closes = candles.get('c', [])
            volumes = candles.get('v', [])
            
            for i in range(len(timestamps)):
                quote_date = datetime.fromtimestamp(timestamps[i]).date()
                
                quotes.append(QuoteCreate(
                    symbol=symbol.upper(),
                    date=quote_date,
                    open=opens[i],
                    high=highs[i],
                    low=lows[i],
                    close=closes[i],
                    volume=int(volumes[i]) if volumes[i] else None,
                    source="finnhub"
                ))
            
            # Importar en masa
            bulk_data = QuoteBulkCreate(quotes=quotes, skip_duplicates=True)
            return self.bulk_import_quotes(bulk_data)
            
        except Exception as e:
            return QuoteBulkResponse(
                total=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[f"Error al importar desde Finnhub: {str(e)}"]
            )
    
    def get_latest_quote(self, symbol: str) -> Optional[Quote]:
        """
        Obtener la cotización más reciente de un símbolo
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Quote más reciente o None
        """
        return self.db.query(Quote).filter(
            Quote.symbol == symbol.upper()
        ).order_by(Quote.date.desc()).first()
