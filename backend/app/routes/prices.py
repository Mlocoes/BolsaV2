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
    
    results = []
    for position in positions:
        asset = position.asset
        price_data = await finnhub_service.get_asset_price(asset.symbol, asset.asset_type)
        if price_data:
            current_value = position.quantity * price_data["current_price"]
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
                "current_price": price_data["current_price"],
                "current_value": current_value,
                "cost_basis": cost_basis,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
                "change_percent": price_data["change_percent"]
            })
    
    return results
