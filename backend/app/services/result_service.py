from typing import List, Optional, Dict
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from uuid import UUID

from app.models.result import Result
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.quote import Quote
from app.models.transaction import Transaction

class ResultService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_portfolio_result(self, portfolio_id: UUID, calculation_date: date = None) -> Result:
        """
        Calcular P&L de un portfolio para una fecha específica
        """
        if calculation_date is None:
            calculation_date = datetime.utcnow().date()

        # 1. Obtener portfolio y posiciones
        portfolio = self.db.get(Portfolio, portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found")

        positions = self.db.scalars(
            select(Position).where(Position.portfolio_id == portfolio_id)
        ).all()

        total_invested = 0.0
        total_current_value = 0.0

        # 2. Calcular valor actual de cada posición
        for pos in positions:
            # Obtener última cotización disponible hasta la fecha de cálculo
            quote = self.db.scalars(
                select(Quote)
                .where(
                    and_(
                        Quote.symbol == pos.asset.symbol,
                        Quote.date <= calculation_date
                    )
                )
                .order_by(Quote.date.desc())
                .limit(1)
            ).first()

            current_price = quote.close if quote else 0.0
            
            # Costo base (promedio ponderado)
            invested = pos.quantity * pos.average_price
            current_val = pos.quantity * current_price

            total_invested += invested
            total_current_value += current_val

        # 3. Calcular P&L
        pnl_absolute = total_current_value - total_invested
        pnl_percent = (pnl_absolute / total_invested * 100) if total_invested > 0 else 0.0

        # 4. Guardar o actualizar Resultado
        # Buscar si ya existe resultado para este día
        existing_result = self.db.scalars(
            select(Result).where(
                and_(
                    Result.portfolio_id == portfolio_id,
                    Result.period_end == calculation_date
                )
            )
        ).first()

        if existing_result:
            result = existing_result
            result.total_invested = total_invested
            result.total_current_value = total_current_value
            result.pnl_absolute = pnl_absolute
            result.pnl_percent = pnl_percent
        else:
            result = Result(
                portfolio_id=portfolio_id,
                period_start=calculation_date, # Simplificación: diario
                period_end=calculation_date,
                total_invested=total_invested,
                total_current_value=total_current_value,
                pnl_absolute=pnl_absolute,
                pnl_percent=pnl_percent
            )
            self.db.add(result)

        self.db.commit()
        self.db.refresh(result)
        return result

    def get_portfolio_history(self, portfolio_id: UUID, days: int = 30) -> List[Result]:
        """Obtener historial de resultados"""
        return self.db.scalars(
            select(Result)
            .where(Result.portfolio_id == portfolio_id)
            .order_by(Result.period_end.desc())
            .limit(days)
        ).all()
