
from dataclasses import dataclass
from typing import List
from decimal import Decimal

@dataclass
class MockTransaction:
    transaction_type: str
    quantity: float
    price: float
    transaction_date: str

def recalculate_position_logic_decimal(transactions: List[MockTransaction]):
    # Logic copied and adapted from PositionService.recalculate_position
    quantity = Decimal('0.0')
    total_cost = Decimal('0.0')
    average_price = Decimal('0.0')

    print(f"{'Type':<10} {'Qty':<10} {'Price':<10} | {'CurQty':<10} {'CurCost':<10} {'AvgPrice':<10}")
    print("-" * 70)

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
            
        print(f"{tx.transaction_type:<10} {tx_qty:<10.4f} {tx_price:<10.4f} | {quantity:<10.6f} {total_cost:<10.4f} {average_price:<10.4f}")

    # Validar cercanía a cero (epsilon check)
    if abs(quantity) < Decimal('1e-9'):
        quantity = Decimal('0.0')
        total_cost = Decimal('0.0')
        average_price = Decimal('0.0')

    return quantity, average_price

# Scenario 3: Floating point precision (0.1 + 0.2)
print("\nScenario 3: Floating point precision (Decimal)")
txs3 = [
    MockTransaction("buy", 0.1, 100.0, "2023-01-01"),
    MockTransaction("buy", 0.2, 100.0, "2023-01-02"),
    MockTransaction("sell", 0.3, 100.0, "2023-01-03")
]
recalculate_position_logic_decimal(txs3)

# Scenario 4: Complex fractional shares
print("\nScenario 4: Complex fractional shares (Decimal)")
txs4 = [
    MockTransaction("buy", 1.234567, 100.0, "2023-01-01"),
    MockTransaction("sell", 1.234567, 110.0, "2023-01-02")
]
recalculate_position_logic_decimal(txs4)
