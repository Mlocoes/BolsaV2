from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.core.middleware import require_auth
from app.utils.portfolio_utils import get_user_portfolio_or_404
from app.services.fiscal_service import FiscalService
from app.schemas.fiscal import FiscalResultResponse

router = APIRouter(
    prefix="/api/fiscal",
    tags=["fiscal"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{portfolio_id}", response_model=FiscalResultResponse)
def get_fiscal_results(
    portfolio_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    # Verify ownership
    get_user_portfolio_or_404(db, portfolio_id, UUID(user["user_id"]))
    
    service = FiscalService(db)
    return service.calculate_fiscal_result(portfolio_id, start_date, end_date)
