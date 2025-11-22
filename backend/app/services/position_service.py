from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from uuid import UUID
from typing import List

from app.models.position import Position
from app.models.transaction import Transaction
from app.models.asset import Asset

class PositionService:
    def __init__(self, db: Session):
        self.db = db

    def recalculate_position(self, portfolio_id: UUID, asset_id: UUID) -> Position:
        """
        Recalcula una posición desde cero basándose en todas las transacciones.
        Esto es más robusto que intentar revertir operaciones individuales.
        """
        # 1. Obtener todas las transacciones para este asset y portfolio
        transactions = self.db.scalars(
            select(Transaction)
            .where(
                and_(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.asset_id == asset_id
                )
            )
            .order_by(Transaction.transaction_date.asc()) # Orden cronológico es importante para promedio ponderado
        ).all()

        # 2. Calcular cantidad y precio promedio
        quantity = 0.0
        total_cost = 0.0
        average_price = 0.0

        for tx in transactions:
            tx_qty = float(tx.quantity)
            tx_price = float(tx.price)
            
            if tx.transaction_type in ["buy", "deposit"]:
                # Compra: Aumenta cantidad y costo total
                quantity += tx_qty
                total_cost += (tx_qty * tx_price)
            
            elif tx.transaction_type in ["sell", "withdrawal"]:
                # Venta: Disminuye cantidad
                # Asumimos FIFO o promedio ponderado para la salida?
                # En contabilidad simple de cartera, al vender se reduce la cantidad
                # pero el precio promedio de compra unitario NO cambia.
                # Solo cambia el total_cost proporcionalmente.
                if quantity > 0:
                    # Reducir costo total proporcionalmente a la cantidad vendida
                    cost_of_sold = (tx_qty / quantity) * total_cost
                    total_cost -= cost_of_sold
                    quantity -= tx_qty
                else:
                    # Venta en corto o error de datos, por ahora permitimos negativo pero costo 0?
                    quantity -= tx_qty
            
            # Recalcular precio promedio
            if quantity > 0:
                average_price = total_cost / quantity
            else:
                average_price = 0.0
                total_cost = 0.0

        # 3. Actualizar o crear la posición en BD
        position = self.db.scalars(
            select(Position).where(
                and_(
                    Position.portfolio_id == portfolio_id,
                    Position.asset_id == asset_id
                )
            )
        ).first()

        if quantity == 0 and position:
            # Si la cantidad es 0, eliminamos la posición
            self.db.delete(position)
            return None
        
        if quantity != 0:
            if not position:
                position = Position(
                    portfolio_id=portfolio_id,
                    asset_id=asset_id
                )
                self.db.add(position)
            
            position.quantity = quantity
            position.average_price = average_price
            
            # Asegurar que se guarde
            self.db.flush()
            
        return position

    def update_position_from_transaction(self, transaction: Transaction):
        """Wrapper conveniente para actualizar posición tras una transacción"""
        return self.recalculate_position(transaction.portfolio_id, transaction.asset_id)
