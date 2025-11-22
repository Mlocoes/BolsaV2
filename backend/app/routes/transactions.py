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
from ..schemas.portfolio import TransactionCreate, TransactionResponse, TransactionBatchUpdate

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

    # Actualizar posición usando PositionService (más robusto)
    from app.services.position_service import PositionService
    position_service = PositionService(db)
    position_service.recalculate_position(portfolio_id, transaction.asset_id)

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

    # Guardar asset_id antes de borrar para recalcular
    asset_id = transaction.asset_id
    
    db.delete(transaction)
    db.commit()
    
    # Recalcular posición
    from app.services.position_service import PositionService
    position_service = PositionService(db)
    position_service.recalculate_position(portfolio_id, asset_id)
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

@router.put("/batch", status_code=status.HTTP_200_OK)
async def update_transactions_batch(
    portfolio_id: UUID,
    batch_update: TransactionBatchUpdate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Actualizar múltiples transacciones en lote"""
    get_user_portfolio(portfolio_id, UUID(user["user_id"]), db)
    
    affected_assets = set()
    min_date = None
    
    for tx_update in batch_update.transactions:
        transaction = db.query(Transaction).filter(
            Transaction.id == tx_update.id,
            Transaction.portfolio_id == portfolio_id
        ).first()
        
        if not transaction:
            continue
            
        # Update fields
        if tx_update.asset_id:
            affected_assets.add(transaction.asset_id) # Old asset
            transaction.asset_id = tx_update.asset_id
            affected_assets.add(tx_update.asset_id) # New asset
        else:
            affected_assets.add(transaction.asset_id)
            
        if tx_update.transaction_type:
            transaction.transaction_type = tx_update.transaction_type
        if tx_update.quantity is not None:
            transaction.quantity = tx_update.quantity
        if tx_update.price is not None:
            transaction.price = tx_update.price
        if tx_update.fees is not None:
            transaction.fees = tx_update.fees
        if tx_update.currency:
            transaction.currency = tx_update.currency
        if tx_update.notes is not None:
            transaction.notes = tx_update.notes
        if tx_update.transaction_date:
            transaction.transaction_date = tx_update.transaction_date
            
        # Track min date for snapshot recalc
        # Handle naive/aware datetime
        tx_date = transaction.transaction_date
        if tx_date.tzinfo:
            tx_date = tx_date.date()
        else:
            tx_date = tx_date.date()
            
        if min_date is None or tx_date < min_date:
            min_date = tx_date
            
    db.commit()
    
    # Recalculate positions
    from app.services.position_service import PositionService
    position_service = PositionService(db)
    for asset_id in affected_assets:
        position_service.recalculate_position(portfolio_id, asset_id)
        
    db.commit()
    
    # Trigger snapshot recalculation
    if min_date:
        from datetime import datetime
        from app.services.snapshot_service import snapshot_service
        today = datetime.now().date()
        
        def run_recalculation(pid, start_date, end_date):
            from app.core.database import SessionLocal
            db_bg = SessionLocal()
            try:
                snapshot_service.create_daily_snapshots_for_portfolio(
                    db_bg, pid, start_date, end_date, overwrite=True
                )
            finally:
                db_bg.close()
                
        background_tasks.add_task(run_recalculation, portfolio_id, min_date, today)
        
    return {"message": "Transacciones actualizadas correctamente"}
