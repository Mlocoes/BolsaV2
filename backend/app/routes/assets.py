from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from uuid import UUID
from ..db.session import get_db
from ..models.asset import Asset
from ..schemas.portfolio import AssetCreate, AssetResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("", response_model=List[AssetResponse])
async def list_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Listar todos los assets disponibles"""
    result = db.execute(select(Asset).offset(skip).limit(limit))
    assets = result.scalars().all()
    return assets

@router.get("/search", response_model=List[AssetResponse])
async def search_assets(
    q: str,
    db: Session = Depends(get_db)
):
    """Buscar assets por símbolo o nombre"""
    result = db.execute(
        select(Asset).where(
            (Asset.symbol.ilike(f"%{q}%")) | (Asset.name.ilike(f"%{q}%"))
        ).limit(20)
    )
    assets = result.scalars().all()
    return assets

@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo activo"""
    # Verificar si ya existe
    result = db.execute(select(Asset).where(Asset.symbol == asset.symbol))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un activo con este símbolo"
        )
    
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db)
):
    """Obtener un activo específico"""
    result = db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado"
        )
    return asset
