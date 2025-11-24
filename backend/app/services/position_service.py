from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from uuid import UUID
from typing import List
from decimal import Decimal, getcontext

from app.models.position import Position
from app.models.transaction import Transaction
from app.models.asset import Asset

# Configurar precisión de Decimal si es necesario, por defecto es suficiente (28 dígitos)
# getcontext().prec = 28

class PositionService:
    def __init__(self, db: Session):
        self.db = db

    def recalculate_position(self, portfolio_id: UUID, asset_id: UUID) -> Position:
        """
        Recalcula una posición desde cero basándose en todas las transacciones.
        Usa Decimal para evitar errores de punto flotante.
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

        # 2. Calcular cantidad y precio promedio usando Decimal
        quantity = Decimal('0.0')
        total_cost = Decimal('0.0')
        average_price = Decimal('0.0')

        for tx in transactions:
            # Convertir a string primero para preservar precisión al crear Decimal
            tx_qty = Decimal(str(tx.quantity))
            tx_price = Decimal(str(tx.price))
            
            if tx.transaction_type in ["buy", "deposit"]:
                # Compra: Aumenta cantidad y costo total
                quantity += tx_qty
                total_cost += (tx_qty * tx_price)
            
            elif tx.transaction_type in ["sell", "withdrawal"]:
                # Venta: Disminuye cantidad
                if quantity > Decimal('0'):
                    # Reducir costo total proporcionalmente a la cantidad vendida
                    # cost_of_sold = (tx_qty / quantity) * total_cost
                    # total_cost -= cost_of_sold
                    
                    # Simplificación matemática:
                    # Nuevo total_cost = total_cost * (1 - tx_qty/quantity)
                    #                  = total_cost * ((quantity - tx_qty) / quantity)
                    remaining_ratio = (quantity - tx_qty) / quantity
                    total_cost = total_cost * remaining_ratio
                    
                    quantity -= tx_qty
                else:
                    # Venta en corto o error de datos
                    quantity -= tx_qty
            
            # Recalcular precio promedio
            if quantity > Decimal('0'):
                average_price = total_cost / quantity
            else:
                average_price = Decimal('0.0')
                total_cost = Decimal('0.0')

        # 3. Validar cercanía a cero (epsilon check)
        # Si la cantidad es muy pequeña (ej. < 1e-9), asumimos 0 para limpiar residuos
        if abs(quantity) < Decimal('1e-9'):
            quantity = Decimal('0.0')
            total_cost = Decimal('0.0')
            average_price = Decimal('0.0')

        # 4. Actualizar o crear la posición en BD
        position = self.db.scalars(
            select(Position).where(
                and_(
                    Position.portfolio_id == portfolio_id,
                    Position.asset_id == asset_id
                )
            )
        ).first()

        if quantity == Decimal('0') and position:
            # Si la cantidad es 0, eliminamos la posición
            self.db.delete(position)
            return None
        
        if quantity != Decimal('0'):
            if not position:
                position = Position(
                    portfolio_id=portfolio_id,
                    asset_id=asset_id
                )
                self.db.add(position)
            
            # Convertir de vuelta a float para la BD
            position.quantity = float(quantity)
            position.average_price = float(average_price)
            
            # Asegurar que se guarde
            self.db.flush()
            
        return position

    def update_position_from_transaction(self, transaction: Transaction):
        """Wrapper conveniente para actualizar posición tras una transacción"""
        return self.recalculate_position(transaction.portfolio_id, transaction.asset_id)
