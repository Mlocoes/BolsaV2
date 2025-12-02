import sys
import os
from datetime import datetime, date
from uuid import uuid4

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.portfolio import Portfolio
from app.models.asset import Asset, AssetType
from app.models.transaction import Transaction, TransactionType
from app.services.fiscal_service import FiscalService
from app.models.usuario import Usuario

def verify_fiscal_logic():
    db = SessionLocal()
    try:
        # 1. Create Test User and Portfolio
        user = db.query(Usuario).first()
        if not user:
            print("No user found. Please create a user first.")
            return

        portfolio_id = uuid4()
        portfolio = Portfolio(
            id=portfolio_id,
            user_id=user.id,
            name="Fiscal Test Portfolio",
            description="Test portfolio for fiscal logic"
        )
        db.add(portfolio)
        
        # 2. Create Asset NVDA
        asset = db.query(Asset).filter(Asset.symbol == "NVDA").first()
        if not asset:
            asset = Asset(
                id=uuid4(),
                symbol="NVDA",
                name="NVIDIA Corp",
                asset_type=AssetType.STOCK,
                currency="USD"
            )
            db.add(asset)
        
        db.commit()

        print(f"Created portfolio {portfolio_id} and ensuring asset NVDA exists")

        # 3. Create Transactions
        # 01/01/25 – compra de 100 NVDA a USD 120
        t1 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            transaction_type=TransactionType.BUY,
            quantity=100,
            price=120,
            transaction_date=datetime(2025, 1, 1, 10, 0, 0)
        )
        
        # 05/01/25 – compra de 100 NVDA a USD 130
        t2 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            transaction_type=TransactionType.BUY,
            quantity=100,
            price=130,
            transaction_date=datetime(2025, 1, 5, 10, 0, 0)
        )
        
        # 20/01/25 – venta de 50 NVDA a USD 150
        t3 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            transaction_type=TransactionType.SELL,
            quantity=50,
            price=150,
            transaction_date=datetime(2025, 1, 20, 10, 0, 0)
        )
        
        # 25/01/25 – venta de 100 a USD 125
        t4 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            transaction_type=TransactionType.SELL,
            quantity=100,
            price=125,
            transaction_date=datetime(2025, 1, 25, 10, 0, 0)
        )
        
        # 26/01/25 – venta de 50 NVDA a USD 120
        t5 = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            transaction_type=TransactionType.SELL,
            quantity=50,
            price=120,
            transaction_date=datetime(2025, 1, 26, 10, 0, 0)
        )
        
        db.add_all([t1, t2, t3, t4, t5])
        db.commit()
        print("Created transactions")

        # 4. Calculate Fiscal Result
        service = FiscalService(db)
        result = service.calculate_fiscal_result(portfolio_id)
        
        print("\n--- Fiscal Results ---")
        print(f"Total Result: {result.total_result}")
        for item in result.items:
            print(f"Sell: {item.date_sell.date()} Qty: {item.quantity} Price: {item.price_sell} | Buy: {item.date_buy.date()} Price: {item.price_buy} | Result: {item.result}")

        # 5. Verify
        expected_total = 1000.0
        if abs(result.total_result - expected_total) < 0.01:
            print("\nSUCCESS: Total result matches expected value (1000)")
        else:
            print(f"\nFAILURE: Expected {expected_total}, got {result.total_result}")

        # Verify individual items roughly
        # We expect 4 items
        if len(result.items) == 4:
            print("SUCCESS: Generated 4 result items")
        else:
            print(f"FAILURE: Expected 4 items, got {len(result.items)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        # db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).delete()
        # db.query(Portfolio).filter(Portfolio.id == portfolio_id).delete()
        # db.commit()
        # print("Cleaned up test data")
        db.close()

if __name__ == "__main__":
    verify_fiscal_logic()
