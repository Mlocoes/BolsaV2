from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from ..db.session import get_db
from ..core.middleware import require_auth
from ..models.usuario import Usuario
from ..models.portfolio import Portfolio
from sqlalchemy.orm import joinedload
from app.utils.portfolio_utils import get_user_portfolio_or_404
from ..models.position import Position
from ..models.asset import Asset
from ..schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioDetail, PositionResponse

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])

@router.get("", response_model=List[PortfolioResponse])
async def list_portfolios(
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Listar todos los portfolios del usuario actual"""
    result = db.execute(
        select(Portfolio).where(Portfolio.user_id == UUID(user["user_id"]))
    )
    portfolios = result.scalars().all()
    return portfolios

@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
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
    """Obtener una cartera específica con sus posiciones"""
    # Cargar posiciones y activos asociados en una sola consulta
    result = db.execute(
        select(Portfolio).options(
            selectinload(Portfolio.positions)
        ).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == UUID(user["user_id"]) 
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartera no encontrada"
        )
    
    return portfolio

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio_update: PortfolioUpdate,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Actualizar una cartera"""
    result = db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == UUID(user["user_id"])
        )
    )
    db_portfolio = result.scalar_one_or_none()
    
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartera no encontrada"
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
    """Eliminar una cartera"""
    result = db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == UUID(user["user_id"])
        )
    )
    db_portfolio = result.scalar_one_or_none()
    
    if not db_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartera no encontrada"
        )
    
    db.delete(db_portfolio)
    db.commit()
    return None

@router.post("/{portfolio_id}/calculate")
async def calculate_portfolio(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Recalcular métricas del portfolio"""
    # Verificar propiedad
    get_user_portfolio_or_404(db, portfolio_id, UUID(user["user_id"]))
    
    from app.services.result_service import ResultService
    service = ResultService(db)
    result = service.calculate_portfolio_result(portfolio_id)
    return result

@router.post("/{portfolio_id}/recalculate_positions")
async def recalculate_portfolio_positions(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Forzar recálculo de todas las posiciones del portfolio"""
    # Verificar propiedad
    get_user_portfolio_or_404(db, portfolio_id, UUID(user["user_id"]))
    
    from app.services.position_service import PositionService
    from app.models.transaction import Transaction
    
    # Obtener todos los assets que tienen transacciones en este portfolio
    asset_ids = db.scalars(
        select(Transaction.asset_id)
        .where(Transaction.portfolio_id == portfolio_id)
        .distinct()
    ).all()
    
    position_service = PositionService(db)
    recalculated_count = 0
    
    for asset_id in asset_ids:
        position_service.recalculate_position(portfolio_id, asset_id)
        recalculated_count += 1
        
    db.commit()
    
    return {"message": f"Se han recalculado {recalculated_count} posiciones correctamente"}

@router.get("/{portfolio_id}/positions", response_model=List[PositionResponse])
async def get_portfolio_positions(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Obtener todas las posiciones del portfolio"""
    # Usar get_portfolio para reutilizar la lógica de carga de relaciones
    # get_portfolio ya carga selectinload(Portfolio.positions)
    portfolio = await get_portfolio(portfolio_id, user, db)
    return portfolio.positions

@router.get("/{portfolio_id}/results")
async def get_portfolio_results(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Obtener historial de resultados"""
    get_user_portfolio_or_404(db, portfolio_id, UUID(user["user_id"]))
    
    from app.services.result_service import ResultService
    service = ResultService(db)
    return service.get_portfolio_history(portfolio_id)
