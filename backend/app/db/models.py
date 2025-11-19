import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, BigInteger, ForeignKey, Enum, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class AssetType(str, PyEnum):
    STOCK = "stock"
    ETF = "etf"
    FUND = "fund"
    CRYPTO = "crypto"
    OTHER = "other"

class OperationSide(str, PyEnum):
    BUY = "buy"
    SELL = "sell"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(255))
    market = Column(String(50))
    asset_type = Column(Enum(AssetType), default=AssetType.STOCK)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Numeric(18, 6))
    high = Column(Numeric(18, 6))
    low = Column(Numeric(18, 6))
    close = Column(Numeric(18, 6), nullable=False)
    volume = Column(BigInteger)
    source = Column(String(50), default="finnhub")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Operation(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    date = Column(DateTime(timezone=True), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    side = Column(Enum(OperationSide), nullable=False)
    quantity = Column(Numeric(24, 8), nullable=False)
    price = Column(Numeric(18, 6), nullable=False)
    fee = Column(Numeric(18, 6), default=0)
    currency = Column(String(10), default="USD")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Result(Base):
    __tablename__ = "results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_buy_amount = Column(Numeric(18, 6), default=0)
    total_current_amount = Column(Numeric(18, 6), default=0)
    pnl_absolute = Column(Numeric(18, 6), default=0)
    pnl_percent = Column(Numeric(10, 4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
