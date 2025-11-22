"""update quotes and results

Revision ID: 003
Revises: 002
Create Date: 2025-11-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # --- Quotes Table ---
    # Since we are changing the primary key structure/constraints significantly and data can be re-imported,
    # we will clear the table to avoid migration conflicts with existing data.
    op.execute("TRUNCATE TABLE quotes CASCADE")

    # Drop old columns/indexes/constraints
    op.drop_constraint('uq_quote_symbol_date', 'quotes', type_='unique')
    op.drop_index('idx_quote_symbol_date', table_name='quotes')
    op.drop_index('idx_quote_date', table_name='quotes')
    
    op.drop_column('quotes', 'symbol')
    op.drop_column('quotes', 'date')

    # Add new columns
    op.add_column('quotes', sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('quotes', sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False))
    
    # Create ForeignKey
    op.create_foreign_key(None, 'quotes', 'assets', ['asset_id'], ['id'])

    # Alter existing columns to Numeric/BigInteger
    op.alter_column('quotes', 'open',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=False)
    op.alter_column('quotes', 'high',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=False)
    op.alter_column('quotes', 'low',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=False)
    op.alter_column('quotes', 'close',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=False)
    op.alter_column('quotes', 'volume',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=True)

    # Create new indexes/constraints
    op.create_index('idx_quote_asset_timestamp', 'quotes', ['asset_id', 'timestamp'], unique=False)
    op.create_index('idx_quote_timestamp', 'quotes', ['timestamp'], unique=False)
    op.create_unique_constraint('uq_quote_asset_timestamp', 'quotes', ['asset_id', 'timestamp'])
    op.create_index(op.f('ix_quotes_asset_id'), 'quotes', ['asset_id'], unique=False)
    op.create_index(op.f('ix_quotes_timestamp'), 'quotes', ['timestamp'], unique=False)


    # --- Results Table ---
    op.alter_column('results', 'total_invested',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=True)
    op.alter_column('results', 'total_current_value',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=True)
    op.alter_column('results', 'pnl_absolute',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=True)
    op.alter_column('results', 'pnl_percent',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=18, scale=6),
               existing_nullable=True)


def downgrade():
    # --- Results Table ---
    op.alter_column('results', 'pnl_percent',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('results', 'pnl_absolute',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('results', 'total_current_value',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('results', 'total_invested',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)

    # --- Quotes Table ---
    op.execute("TRUNCATE TABLE quotes CASCADE")

    op.drop_index(op.f('ix_quotes_timestamp'), table_name='quotes')
    op.drop_index(op.f('ix_quotes_asset_id'), table_name='quotes')
    op.drop_constraint('uq_quote_asset_timestamp', 'quotes', type_='unique')
    op.drop_index('idx_quote_timestamp', table_name='quotes')
    op.drop_index('idx_quote_asset_timestamp', table_name='quotes')
    
    op.alter_column('quotes', 'volume',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.alter_column('quotes', 'close',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    op.alter_column('quotes', 'low',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    op.alter_column('quotes', 'high',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    op.alter_column('quotes', 'open',
               existing_type=sa.Numeric(precision=18, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)

    op.drop_constraint(None, 'quotes', type_='foreignkey')
    op.drop_column('quotes', 'timestamp')
    op.drop_column('quotes', 'asset_id')

    op.add_column('quotes', sa.Column('date', sa.DATE(), autoincrement=False, nullable=False))
    op.add_column('quotes', sa.Column('symbol', sa.VARCHAR(length=20), autoincrement=False, nullable=False))
    
    op.create_index('idx_quote_date', 'quotes', ['date'], unique=False)
    op.create_index('idx_quote_symbol_date', 'quotes', ['symbol', 'date'], unique=False)
    op.create_unique_constraint('uq_quote_symbol_date', 'quotes', ['symbol', 'date'])
