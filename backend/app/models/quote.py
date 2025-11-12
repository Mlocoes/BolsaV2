"""
Modelo para cotizaciones históricas (OHLCV)
Open, High, Low, Close, Volume
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Date, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Quote(Base):
    """Cotizaciones históricas de activos"""
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)  # Puede ser null para algunos assets
    
    # Metadata
    source = Column(String(50), nullable=True)  # finnhub, yahoo, manual, etc
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraint: Un symbol no puede tener dos quotes para la misma fecha
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_quote_symbol_date'),
        Index('idx_quote_symbol_date', 'symbol', 'date'),  # Índice compuesto para queries rápidas
        Index('idx_quote_date', 'date'),  # Índice para queries por rango de fechas
    )
    
    def __repr__(self):
        return f"<Quote {self.symbol} {self.date} close={self.close}>"
