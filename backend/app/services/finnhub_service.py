"""
Servicio para obtener precios de activos usando Finnhub API
"""
import os
import httpx
import logging
from typing import Optional, Dict
from ..core.config import settings

logger = logging.getLogger(__name__)

import json
import redis.asyncio as redis
from datetime import timedelta

class FinnhubService:
    def __init__(self):
        self.api_key = settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = timedelta(minutes=5)
        self.cache_prefix = "price_cache:"
        
    async def connect_redis(self):
        """Lazy connection to Redis"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

    async def _get_cache(self, symbol: str) -> Optional[Dict]:
        await self.connect_redis()
        if self.redis_client:
            data = await self.redis_client.get(f"{self.cache_prefix}{symbol}")
            if data:
                return json.loads(data)
        return None

    async def _set_cache(self, symbol: str, data: Dict):
        await self.connect_redis()
        if self.redis_client:
            await self.redis_client.setex(
                f"{self.cache_prefix}{symbol}",
                self.cache_ttl,
                json.dumps(data)
            )

    async def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Obtener cotización de una acción con caching"""
        # Intentar cache primero
        cached = await self._get_cache(symbol)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": symbol, "token": self.api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):  # c = current price
                        result = {
                            "symbol": symbol,
                            "current_price": data["c"],
                            "high": data["h"],
                            "low": data["l"],
                            "open": data["o"],
                            "previous_close": data["pc"],
                            "change": data["c"] - data["pc"],
                            "change_percent": ((data["c"] - data["pc"]) / data["pc"] * 100) if data["pc"] else 0
                        }
                        # Guardar en cache
                        await self._set_cache(symbol, result)
                        return result
                return None
        except Exception as e:
            logger.error(f"Error fetching stock quote for {symbol}: {e}")
            return None
    
    async def get_crypto_price(self, symbol: str) -> Optional[Dict]:
        """Obtener precio de criptomoneda con caching"""
        # Cache key para crypto
        cache_key = f"CRYPTO:{symbol}"
        cached = await self._get_cache(cache_key)
        if cached:
            return cached

        # Finnhub usa formato BINANCE:BTCUSDT
        crypto_symbol = f"BINANCE:{symbol}USDT"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": crypto_symbol, "token": self.api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):
                        result = {
                            "symbol": symbol,
                            "current_price": data["c"],
                            "high": data["h"],
                            "low": data["l"],
                            "open": data["o"],
                            "previous_close": data["pc"],
                            "change": data["c"] - data["pc"],
                            "change_percent": ((data["c"] - data["pc"]) / data["pc"] * 100) if data["pc"] else 0
                        }
                        await self._set_cache(cache_key, result)
                        return result
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
            # Para cash, el precio es siempre 1 (no cache needed really, but consistent interface)
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
