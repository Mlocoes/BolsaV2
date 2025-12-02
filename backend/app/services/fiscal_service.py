from typing import List, Dict, Deque, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from uuid import UUID
from collections import deque

from app.models.transaction import Transaction, TransactionType
from app.schemas.fiscal import FiscalResultItem, FiscalResultResponse

class FiscalService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_fiscal_result(
        self, 
        portfolio_id: UUID, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> FiscalResultResponse:
        """
        Calcula el resultado fiscal usando el método FIFO.
        """
        # 1. Obtener todas las transacciones ordenadas por fecha
        transactions = self.db.scalars(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date)
        ).all()

        # Cola de compras por símbolo: {symbol: deque([ {'date': ..., 'qty': ..., 'price': ...} ])}
        buy_queues: Dict[str, Deque[dict]] = {}
        results: List[FiscalResultItem] = []
        total_result = 0.0

        for tx in transactions:
            symbol = tx.asset.symbol if tx.asset else "UNKNOWN"
            
            if symbol not in buy_queues:
                buy_queues[symbol] = deque()

            if tx.transaction_type == TransactionType.BUY:
                # Añadir a la cola de compras
                buy_queues[symbol].append({
                    'date': tx.transaction_date,
                    'quantity': tx.quantity,
                    'price': tx.price
                })
            
            elif tx.transaction_type == TransactionType.SELL:
                qty_to_sell = tx.quantity
                
                # Procesar venta contra la cola de compras (FIFO)
                while qty_to_sell > 0 and buy_queues[symbol]:
                    oldest_buy = buy_queues[symbol][0]
                    
                    match_qty = min(qty_to_sell, oldest_buy['quantity'])
                    
                    # Calcular resultado para esta porción
                    # Resultado = (Precio Venta - Precio Compra) * Cantidad
                    pnl = (tx.price - oldest_buy['price']) * match_qty
                    
                    # Crear registro de resultado
                    # Solo añadimos si está dentro del rango de fechas solicitado (si se especificó)
                    tx_date = tx.transaction_date.date() if isinstance(tx.transaction_date, datetime) else tx.transaction_date
                    
                    in_range = True
                    if start_date and tx_date < start_date:
                        in_range = False
                    if end_date and tx_date > end_date:
                        in_range = False
                        
                    if in_range:
                        results.append(FiscalResultItem(
                            symbol=symbol,
                            date_sell=tx_date,
                            date_buy=oldest_buy['date'].date() if isinstance(oldest_buy['date'], datetime) else oldest_buy['date'],
                            quantity=match_qty,
                            price_sell=tx.price,
                            price_buy=oldest_buy['price'],
                            result=pnl
                        ))
                        total_result += pnl

                    # Actualizar cantidades
                    qty_to_sell -= match_qty
                    oldest_buy['quantity'] -= match_qty
                    
                    # Si la compra se agotó, quitarla de la cola
                    if oldest_buy['quantity'] <= 0.000001: # Usar epsilon para float
                        buy_queues[symbol].popleft()
                
                # Si todavía queda cantidad por vender pero no hay compras (Short selling o error de datos)
                # Por ahora lo ignoramos o podríamos registrar un error. 
                # El requerimiento dice "Validar que no se vendan más acciones de las disponibles"
                # Aquí simplemente no generamos resultado fiscal para la parte no cubierta.

        return FiscalResultResponse(items=results, total_result=total_result)
