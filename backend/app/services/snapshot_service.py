"""
Portfolio Snapshot Service - Daily portfolio state capture
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import Session

# Correct imports matching the rest of the application
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction, TransactionType
from app.models.asset import Asset
from app.models.quote import Quote
from app.db.models_snapshots import PortfolioSnapshot, PositionSnapshot, SnapshotMetrics


class SnapshotService:
    """Service for creating and managing portfolio snapshots"""

    @staticmethod
    def calculate_portfolio_state(
        db: Session,
        portfolio_id: UUID,
        target_date: date
    ) -> Dict:
        """
        Calculate portfolio state for a specific date
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            target_date: Date to calculate state for
            
        Returns:
            Dictionary with portfolio state
        """
        # Get all transactions up to target date
        result = db.execute(
            select(Transaction, Asset)
            .join(Asset, Transaction.asset_id == Asset.id)
            .where(
                and_(
                    Transaction.portfolio_id == portfolio_id,
                    func.date(Transaction.transaction_date) <= target_date
                )
            )
            .order_by(Transaction.transaction_date)
        )
        transactions = result.all()

        # Calculate positions
        positions = {}
        total_invested = Decimal("0")
        
        for transaction, asset in transactions:
            asset_id = str(transaction.asset_id)
            
            if asset_id not in positions:
                positions[asset_id] = {
                    "asset": asset,
                    "quantity": Decimal("0"),
                    "total_cost": Decimal("0"),
                    "operations": []
                }
            
            pos = positions[asset_id]
            
            # Convert float to Decimal for calculation
            qty = Decimal(str(transaction.quantity))
            price = Decimal(str(transaction.price))
            fees = Decimal(str(transaction.fees or 0))
            
            if transaction.transaction_type == TransactionType.BUY:
                pos["quantity"] += qty
                cost = (qty * price) + fees
                pos["total_cost"] += cost
                total_invested += cost
            elif transaction.transaction_type == TransactionType.SELL:
                # Calculate proportion being sold
                if pos["quantity"] > 0:
                    sell_proportion = qty / pos["quantity"]
                    cost_reduction = pos["total_cost"] * sell_proportion
                    pos["total_cost"] -= cost_reduction
                    total_invested -= cost_reduction
                
                pos["quantity"] -= qty
            # Handle other types if necessary (DEPOSIT/WITHDRAWAL usually affect cash, not positions directly unless it's crypto/asset transfer)
            
            pos["operations"].append(transaction)

        # Filter active positions
        active_positions = {
            k: v for k, v in positions.items()
            if v["quantity"] > Decimal("0")
        }

        # Get quotes for target date (or closest previous)
        position_details = []
        total_value = Decimal("0")
        
        for asset_id, pos_data in active_positions.items():
            asset = pos_data["asset"]
            quantity = pos_data["quantity"]
            total_cost = pos_data["total_cost"]
            
            # Get quote for target date or most recent before
            # Using correct columns: asset_id and timestamp
            quote_result = db.execute(
                select(Quote)
                .where(
                    and_(
                        Quote.asset_id == asset.id,
                        func.date(Quote.timestamp) <= target_date
                    )
                )
                .order_by(desc(Quote.timestamp))
                .limit(1)
            )
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                # No quote available, use average cost as fallback or 0?
                # Using average cost implies no PnL, which is safer than 0 value
                current_price = total_cost / quantity if quantity > 0 else Decimal("0")
            else:
                current_price = Decimal(str(quote.close))
            
            avg_buy_price = total_cost / quantity if quantity > 0 else Decimal("0")
            current_value = quantity * current_price
            position_pnl = current_value - total_cost
            position_pnl_percent = (position_pnl / total_cost * 100) if total_cost > 0 else Decimal("0")
            
            total_value += current_value
            
            position_details.append({
                "asset_id": UUID(asset_id),
                "ticker": asset.symbol,
                "asset_name": asset.name,
                "quantity": quantity,
                "average_buy_price": avg_buy_price,
                "current_price": current_price,
                "total_cost": total_cost,
                "current_value": current_value,
                "position_pnl": position_pnl,
                "position_pnl_percent": position_pnl_percent,
            })

        # Calculate portfolio metrics
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else Decimal("0")

        return {
            "portfolio_id": portfolio_id,
            "snapshot_date": target_date,
            "total_invested": total_invested,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "number_of_positions": len(position_details),
            "number_of_assets": len(active_positions),
            "positions": position_details
        }

    @staticmethod
    def create_snapshot(
        db: Session,
        portfolio_id: UUID,
        target_date: date,
        overwrite: bool = False
    ) -> PortfolioSnapshot:
        """
        Create a snapshot for a specific date
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            target_date: Date for snapshot
            overwrite: Whether to overwrite if exists
            
        Returns:
            Created PortfolioSnapshot
        """
        # Check if snapshot already exists
        existing = db.execute(
            select(PortfolioSnapshot).where(
                and_(
                    PortfolioSnapshot.portfolio_id == portfolio_id,
                    PortfolioSnapshot.snapshot_date == target_date
                )
            )
        )
        existing_snapshot = existing.scalar_one_or_none()
        
        if existing_snapshot:
            if not overwrite:
                raise ValueError(f"Snapshot already exists for {target_date}")
            else:
                # Delete existing snapshot (cascade handles positions)
                db.delete(existing_snapshot)
                db.flush()

        # Calculate portfolio state
        state = SnapshotService.calculate_portfolio_state(
            db, portfolio_id, target_date
        )

        # Get previous snapshot for daily change
        prev_snapshot = db.execute(
            select(PortfolioSnapshot)
            .where(
                and_(
                    PortfolioSnapshot.portfolio_id == portfolio_id,
                    PortfolioSnapshot.snapshot_date < target_date
                )
            )
            .order_by(desc(PortfolioSnapshot.snapshot_date))
            .limit(1)
        )
        prev = prev_snapshot.scalar_one_or_none()

        if prev:
            daily_pnl = state["total_value"] - prev.total_value
            daily_pnl_percent = (daily_pnl / prev.total_value * 100) if prev.total_value > 0 else Decimal("0")
        else:
            daily_pnl = Decimal("0")
            daily_pnl_percent = Decimal("0")

        # Create portfolio snapshot
        portfolio_snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            snapshot_date=target_date,
            total_invested=state["total_invested"],
            total_value=state["total_value"],
            cash_balance=Decimal("0"),  # TODO: Implement cash tracking
            daily_pnl=daily_pnl,
            daily_pnl_percent=daily_pnl_percent,
            total_pnl=state["total_pnl"],
            total_pnl_percent=state["total_pnl_percent"],
            number_of_positions=state["number_of_positions"],
            number_of_assets=state["number_of_assets"]
        )
        
        db.add(portfolio_snapshot)
        db.flush()

        # Create position snapshots
        for position in state["positions"]:
            # Get previous position for daily change
            prev_position_result = db.execute(
                select(PositionSnapshot)
                .join(PortfolioSnapshot)
                .where(
                    and_(
                        PortfolioSnapshot.portfolio_id == portfolio_id,
                        PositionSnapshot.asset_id == position["asset_id"],
                        PositionSnapshot.snapshot_date < target_date
                    )
                )
                .order_by(desc(PositionSnapshot.snapshot_date))
                .limit(1)
            )
            prev_position = prev_position_result.scalar_one_or_none()

            if prev_position:
                daily_change = position["current_value"] - prev_position.current_value
                daily_change_percent = (
                    daily_change / prev_position.current_value * 100
                ) if prev_position.current_value > 0 else Decimal("0")
            else:
                daily_change = Decimal("0")
                daily_change_percent = Decimal("0")

            # Calculate portfolio weight
            portfolio_weight = (
                position["current_value"] / state["total_value"] * 100
            ) if state["total_value"] > 0 else Decimal("0")

            position_snapshot = PositionSnapshot(
                portfolio_snapshot_id=portfolio_snapshot.id,
                asset_id=position["asset_id"],
                snapshot_date=target_date,
                ticker=position["ticker"],
                quantity=position["quantity"],
                average_buy_price=position["average_buy_price"],
                current_price=position["current_price"],
                total_cost=position["total_cost"],
                current_value=position["current_value"],
                position_pnl=position["position_pnl"],
                position_pnl_percent=position["position_pnl_percent"],
                daily_change=daily_change,
                daily_change_percent=daily_change_percent,
                portfolio_weight=portfolio_weight
            )
            
            db.add(position_snapshot)

        db.commit()
        db.refresh(portfolio_snapshot)

        return portfolio_snapshot

    @staticmethod
    def create_daily_snapshots_for_portfolio(
        db: Session,
        portfolio_id: UUID,
        from_date: date,
        to_date: date,
        overwrite: bool = False
    ) -> Dict:
        """
        Create snapshots for a date range
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            from_date: Start date
            to_date: End date
            overwrite: Whether to overwrite existing snapshots
            
        Returns:
            Summary of created snapshots
        """
        created = 0
        skipped = 0
        errors = []

        current_date = from_date
        while current_date <= to_date:
            try:
                SnapshotService.create_snapshot(db, portfolio_id, current_date, overwrite)
                created += 1
            except ValueError as e:
                # Snapshot already exists
                skipped += 1
            except Exception as e:
                errors.append({
                    "date": current_date.isoformat(),
                    "error": str(e)
                })
            
            current_date += timedelta(days=1)

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "total_days": (to_date - from_date).days + 1
        }

    @staticmethod
    def get_snapshot_history(
        db: Session,
        portfolio_id: UUID,
        from_date: date,
        to_date: date,
        include_positions: bool = False
    ) -> List[Dict]:
        """
        Get snapshot history for a portfolio
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            from_date: Start date
            to_date: End date
            include_positions: Include position details
            
        Returns:
            List of snapshots
        """
        # Get snapshots
        result = db.execute(
            select(PortfolioSnapshot)
            .where(
                and_(
                    PortfolioSnapshot.portfolio_id == portfolio_id,
                    PortfolioSnapshot.snapshot_date >= from_date,
                    PortfolioSnapshot.snapshot_date <= to_date
                )
            )
            .order_by(PortfolioSnapshot.snapshot_date)
        )
        snapshots = result.scalars().all()

        history = []
        for snapshot in snapshots:
            snapshot_dict = {
                "id": str(snapshot.id),
                "date": snapshot.snapshot_date.isoformat(),
                "total_invested": float(snapshot.total_invested),
                "total_value": float(snapshot.total_value),
                "daily_pnl": float(snapshot.daily_pnl),
                "daily_pnl_percent": float(snapshot.daily_pnl_percent),
                "total_pnl": float(snapshot.total_pnl),
                "total_pnl_percent": float(snapshot.total_pnl_percent),
                "number_of_positions": int(snapshot.number_of_positions),
                "number_of_assets": int(snapshot.number_of_assets),
            }

            if include_positions:
                # Get positions for this snapshot
                positions_result = db.execute(
                    select(PositionSnapshot, Asset)
                    .join(Asset, PositionSnapshot.asset_id == Asset.id)
                    .where(PositionSnapshot.portfolio_snapshot_id == snapshot.id)
                    .order_by(desc(PositionSnapshot.current_value))
                )
                positions_with_assets = positions_result.all()

                snapshot_dict["positions"] = [
                    {
                        "symbol": pos.ticker,
                        "name": asset.name or pos.ticker,
                        "asset_type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else "STOCK",
                        "quantity": float(pos.quantity),
                        "average_price": float(pos.average_buy_price),
                        "current_price": float(pos.current_price),
                        "current_value": float(pos.current_value),
                        "cost_basis": float(pos.total_cost),
                        "profit_loss": float(pos.position_pnl),
                        "profit_loss_percent": float(pos.position_pnl_percent),
                        "daily_change_percent": float(pos.daily_change_percent),
                        "portfolio_weight": float(pos.portfolio_weight),
                    }
                    for pos, asset in positions_with_assets
                ]

            history.append(snapshot_dict)

        return history


# Global instance
snapshot_service = SnapshotService()
snapshot_service = SnapshotService()