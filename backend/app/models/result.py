from sqlalchemy import Column, Float, Date, ForeignKey, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class Result(Base):
    __tablename__ = "results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Métricas calculadas - Usamos Numeric(18, 6) para precisión financiera
    total_invested = Column(Numeric(18, 6), default=0.0)
    total_current_value = Column(Numeric(18, 6), default=0.0)
    pnl_absolute = Column(Numeric(18, 6), default=0.0)
    pnl_percent = Column(Numeric(18, 6), default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    portfolio = relationship("Portfolio", back_populates="results")
