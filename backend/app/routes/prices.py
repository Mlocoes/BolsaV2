"""
Rutas para obtener precios de activos en tiempo real
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict
from uuid import UUID
from ..db.session import get_db
from ..models.asset import Asset
from ..services.finnhub_service import finnhub_service

router = APIRouter(prefix="/api/prices", tags=["prices"])

@router.get("/{symbol}")
async def get_asset_price(symbol: str, db: Session = Depends(get_db)):
    """Obtener precio actual de un activo por su símbolo"""
    # Buscar el asset en la base de datos
    result = db.execute(
        select(Asset).where(Asset.symbol == symbol.upper())
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado")
    
    # Obtener precio desde Finnhub
    price_data = await finnhub_service.get_asset_price(asset.symbol, asset.asset_type)
    if not price_data:
        raise HTTPException(status_code=503, detail="No se pudo obtener el precio del activo")
    
    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "currency": asset.currency,
        **price_data
    }

@router.get("")
async def get_multiple_prices(symbols: str, db: Session = Depends(get_db)):
    """
    Obtener precios de múltiples activos
    Parámetro symbols: lista de símbolos separados por coma (ej: AAPL,GOOGL,BTC)
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    # Buscar assets en la base de datos
    result = db.execute(
        select(Asset).where(Asset.symbol.in_(symbol_list))
    )
    assets = result.scalars().all()
    
    if not assets:
        raise HTTPException(status_code=404, detail="No se encontraron assets")
    
    results = []
    for asset in assets:
        price_data = await finnhub_service.get_asset_price(asset.symbol, asset.asset_type)
        if price_data:
            results.append({
                "id": asset.id,
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "currency": asset.currency,
                **price_data
            })
    
    return results

@router.get("/portfolio/{portfolio_id}")
async def get_portfolio_prices(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Obtener precios actuales de todos los activos en un portfolio"""
    from ..models.position import Position
    from sqlalchemy.orm import selectinload
    
    result = db.execute(
        select(Position).options(
            selectinload(Position.asset)
        ).where(
            Position.portfolio_id == portfolio_id,
            Position.quantity > 0
        )
    )
    positions = result.scalars().all()
    
    if not positions:
        return []

    import asyncio

    # Semáforo para limitar concurrencia y respetar rate limits de Finnhub
    # Free tier: 60 req/min. Con 5 concurrentes evitamos picos agresivos.
    semaphore = asyncio.Semaphore(10)

    async def fetch_price_safely(position):
        async with semaphore:
            try:
                asset = position.asset
                price = await finnhub_service.get_asset_price(asset.symbol, asset.asset_type)
                return position, price
            except Exception:
                return position, None

    
    # Pre-fetch latest quotes from DB for all assets in portfolio to optimize fallback
    from ..models.quote import Quote
    from sqlalchemy import func
    
    asset_ids = [p.asset_id for p in positions]
    
    # Subquery to find max timestamp per asset
    subquery = (
        db.query(Quote.asset_id, func.max(Quote.timestamp).label("max_ts"))
        .filter(Quote.asset_id.in_(asset_ids))
        .group_by(Quote.asset_id)
        .subquery()
    )
    
    # Query to get the full quote rows
    latest_quotes_query = (
        db.query(Quote)
        .join(subquery, (Quote.asset_id == subquery.c.asset_id) & (Quote.timestamp == subquery.c.max_ts))
    )
    
    latest_quotes_map = {q.asset_id: q for q in latest_quotes_query.all()}
    
    tasks = [fetch_price_safely(p) for p in positions]
    results_pairs = await asyncio.gather(*tasks)
    
    results = []
    for position, price_data in results_pairs:
        asset = position.asset
        print(f"DEBUG: Processing {asset.symbol}, Price Data: {price_data is not None}")
        
        if price_data:
            current_price = price_data["current_price"]
            change_percent = price_data["change_percent"]
            
            # Actualizar precio en BD para persistencia
            asset.last_price = current_price
            from datetime import datetime
            asset.last_price_updated_at = datetime.utcnow()
            
        else:
            # Fallback 1: Usar último precio conocido en columna Asset
            if asset.last_price is not None:
                current_price = asset.last_price
                change_percent = 0.0 
                print(f"DEBUG: Using Asset.last_price for {asset.symbol}: {current_price}")
            
            # Fallback 2: Usar última cotización en tabla Quotes (Histórico)
            elif asset.id in latest_quotes_map:
                quote = latest_quotes_map[asset.id]
                current_price = float(quote.close)
                # Intentar calcular cambio con el open del mismo día si es posible, o 0
                day_open = float(quote.open) if quote.open else current_price
                change_percent = ((current_price - day_open) / day_open * 100) if day_open else 0.0
                print(f"DEBUG: Using Quote history for {asset.symbol}: {current_price}")
                
            # Fallback 3: Usar precio promedio de compra
            else:
                current_price = position.average_price
                change_percent = 0.0
                print(f"DEBUG: Using avg_price fallback for {asset.symbol}: {current_price}")

        current_value = position.quantity * current_price
        cost_basis = position.quantity * position.average_price
        profit_loss = current_value - cost_basis
        profit_loss_percent = (profit_loss / cost_basis * 100) if cost_basis else 0
        
        results.append({
            "position_id": position.id,
            "asset_id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "quantity": position.quantity,
            "average_price": position.average_price,
            "current_price": current_price,
            "current_value": current_value,
            "cost_basis": cost_basis,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_percent,
            "change_percent": change_percent
        })
    
    try:
        db.commit()
    except Exception as e:
        print(f"ERROR: Failed to commit price updates: {e}")
        db.rollback()
        
    print(f"DEBUG: Returning {len(results)} results")
    return results
