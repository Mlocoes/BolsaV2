from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.asset import Asset
from ..schemas.portfolio import AssetCreate, AssetResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Listar todos los assets disponibles"""
    assets = db.query(Asset).offset(skip).limit(limit).all()
    return assets

@router.get("/search", response_model=List[AssetResponse])
async def search_assets(
    q: str,
    db: Session = Depends(get_db)
):
    """Buscar assets por símbolo o nombre"""
    assets = db.query(Asset).filter(
        (Asset.symbol.ilike(f"%{q}%")) | (Asset.name.ilike(f"%{q}%"))
    ).limit(20).all()
    return assets

@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo asset"""
    # Verificar si ya existe
    existing = db.query(Asset).filter(Asset.symbol == asset.symbol).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset with this symbol already exists"
        )
    
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Obtener un asset específico"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    return asset
