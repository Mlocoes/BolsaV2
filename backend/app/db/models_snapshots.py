"""
Portfolio Snapshot Models - Daily historical records
"""
import uuid
from datetime import date
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.models import Base


class PortfolioSnapshot(Base):
    """
    Daily snapshot of portfolio state
    Captures complete portfolio status at end of each day
    """
    __tablename__ = "portfolio_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False
    )
    snapshot_date = Column(Date, nullable=False, index=True)

    # Portfolio totals
    total_invested = Column(Numeric(18, 6), nullable=False, default=0)
    total_value = Column(Numeric(18, 6), nullable=False, default=0)
    cash_balance = Column(Numeric(18, 6), nullable=False, default=0)

    # Performance metrics
    daily_pnl = Column(Numeric(18, 6), nullable=False, default=0)
    daily_pnl_percent = Column(Numeric(10, 4), nullable=False, default=0)
    total_pnl = Column(Numeric(18, 6), nullable=False, default=0)
    total_pnl_percent = Column(Numeric(10, 4), nullable=False, default=0)

    # Additional metrics
    number_of_positions = Column(Numeric(10, 0), nullable=False, default=0)
    number_of_assets = Column(Numeric(10, 0), nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    calculation_notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint("portfolio_id", "snapshot_date", name="uq_portfolio_snapshot_date"),
        Index("idx_portfolio_snapshot_portfolio_date", "portfolio_id", "snapshot_date"),
        Index("idx_portfolio_snapshot_date", "snapshot_date"),
    )

    def __repr__(self):
        return f"<PortfolioSnapshot {self.portfolio_id} @ {self.snapshot_date}>"


class PositionSnapshot(Base):
    """
    Daily snapshot of individual position within a portfolio
    Captures asset-level details
    """
    __tablename__ = "position_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_snapshots.id", ondelete="CASCADE"),
        nullable=False
    )
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False
    )
    snapshot_date = Column(Date, nullable=False, index=True)

    # Position details
    ticker = Column(String(20), nullable=False)
    quantity = Column(Numeric(24, 8), nullable=False)
    average_buy_price = Column(Numeric(18, 6), nullable=False)
    current_price = Column(Numeric(18, 6), nullable=False)

    # Position values
    total_cost = Column(Numeric(18, 6), nullable=False)
    current_value = Column(Numeric(18, 6), nullable=False)

    # Performance
    position_pnl = Column(Numeric(18, 6), nullable=False)
    position_pnl_percent = Column(Numeric(10, 4), nullable=False)
    daily_change = Column(Numeric(18, 6), nullable=False, default=0)
    daily_change_percent = Column(Numeric(10, 4), nullable=False, default=0)

    # Weight in portfolio
    portfolio_weight = Column(Numeric(10, 4), nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_position_snapshot_portfolio", "portfolio_snapshot_id"),
        Index("idx_position_snapshot_asset_date", "asset_id", "snapshot_date"),
    )

    def __repr__(self):
        return f"<PositionSnapshot {self.ticker} @ {self.snapshot_date}>"


class SnapshotMetrics(Base):
    """
    Aggregated metrics and analytics for snapshots
    Pre-calculated for faster queries
    """
    __tablename__ = "snapshot_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False
    )
    metric_date = Column(Date, nullable=False)

    # Period metrics (rolling)
    weekly_return = Column(Numeric(10, 4), nullable=True)
    monthly_return = Column(Numeric(10, 4), nullable=True)
    yearly_return = Column(Numeric(10, 4), nullable=True)
    ytd_return = Column(Numeric(10, 4), nullable=True)

    # Volatility metrics
    daily_volatility = Column(Numeric(10, 6), nullable=True)
    weekly_volatility = Column(Numeric(10, 6), nullable=True)

    # Risk metrics
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)
    max_drawdown_date = Column(Date, nullable=True)

    # Best/worst days
    best_day_return = Column(Numeric(10, 4), nullable=True)
    best_day_date = Column(Date, nullable=True)
    worst_day_return = Column(Numeric(10, 4), nullable=True)
    worst_day_date = Column(Date, nullable=True)

    # Asset allocation (stored as JSON)
    asset_allocation = Column(JSONB, nullable=True)
    sector_allocation = Column(JSONB, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        UniqueConstraint("portfolio_id", "metric_date", name="uq_portfolio_metrics_date"),
        Index("idx_snapshot_metrics_portfolio_date", "portfolio_id", "metric_date"),
    )

    def __repr__(self):
        return f"<SnapshotMetrics {self.portfolio_id} @ {self.metric_date}>"