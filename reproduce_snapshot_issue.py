
import sys
import os
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
if os.path.exists('backend'):
    sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.usuario import Usuario
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction, TransactionType
from app.services.snapshot_service import SnapshotService

# Setup DB connection
# Use localhost for local execution
settings.DATABASE_URL = "postgresql://bolsav2_user:bolsav2pass@localhost:5432/bolsav2"
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def run_verification():
    print("Starting snapshot verification...")
    
    # 1. Setup Test Data
    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    
    print(f"Creating test data... User: {user_id}, Portfolio: {portfolio_id}")
    
    try:
        # Create User
        user = Usuario(id=user_id, email=f"test_snap_{str(user_id)[:8]}@example.com", hashed_password="test", username=f"test_snap_{str(user_id)[:8]}")
        db.add(user)
        
        # Create Portfolio
        portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Test Snapshot Portfolio")
        db.add(portfolio)
        
        # Create Asset (NVDA)
        asset = Asset(id=asset_id, symbol=f"NVDA_{str(user_id)[:4]}", name="NVIDIA Corp", asset_type="stock")
        db.add(asset)
        
        db.commit()
        
        # 2. Create Transaction on Nov 3rd
        tx_date = datetime(2025, 11, 3, 12, 0, 0) # Nov 3rd, 2025
        print(f"Creating transaction on {tx_date}")
        
        tx1 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=100.0,
            price=170.0,
            transaction_date=tx_date
        )
        db.add(tx1)
        db.commit()
        
        # 3. Generate Snapshot for Nov 21st
        snap_date = date(2025, 11, 21)
        print(f"Generating snapshot for {snap_date}")
        
        snapshot = SnapshotService.create_snapshot(db, portfolio_id, snap_date, overwrite=True)
        
        # 4. Verify Snapshot Content
        print(f"Snapshot created. ID: {snapshot.id}")
        print(f"Total Value: {snapshot.total_value}")
        print(f"Num Positions: {snapshot.number_of_positions}")
        
        # Check if NVDA is in positions
        found = False
        # We need to query position snapshots
        from app.db.models_snapshots import PositionSnapshot
        pos_snaps = db.scalars(select(PositionSnapshot).where(PositionSnapshot.portfolio_snapshot_id == snapshot.id)).all()
        
        for pos in pos_snaps:
            print(f"Position: {pos.ticker}, Qty: {pos.quantity}")
            if pos.asset_id == asset_id:
                found = True
                if abs(pos.quantity - Decimal('100.0')) < Decimal('0.001'):
                    print("✅ SUCCESS: NVDA position found with correct quantity 100.0")
                else:
                    print(f"❌ FAILURE: NVDA position found but quantity is {pos.quantity} (Expected 100.0)")
        
        if not found:
            print("❌ FAILURE: NVDA position NOT found in snapshot")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        # Cleanup
        print("\nCleaning up...")
        try:
            # Delete snapshots first (cascade should handle positions)
            from app.db.models_snapshots import PortfolioSnapshot
            db.execute(text(f"DELETE FROM portfolio_snapshots WHERE portfolio_id = '{portfolio_id}'"))
            db.execute(text(f"DELETE FROM transactions WHERE portfolio_id = '{portfolio_id}'"))
            db.execute(text(f"DELETE FROM assets WHERE id = '{asset_id}'"))
            db.execute(text(f"DELETE FROM portfolios WHERE id = '{portfolio_id}'"))
            db.execute(text(f"DELETE FROM usuarios WHERE id = '{user_id}'"))
            db.commit()
            print("Cleanup complete.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        db.close()

if __name__ == "__main__":
    run_verification()
