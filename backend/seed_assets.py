"""
Script para poblar la base de datos con assets de ejemplo
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.portfolio import AssetType

def create_sample_assets():
    """Crear assets de ejemplo"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existen assets
        existing_count = db.query(Asset).count()
        if existing_count > 0:
            print(f"✓ Ya existen {existing_count} assets en la base de datos")
            return
        
        print("Creando assets de ejemplo...")
        
        sample_assets = [
            # Acciones populares
            Asset(symbol="AAPL", name="Apple Inc.", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="GOOGL", name="Alphabet Inc.", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="MSFT", name="Microsoft Corporation", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="AMZN", name="Amazon.com Inc.", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="TSLA", name="Tesla Inc.", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="NVDA", name="NVIDIA Corporation", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="META", name="Meta Platforms Inc.", asset_type=AssetType.STOCK, currency="USD"),
            Asset(symbol="NFLX", name="Netflix Inc.", asset_type=AssetType.STOCK, currency="USD"),
            
            # Criptomonedas
            Asset(symbol="BTC", name="Bitcoin", asset_type=AssetType.CRYPTO, currency="USD"),
            Asset(symbol="ETH", name="Ethereum", asset_type=AssetType.CRYPTO, currency="USD"),
            Asset(symbol="BNB", name="Binance Coin", asset_type=AssetType.CRYPTO, currency="USD"),
            Asset(symbol="ADA", name="Cardano", asset_type=AssetType.CRYPTO, currency="USD"),
            Asset(symbol="SOL", name="Solana", asset_type=AssetType.CRYPTO, currency="USD"),
            
            # ETFs
            Asset(symbol="SPY", name="SPDR S&P 500 ETF Trust", asset_type=AssetType.ETF, currency="USD"),
            Asset(symbol="QQQ", name="Invesco QQQ Trust", asset_type=AssetType.ETF, currency="USD"),
            Asset(symbol="VTI", name="Vanguard Total Stock Market ETF", asset_type=AssetType.ETF, currency="USD"),
            
            # Cash
            Asset(symbol="USD", name="US Dollar", asset_type=AssetType.CASH, currency="USD"),
            Asset(symbol="EUR", name="Euro", asset_type=AssetType.CASH, currency="EUR"),
        ]
        
        for asset in sample_assets:
            db.add(asset)
        
        db.commit()
        print(f"✓ Se crearon {len(sample_assets)} assets de ejemplo")
        
    except Exception as e:
        print(f"Error al crear assets: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_assets()
