
import sys
import os
import uuid
from decimal import Decimal
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

# Add backend to path if not in container (simple check)
if os.path.exists('backend'):
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
# If in container, we are likely in /app, so app module is available directly


from app.core.config import settings
from app.models.usuario import Usuario
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction, TransactionType
from app.models.position import Position
from app.services.position_service import PositionService

# Setup DB connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def run_verification():
    print("Starting verification...")
    
    # 1. Setup Test Data
    user_id = uuid.uuid4()
    portfolio_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    
    print(f"Creating test data... User: {user_id}, Portfolio: {portfolio_id}")
    
    try:
        # Create User
        user = Usuario(id=user_id, email=f"test_{user_id}@example.com", hashed_password="test", username=f"test_{str(user_id)[:8]}")
        db.add(user)
        
        # Create Portfolio
        portfolio = Portfolio(id=portfolio_id, user_id=user_id, name="Test Portfolio")
        db.add(portfolio)
        
        # Create Asset
        asset = Asset(id=asset_id, symbol=f"TEST_{str(user_id)[:8]}", name="Test Asset", asset_type="stock")
        db.add(asset)
        
        db.commit()
        
        # 2. Test Bug Reproduction (No Flush)
        print("\nTest 1: Simulating Bug (No Flush)")
        tx1 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=10.0,
            price=100.0,
            transaction_date=None
        )
        db.add(tx1)
        # NO FLUSH HERE - mimicking the bug
        
        ps = PositionService(db)
        ps.recalculate_position(portfolio_id, asset_id)
        db.commit()
        
        # Check position
        pos = db.scalars(select(Position).where(Position.portfolio_id == portfolio_id, Position.asset_id == asset_id)).first()
        if pos is None:
            print("✅ SUCCESS: Position not created (Bug reproduced: transaction was ignored without flush)")
        else:
            print(f"❌ FAILURE: Position created with qty {pos.quantity} (Expected None or 0)")
            
        # 3. Test Recalculate Logic (The Fix for existing data)
        print("\nTest 2: Testing Recalculate Logic")
        # Now the transaction exists in DB from previous commit
        ps.recalculate_position(portfolio_id, asset_id)
        db.commit()
        
        pos = db.scalars(select(Position).where(Position.portfolio_id == portfolio_id, Position.asset_id == asset_id)).first()
        if pos and abs(pos.quantity - 10.0) < 0.001:
             print(f"✅ SUCCESS: Position correctly recalculated to {pos.quantity}")
        else:
             print(f"❌ FAILURE: Position is {pos.quantity if pos else 'None'} (Expected 10.0)")

        # 4. Test Fix (With Flush)
        print("\nTest 3: Simulating Fix (With Flush)")
        tx2 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=5.0,
            price=100.0,
            transaction_date=None
        )
        db.add(tx2)
        
        # FLUSH HERE - mimicking the fix
        db.flush()
        
        ps.recalculate_position(portfolio_id, asset_id)
        db.commit()
        
        pos = db.scalars(select(Position).where(Position.portfolio_id == portfolio_id, Position.asset_id == asset_id)).first()
        if pos and abs(pos.quantity - 15.0) < 0.001:
             print(f"✅ SUCCESS: Position correctly updated to {pos.quantity} (10 + 5)")
        else:
             print(f"❌ FAILURE: Position is {pos.quantity if pos else 'None'} (Expected 15.0)")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        db.rollback()
    finally:
        # Cleanup
        print("\nCleaning up...")
        try:
            db.execute(text(f"DELETE FROM positions WHERE portfolio_id = '{portfolio_id}'"))
            db.execute(text(f"DELETE FROM transactions WHERE portfolio_id = '{portfolio_id}'"))
            db.execute(text(f"DELETE FROM assets WHERE id = '{asset_id}'"))
            db.execute(text(f"DELETE FROM portfolios WHERE id = '{portfolio_id}'"))
            db.execute(text(f"DELETE FROM users WHERE id = '{user_id}'"))
            db.commit()
            print("Cleanup complete.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        db.close()

if __name__ == "__main__":
    run_verification()
