"""
Servicio para obtener precios de activos usando Finnhub API
"""
import os
import httpx
import logging
from typing import Optional, Dict
from ..core.config import settings

logger = logging.getLogger(__name__)

class FinnhubService:
    def __init__(self):
        self.api_key = settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Obtener cotización de una acción"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": symbol, "token": self.api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):  # c = current price
                        return {
                            "symbol": symbol,
                            "current_price": data["c"],
                            "high": data["h"],
                            "low": data["l"],
                            "open": data["o"],
                            "previous_close": data["pc"],
                            "change": data["c"] - data["pc"],
                            "change_percent": ((data["c"] - data["pc"]) / data["pc"] * 100) if data["pc"] else 0
                        }
                return None
        except Exception as e:
            logger.error(f"Error fetching stock quote for {symbol}: {e}")
            return None
    
    async def get_crypto_price(self, symbol: str) -> Optional[Dict]:
        """Obtener precio de criptomoneda"""
        # Finnhub usa formato BINANCE:BTCUSDT
        crypto_symbol = f"BINANCE:{symbol}USDT"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": crypto_symbol, "token": self.api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):
                        return {
                            "symbol": symbol,
                            "current_price": data["c"],
                            "high": data["h"],
                            "low": data["l"],
                            "open": data["o"],
                            "previous_close": data["pc"],
                            "change": data["c"] - data["pc"],
                            "change_percent": ((data["c"] - data["pc"]) / data["pc"] * 100) if data["pc"] else 0
                        }
                return None
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
            return None
    
    async def get_asset_price(self, symbol: str, asset_type: str) -> Optional[Dict]:
        """Obtener precio de cualquier tipo de asset"""
        if asset_type == "crypto":
            return await self.get_crypto_price(symbol)
        elif asset_type in ["stock", "etf"]:
            return await self.get_stock_quote(symbol)
        elif asset_type == "cash":
            # Para cash, el precio es siempre 1
            return {
                "symbol": symbol,
                "current_price": 1.0,
                "high": 1.0,
                "low": 1.0,
                "open": 1.0,
                "previous_close": 1.0,
                "change": 0.0,
                "change_percent": 0.0
            }
        return None

# Instancia global del servicio
finnhub_service = FinnhubService()
