from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..core.database import get_db
from ..core.middleware import require_auth
from ..models.usuario import Usuario
from ..models.portfolio import Portfolio
from ..models.position import Position
from ..models.asset import Asset
from ..schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioDetail

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])

@router.get("/", response_model=List[PortfolioResponse])
async def list_portfolios(
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Listar todos los portfolios del usuario actual"""
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == UUID(user["user_id"])).all()
    return portfolios

@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: PortfolioCreate,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Crear un nuevo portfolio"""
    db_portfolio = Portfolio(
        **portfolio.dict(),
        user_id=UUID(user["user_id"])
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.get("/{portfolio_id}", response_model=PortfolioDetail)
async def get_portfolio(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Obtener un portfolio específico con sus posiciones"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == UUID(user["user_id"])
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return portfolio

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio_update: PortfolioUpdate,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Actualizar un portfolio"""
    db_portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == UUID(user["user_id"])
    ).first()
    
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    update_data = portfolio_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_portfolio, field, value)
    
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Eliminar un portfolio"""
    db_portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == UUID(user["user_id"])
    ).first()
    
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    db.delete(db_portfolio)
    db.commit()
    return None
