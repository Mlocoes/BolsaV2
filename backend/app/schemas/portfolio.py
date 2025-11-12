from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

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
    id: int
    name: str
    description: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Asset Schemas
class AssetCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: AssetType
    currency: str = Field(default="USD", max_length=10)

class AssetResponse(BaseModel):
    id: int
    symbol: str
    name: str
    asset_type: AssetType
    currency: str
    
    class Config:
        from_attributes = True

# Position Schemas
class PositionResponse(BaseModel):
    id: int
    portfolio_id: int
    asset_id: int
    asset: AssetResponse
    quantity: float
    average_price: float
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionCreate(BaseModel):
    asset_id: int
    transaction_type: TransactionType
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fees: float = Field(default=0, ge=0)
    notes: Optional[str] = Field(None, max_length=500)
    transaction_date: Optional[datetime] = None

class TransactionResponse(BaseModel):
    id: int
    portfolio_id: int
    asset_id: int
    asset: AssetResponse
    transaction_type: TransactionType
    quantity: float
    price: float
    fees: float
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
