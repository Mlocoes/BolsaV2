import asyncio
import sys
import os
from datetime import date

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.database import SessionLocal
from app.services.result_service import ResultService
from app.models import *
from uuid import uuid4

def verify_calculation():
    print("Verifying Result Calculation...")
    db = SessionLocal()
    try:
        # 1. Create Mock Data
        # User
        user = db.query(Usuario).filter(Usuario.username == "test_calc").first()
        if not user:
            user = Usuario(username="test_calc", email="test_calc@example.com", hashed_password="hash", is_active=True)
            db.add(user)
            db.commit()
            
        # Portfolio
        portfolio = Portfolio(name="Test Portfolio", user_id=user.id)
        db.add(portfolio)
        db.commit()
        
        # Asset
        asset = db.query(Asset).filter(Asset.symbol == "TEST").first()
        if not asset:
            asset = Asset(symbol="TEST", name="Test Asset", asset_type=AssetType.STOCK)
            db.add(asset)
            db.commit()
            
        # Quote (Yesterday)
        quote = Quote(symbol="TEST", date=date(2023, 1, 1), close=150.0, open=100, high=100, low=100)
        db.add(quote)
        try:
            db.commit()
        except:
            db.rollback() # Quote might exist
            
        # Position
        position = Position(portfolio_id=portfolio.id, asset_id=asset.id, quantity=10, average_price=100.0)
        db.add(position)
        db.commit()
        
        print(f"Created Portfolio {portfolio.id} with 10 shares of TEST @ 100.0")
        print("Current Price (2023-01-01): 150.0")
        
        # 2. Calculate
        service = ResultService(db)
        result = service.calculate_portfolio_result(portfolio.id, calculation_date=date(2023, 1, 1))
        
        print(f"\nCalculation Result:")
        print(f"Invested: {result.total_invested} (Expected: 1000.0)")
        print(f"Current Value: {result.total_current_value} (Expected: 1500.0)")
        print(f"PnL Absolute: {result.pnl_absolute} (Expected: 500.0)")
        print(f"PnL Percent: {result.pnl_percent}% (Expected: 50.0%)")
        
        if result.pnl_absolute == 500.0 and result.pnl_percent == 50.0:
            print("\n✅ Calculation Verified!")
        else:
            print("\n❌ Calculation Failed!")
            
        # Cleanup
        db.delete(position)
        db.delete(portfolio)
        # Keep user/asset/quote for reuse
        db.commit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    verify_calculation()
