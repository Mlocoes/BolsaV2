from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..core.database import Base
from .portfolio import AssetType

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    currency = Column(String(10), default="USD")
    
    # Relaciones
    positions = relationship("Position", back_populates="asset")
    transactions = relationship("Transaction", back_populates="asset")
