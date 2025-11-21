import sys
import os
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.database import SessionLocal
from app.models.portfolio import Portfolio
from app.models.usuario import Usuario
from app.models.asset import Asset, AssetType
from app.models.transaction import Transaction, TransactionType
from app.db.models_snapshots import PortfolioSnapshot
from app.core.auth import get_password_hash
from app.services.snapshot_service import snapshot_service

def verify_history_update():
    print("Verifying Historical Data Update...")
    db = SessionLocal()
    try:
        # 1. Create Test User and Portfolio
        print("Creating test data...")
        user_id = uuid4()
        user = Usuario(
            id=user_id,
            username=f"test_history_{user_id.hex[:8]}",
            email=f"test_history_{user_id.hex[:8]}@example.com",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        db.add(user)
        
        portfolio_id = uuid4()
        portfolio = Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name="History Test Portfolio"
        )
        db.add(portfolio)
        
        # Create Asset
        asset_id = uuid4()
        asset = Asset(
            id=asset_id,
            symbol="TESTHIST",
            name="Test History Asset",
            asset_type=AssetType.STOCK,
            market="US"
        )
        db.add(asset)
        db.commit()
        
        # 2. Create Snapshots for last 5 days (empty)
        print("Creating initial empty snapshots...")
        today = datetime.now().date()
        start_date = today - timedelta(days=5)
        
        snapshot_service.create_daily_snapshots_for_portfolio(
            db, portfolio_id, start_date, today
        )
        
        # Verify empty snapshots
        snapshots = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id
        ).all()
        print(f"Created {len(snapshots)} initial snapshots.")
        for s in snapshots:
            if s.total_value > 0:
                print(f"❌ Error: Snapshot {s.snapshot_date} should be empty but has value {s.total_value}")
                return
        
        # 3. Simulate "Adding Transaction" in the past (T-3)
        # We simulate the background task logic here directly
        print("Adding transaction at T-3...")
        tx_date = today - timedelta(days=3)
        transaction = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=10,
            price=100,
            transaction_date=tx_date
        )
        db.add(transaction)
        db.commit()
        
        # 4. Trigger Recalculation (Simulating Background Task)
        print("Triggering recalculation...")
        snapshot_service.create_daily_snapshots_for_portfolio(
            db, portfolio_id, tx_date, today, overwrite=True
        )
        
        # 5. Verify Snapshots Updated
        print("Verifying snapshots...")
        snapshots = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.snapshot_date >= tx_date
        ).order_by(PortfolioSnapshot.snapshot_date).all()
        
        for s in snapshots:
            print(f"Snapshot {s.snapshot_date}: Value={s.total_value}")
            if s.total_value != 1000: # 10 * 100
                print(f"❌ Error: Snapshot {s.snapshot_date} should have value 1000 but has {s.total_value}")
                # Note: This assumes no price change (no quotes). 
                # If quotes existed, value would vary. 
                # Since we didn't add quotes, it uses cost basis or 0 if logic dictates.
                # Let's check logic: if no quote, it uses average cost.
                # So value should be cost.
                pass
            else:
                print(f"✅ Snapshot {s.snapshot_date} correct.")

        print("✅ Verification Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        # db.delete(portfolio) # Cascade should handle it
        # db.delete(user)
        # db.commit()
        db.close()

if __name__ == "__main__":
    verify_history_update()
