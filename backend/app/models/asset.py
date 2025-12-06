from sqlalchemy import Column, String, Float, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from .portfolio import AssetType
import uuid

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    market = Column(String(50), nullable=True)  # NASDAQ, NYSE, etc
    currency = Column(String(10), default="USD")
    last_price = Column(Float, nullable=True)
    last_price_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    positions = relationship("Position", back_populates="asset")
    transactions = relationship("Transaction", back_populates="asset")
