import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.database import SessionLocal
from uuid import uuid4

def debug_snapshot_dates():
    print("Debugging Snapshot Dates...")
    db = SessionLocal()
    try:
        # Try the import that was failing
        print("Attempting import...")
        from app.db.models_snapshots import PortfolioSnapshot
        print("✅ Import successful.")
        
        # Try the query
        from sqlalchemy import select, distinct
        portfolio_id = uuid4() # Dummy ID
        
        print(f"Executing query for portfolio {portfolio_id}...")
        result = db.execute(
            select(distinct(PortfolioSnapshot.snapshot_date))
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.snapshot_date.desc())
        )
        dates = result.scalars().all()
        print(f"✅ Query successful. Found {len(dates)} dates.")
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_snapshot_dates()
