"""
Add snapshot tables

Revision ID: 002
Revises: 001
Create Date: 2024-11-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create portfolio_snapshots table
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_invested', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('total_value', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('cash_balance', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('daily_pnl', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('daily_pnl_percent', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('total_pnl', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('total_pnl_percent', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('number_of_positions', sa.Numeric(10, 0), nullable=False, server_default='0'),
        sa.Column('number_of_assets', sa.Numeric(10, 0), nullable=False, server_default='0'),
        sa.Column('calculation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('idx_portfolio_snapshot_portfolio_date', 'portfolio_snapshots', ['portfolio_id', 'snapshot_date'])
    op.create_index('idx_portfolio_snapshot_date', 'portfolio_snapshots', ['snapshot_date'])
    op.create_unique_constraint('uq_portfolio_snapshot_date', 'portfolio_snapshots', ['portfolio_id', 'snapshot_date'])

    # Create position_snapshots table
    op.create_table(
        'position_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('portfolio_snapshot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio_snapshots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(24, 8), nullable=False),
        sa.Column('average_buy_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('current_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('total_cost', sa.Numeric(18, 6), nullable=False),
        sa.Column('current_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('position_pnl', sa.Numeric(18, 6), nullable=False),
        sa.Column('position_pnl_percent', sa.Numeric(10, 4), nullable=False),
        sa.Column('daily_change', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('daily_change_percent', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('portfolio_weight', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('idx_position_snapshot_portfolio', 'position_snapshots', ['portfolio_snapshot_id'])
    op.create_index('idx_position_snapshot_asset_date', 'position_snapshots', ['asset_id', 'snapshot_date'])

    # Create snapshot_metrics table
    op.create_table(
        'snapshot_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('weekly_return', sa.Numeric(10, 4), nullable=True),
        sa.Column('monthly_return', sa.Numeric(10, 4), nullable=True),
        sa.Column('yearly_return', sa.Numeric(10, 4), nullable=True),
        sa.Column('ytd_return', sa.Numeric(10, 4), nullable=True),
        sa.Column('daily_volatility', sa.Numeric(10, 6), nullable=True),
        sa.Column('weekly_volatility', sa.Numeric(10, 6), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(10, 4), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(10, 4), nullable=True),
        sa.Column('max_drawdown_date', sa.Date(), nullable=True),
        sa.Column('best_day_return', sa.Numeric(10, 4), nullable=True),
        sa.Column('best_day_date', sa.Date(), nullable=True),
        sa.Column('worst_day_return', sa.Numeric(10, 4), nullable=True),
        sa.Column('worst_day_date', sa.Date(), nullable=True),
        sa.Column('asset_allocation', postgresql.JSONB(), nullable=True),
        sa.Column('sector_allocation', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    op.create_index('idx_snapshot_metrics_portfolio_date', 'snapshot_metrics', ['portfolio_id', 'metric_date'])
    op.create_unique_constraint('uq_portfolio_metrics_date', 'snapshot_metrics', ['portfolio_id', 'metric_date'])


def downgrade():
    op.drop_table('snapshot_metrics')
    op.drop_table('position_snapshots')
    op.drop_table('portfolio_snapshots')
