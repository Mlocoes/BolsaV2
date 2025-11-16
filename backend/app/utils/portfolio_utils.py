from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.portfolio import Portfolio


def get_user_portfolio_or_404(db: Session, portfolio_id: UUID, user_id: UUID) -> Portfolio:
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cartera no encontrada"
        )
    return portfolio
