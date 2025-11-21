from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..core.database import get_db
from ..core.middleware import require_auth
from ..models.portfolio import Portfolio
from app.utils.portfolio_utils import get_user_portfolio_or_404
from ..models.transaction import Transaction
from ..models.position import Position
from ..models.asset import Asset
from ..schemas.portfolio import TransactionCreate, TransactionResponse

router = APIRouter(
    prefix="/api/portfolios/{portfolio_id}/transactions", tags=["transactions"]
)


def get_user_portfolio(portfolio_id: UUID, user_id: UUID, db: Session) -> Portfolio:
    """Mantener compatibilidad interna delegando al util compartido"""
    return get_user_portfolio_or_404(db, portfolio_id, user_id)


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    portfolio_id: UUID,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Listar todas las transacciones de una cartera"""
    get_user_portfolio(portfolio_id, UUID(user["user_id"]), db)

    transactions = (
        db.query(Transaction)
        .filter(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )

    return transactions


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    portfolio_id: UUID,
    transaction: TransactionCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Crear una nueva transacción y actualizar posiciones"""
    _ = get_user_portfolio(portfolio_id, UUID(user["user_id"]), db)

    # Verificar que el activo existe
    asset = db.query(Asset).filter(Asset.id == transaction.asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activo no encontrado"
        )

    # Crear la transacción
    db_transaction = Transaction(**transaction.dict(), portfolio_id=portfolio_id)
    db.add(db_transaction)

    # Actualizar o crear posición
    position = (
        db.query(Position)
        .filter(
            Position.portfolio_id == portfolio_id,
            Position.asset_id == transaction.asset_id,
        )
        .first()
    )

    if transaction.transaction_type in ["buy", "deposit"]:
        if position:
            # Actualizar posición existente
            total_cost = (position.quantity * position.average_price) + (
                transaction.quantity * transaction.price
            )
            position.quantity += transaction.quantity
            position.average_price = (
                total_cost / position.quantity if position.quantity > 0 else 0
            )
        else:
            # Crear nueva posición
            position = Position(
                portfolio_id=portfolio_id,
                asset_id=transaction.asset_id,
                quantity=transaction.quantity,
                average_price=transaction.price,
            )
            db.add(position)

    elif transaction.transaction_type == "sell":
        if not position or position.quantity < transaction.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cantidad insuficiente para vender",
            )
        position.quantity -= transaction.quantity

        # Si la cantidad es 0, eliminar la posición
        if position.quantity == 0:
            db.delete(position)

    db.commit()
    db.refresh(db_transaction)
    
    # Trigger snapshot recalculation in background
    from datetime import datetime
    from app.services.snapshot_service import snapshot_service
    
    today = datetime.now().date()
    # Handle naive datetime if necessary, though Pydantic usually handles it
    if transaction.transaction_date:
        if transaction.transaction_date.tzinfo:
            transaction_date = transaction.transaction_date.date()
        else:
            transaction_date = transaction.transaction_date.date()
    else:
        transaction_date = today
        
    # Define the task function to run with a fresh session
    def run_recalculation(pid, start_date, end_date):
        from app.core.database import SessionLocal
        db_bg = SessionLocal()
        try:
            snapshot_service.create_daily_snapshots_for_portfolio(
                db_bg, pid, start_date, end_date, overwrite=True
            )
        finally:
            db_bg.close()
            
    background_tasks.add_task(run_recalculation, portfolio_id, transaction_date, today)

    return db_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    portfolio_id: UUID,
    transaction_id: UUID,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Eliminar una transacción (no revierte posiciones)"""
    get_user_portfolio(portfolio_id, UUID(user["user_id"]), db)

    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id, Transaction.portfolio_id == portfolio_id
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada"
        )

    db.delete(transaction)
    db.commit()
    
    # Trigger snapshot recalculation in background
    from datetime import datetime
    from app.services.snapshot_service import snapshot_service
    
    today = datetime.now().date()
    # Handle naive datetime
    if transaction.transaction_date:
        if transaction.transaction_date.tzinfo:
            transaction_date = transaction.transaction_date.date()
        else:
            transaction_date = transaction.transaction_date.date()
    else:
        transaction_date = today
        
    # Define the task function to run with a fresh session
    def run_recalculation(pid, start_date, end_date):
        from app.core.database import SessionLocal
        db_bg = SessionLocal()
        try:
            snapshot_service.create_daily_snapshots_for_portfolio(
                db_bg, pid, start_date, end_date, overwrite=True
            )
        finally:
            db_bg.close()
            
    background_tasks.add_task(run_recalculation, portfolio_id, transaction_date, today)
    
    return None
