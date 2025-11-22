from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID

class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"
    BOND = "bond"
    COMMODITY = "commodity"
    CASH = "cash"

class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

# Portfolio Schemas
class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class PortfolioResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Asset Schemas
class AssetCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: AssetType
    market: Optional[str] = Field(None, max_length=50)
    currency: str = Field(default="USD", max_length=10)

class AssetResponse(BaseModel):
    id: UUID
    symbol: str
    name: str
    asset_type: AssetType
    market: Optional[str]
    currency: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Position Schemas
class PositionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    asset_id: UUID
    asset: AssetResponse
    quantity: float
    average_price: float
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionCreate(BaseModel):
    asset_id: UUID
    transaction_type: TransactionType
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fees: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=10)
    notes: Optional[str] = Field(None, max_length=500)
    transaction_date: Optional[datetime] = None

class TransactionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    asset_id: UUID
    asset: AssetResponse
    transaction_type: TransactionType
    quantity: float
    price: float
    fees: float
    currency: str
    notes: Optional[str]
    transaction_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Portfolio con posiciones
class PortfolioDetail(PortfolioResponse):
    positions: List[PositionResponse] = []
    
    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    id: UUID
    asset_id: Optional[UUID] = None
    transaction_type: Optional[TransactionType] = None
    quantity: Optional[float] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    fees: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=500)
    transaction_date: Optional[datetime] = None

class TransactionBatchUpdate(BaseModel):
    transactions: List[TransactionUpdate]
