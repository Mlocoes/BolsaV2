import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.database import Base, engine
from app.models import *  # Import all models to ensure they are registered
from app.core.session import session_manager
from sqlalchemy import inspect

async def verify():
    print("Verifying setup...")
    
    # 1. Verify DB Tables
    print("Checking database tables...")
    # Use sync engine
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    
    if "results" in tables:
        print("✅ 'results' table exists.")
    else:
        print("❌ 'results' table MISSING.")
            
    # 2. Verify Redis Session
    print("\nChecking Redis Session...")
    try:
        await session_manager.connect()
        session_id = await session_manager.create_session("test_user_id", {"username": "test"})
        print(f"Created session: {session_id}")
        
        retrieved = await session_manager.get_session(session_id)
        if retrieved and retrieved["username"] == "test":
            print("✅ Session retrieved successfully.")
        else:
            print("❌ Failed to retrieve session.")
            
        await session_manager.delete_session(session_id)
        print("Session deleted.")
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
        print("Ensure Redis is running (docker-compose up -d redis).")

if __name__ == "__main__":
    asyncio.run(verify())
