"""
Servicio para gestión de cotizaciones históricas
Incluye importación desde Alpha Vantage y Finnhub
"""
from typing import Optional, Dict, List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import finnhub
import pandas as pd
import logging
from alpha_vantage.timeseries import TimeSeries

from app.core.config import settings
from app.models.quote import Quote
from app.schemas.quote import QuoteCreate, QuoteBulkCreate, QuoteBulkResponse


class QuoteService:
    """Servicio para gestión de cotizaciones"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        self.alpha_vantage_ts = TimeSeries(key=settings.ALPHA_VANTAGE_API_KEY, output_format='pandas')
    
    def get_quotes(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Quote]:
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
    
    def import_historical_from_alphavantage(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> QuoteBulkResponse:
        """
        Importar datos históricos desde Alpha Vantage
        
        Args:
            symbol: Símbolo del activo
            start_date: Fecha de inicio
            end_date: Fecha de fin
        
        Returns:
            QuoteBulkResponse con estadísticas
        """
        try:
            self.logger.info(f"Importing historical data for {symbol} from {start_date} to {end_date} using Alpha Vantage")
            
            # Obtener datos históricos completos (últimos 20 años o outputsize=full)
            # Usar get_daily en lugar de get_daily_adjusted (que requiere premium)
            df, meta_data = self.alpha_vantage_ts.get_daily(
                symbol=symbol.upper(),
                outputsize='full'  # 'compact' = 100 días, 'full' = 20+ años
            )
            
            if df is None or df.empty:
                self.logger.warning(f"No data returned from Alpha Vantage for {symbol}")
                return QuoteBulkResponse(
                    total=0,
                    created=0,
                    updated=0,
                    skipped=0,
                    errors=[f"No se encontraron datos para {symbol} en Alpha Vantage. Verifica que el símbolo sea correcto."]
                )
            
            # Filtrar por rango de fechas
            df.index = pd.to_datetime(df.index)
            mask = (df.index.date >= start_date) & (df.index.date <= end_date)
            df = df.loc[mask]
            
            if df.empty:
                self.logger.warning(f"No data in date range for {symbol}")
                return QuoteBulkResponse(
                    total=0,
                    created=0,
                    updated=0,
                    skipped=0,
                    errors=[f"No hay datos en el rango de fechas para {symbol}"]
                )

            # Convertir DataFrame a QuoteCreate
            # Alpha Vantage columns para get_daily: 1. open, 2. high, 3. low, 4. close, 5. volume
            quotes = []
            for idx, row in df.iterrows():
                quote_date = idx.date()

                # Validar que tengamos al menos el precio de cierre
                close_price = row.get('4. close')
                if pd.isna(close_price):
                    continue
                
                quotes.append(QuoteCreate(
                    symbol=symbol.upper(),
                    date=quote_date,
                    open=float(row['1. open']) if not pd.isna(row.get('1. open')) else None,
                    high=float(row['2. high']) if not pd.isna(row.get('2. high')) else None,
                    low=float(row['3. low']) if not pd.isna(row.get('3. low')) else None,
                    close=float(close_price),
                    volume=int(row['5. volume']) if not pd.isna(row.get('5. volume')) and row.get('5. volume', 0) > 0 else None,
                    source="alphavantage"
                ))
            
            self.logger.info(f"Retrieved {len(quotes)} quotes for {symbol} from Alpha Vantage")

            if not quotes:
                return QuoteBulkResponse(
                    total=0,
                    created=0,
                    updated=0,
                    skipped=0,
                    errors=[f"No se pudieron procesar datos para {symbol}"]
                )

            # Importar en masa
            bulk_data = QuoteBulkCreate(quotes=quotes, skip_duplicates=True)
            return self.bulk_import_quotes(bulk_data)
            
        except Exception as e:
            self.logger.error(f"Error importing from Alpha Vantage for {symbol}: {str(e)}", exc_info=True)
            return QuoteBulkResponse(
                total=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[f"Error al importar desde Alpha Vantage: {str(e)}"]
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

    def get_missing_date_ranges(
        self,
        symbol: str,
        from_date: date,
        to_date: date
    ) -> List[tuple[date, date]]:
        """
        Encontrar rangos de fechas faltantes para un símbolo

        Args:
            symbol: Símbolo del activo
            from_date: Fecha de inicio
            to_date: Fecha de fin

        Returns:
            Lista de tuplas (inicio, fin) donde faltan cotizaciones
        """
        # Obtener todas las fechas existentes en el rango
        existing = self.db.query(Quote.date).filter(
            and_(
                Quote.symbol == symbol.upper(),
                Quote.date >= from_date,
                Quote.date <= to_date
            )
        ).order_by(Quote.date).all()

        existing_dates = [row[0] for row in existing]

        if not existing_dates:
            # No hay cotizaciones, retornar el rango completo
            return [(from_date, to_date)]

        # Encontrar gaps en los datos
        missing_ranges = []
        current_date = from_date

        for existing_date in existing_dates:
            if current_date < existing_date:
                # Encontrado un gap
                gap_end = existing_date - timedelta(days=1)
                missing_ranges.append((current_date, gap_end))
            current_date = existing_date + timedelta(days=1)

        # Verificar si hay un gap al final
        if current_date <= to_date:
            missing_ranges.append((current_date, to_date))

        return missing_ranges

    def import_historical_smart(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        force_refresh: bool = False
    ) -> QuoteBulkResponse:
        """
        Importar datos históricos de forma inteligente (solo gaps)

        Si force_refresh=False, solo importa rangos de fechas faltantes.
        Si force_refresh=True, re-importa todos los datos.

        Args:
            symbol: Símbolo del activo
            start_date: Fecha de inicio
            end_date: Fecha de fin
            force_refresh: Si True, re-importa todo

        Returns:
            QuoteBulkResponse con estadísticas
        """
        if force_refresh:
            # Re-importar todo usando Alpha Vantage
            return self.import_historical_from_alphavantage(symbol, start_date, end_date)

        # Encontrar rangos faltantes
        missing_ranges = self.get_missing_date_ranges(symbol, start_date, end_date)

        self.logger.info(f"Smart import for {symbol}: missing_ranges={missing_ranges}, force_refresh={force_refresh}")

        if not missing_ranges:
            return QuoteBulkResponse(
                total=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[],
                message="Todos los datos ya existen"
            )

        # Importar cada rango faltante
        total_created = 0
        total_updated = 0
        total_skipped = 0
        all_errors = []

        for range_start, range_end in missing_ranges:
            result = self.import_historical_from_alphavantage(symbol, range_start, range_end)
            total_created += result.created
            total_updated += result.updated
            total_skipped += result.skipped
            all_errors.extend(result.errors)

        return QuoteBulkResponse(
            total=total_created + total_updated + total_skipped,
            created=total_created,
            updated=total_updated,
            skipped=total_skipped,
            errors=all_errors,
            message=f"Importados {total_created} nuevos registros en {len(missing_ranges)} rangos"
        )

    def update_latest_quote_realtime(self, symbol: str) -> Optional[Dict]:
        """
        Actualizar con la última cotización en tiempo real desde Finnhub

        Args:
            symbol: Símbolo del activo

        Returns:
            Dict con información de la actualización o None
        """
        try:
            # Obtener quote en tiempo real
            quote_data = self.finnhub_client.quote(symbol.upper())

            if not quote_data or quote_data.get('c') is None:
                return {
                    "success": False,
                    "error": "No quote available",
                    "ticker": symbol
                }

            # Crear QuoteCreate con datos actuales
            today = datetime.utcnow().date()

            quote_create = QuoteCreate(
                symbol=symbol.upper(),
                date=today,
                open=quote_data.get('o', quote_data['c']),
                high=quote_data.get('h', quote_data['c']),
                low=quote_data.get('l', quote_data['c']),
                close=quote_data['c'],
                volume=None,  # El endpoint 'quote' no devuelve volumen
                source="finnhub"
            )

            # Verificar si ya existe para hoy
            existing = self.get_quote_by_symbol_date(symbol.upper(), today)

            if existing:
                # Actualizar
                self.update_quote(str(existing.id), {
                    'open': quote_create.open,
                    'high': quote_create.high,
                    'low': quote_create.low,
                    'close': quote_create.close,
                    'source': 'finnhub'
                })
                action = "updated"
            else:
                # Crear
                self.create_quote(quote_create)
                action = "created"

            return {
                "success": True,
                "ticker": symbol,
                "price": quote_data['c'],
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ticker": symbol
            }
