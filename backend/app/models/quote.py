"""
Modelo para cotizaciones históricas (OHLCV)
Open, High, Low, Close, Volume
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Date, Index, UniqueConstraint, ForeignKey, Numeric, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Quote(Base):
    """Cotizaciones históricas de activos"""
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # OHLCV data - Usamos Numeric(18, 6) para precisión financiera
    open = Column(Numeric(18, 6), nullable=False)
    high = Column(Numeric(18, 6), nullable=False)
    low = Column(Numeric(18, 6), nullable=False)
    close = Column(Numeric(18, 6), nullable=False)
    volume = Column(BigInteger, nullable=True)
    
    # Metadata
    source = Column(String(50), nullable=True)  # finnhub, yahoo, manual, etc
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    asset = relationship("Asset", backref="quotes")
    
    # Constraint: Un asset no puede tener dos quotes para el mismo timestamp
    __table_args__ = (
        UniqueConstraint('asset_id', 'timestamp', name='uq_quote_asset_timestamp'),
        Index('idx_quote_asset_timestamp', 'asset_id', 'timestamp'),  # Índice compuesto para queries rápidas
        Index('idx_quote_timestamp', 'timestamp'),  # Índice para queries por rango de fechas
    )
    
    def __repr__(self):
        return f"<Quote {self.asset_id} {self.timestamp} close={self.close}>"
