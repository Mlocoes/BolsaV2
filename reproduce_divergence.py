
from dataclasses import dataclass
from typing import List

@dataclass
class MockTransaction:
    transaction_type: str
    quantity: float
    price: float
    transaction_date: str

def recalculate_position_logic(transactions: List[MockTransaction]):
    quantity = 0.0
    total_cost = 0.0
    average_price = 0.0

    print(f"{'Type':<10} {'Qty':<10} {'Price':<10} | {'CurQty':<10} {'CurCost':<10} {'AvgPrice':<10}")
    print("-" * 70)

    for tx in transactions:
        tx_qty = float(tx.quantity)
        tx_price = float(tx.price)
        
        if tx.transaction_type in ["buy", "deposit"]:
            quantity += tx_qty
            total_cost += (tx_qty * tx_price)
        
        elif tx.transaction_type in ["sell", "withdrawal"]:
            if quantity > 0:
                cost_of_sold = (tx_qty / quantity) * total_cost
                total_cost -= cost_of_sold
                quantity -= tx_qty
            else:
                quantity -= tx_qty
        
        if quantity > 0:
            average_price = total_cost / quantity
        else:
            average_price = 0.0
            total_cost = 0.0
            
        print(f"{tx.transaction_type:<10} {tx_qty:<10.4f} {tx_price:<10.4f} | {quantity:<10.6f} {total_cost:<10.4f} {average_price:<10.4f}")

    return quantity, average_price

# Scenario 1: Simple Buy and Sell to 0
print("\nScenario 1: Simple Buy and Sell to 0")
txs1 = [
    MockTransaction("buy", 10.0, 100.0, "2023-01-01"),
    MockTransaction("sell", 10.0, 120.0, "2023-01-02")
]
recalculate_position_logic(txs1)

# Scenario 2: Buy, Partial Sell, Sell Remainder
print("\nScenario 2: Buy, Partial Sell, Sell Remainder")
txs2 = [
    MockTransaction("buy", 10.0, 100.0, "2023-01-01"),
    MockTransaction("sell", 5.0, 120.0, "2023-01-02"),
    MockTransaction("sell", 5.0, 110.0, "2023-01-03")
]
recalculate_position_logic(txs2)

# Scenario 3: Floating point precision (0.1 + 0.2)
print("\nScenario 3: Floating point precision")
txs3 = [
    MockTransaction("buy", 0.1, 100.0, "2023-01-01"),
    MockTransaction("buy", 0.2, 100.0, "2023-01-02"),
    MockTransaction("sell", 0.3, 100.0, "2023-01-03")
]
recalculate_position_logic(txs3)

# Scenario 4: Complex fractional shares
print("\nScenario 4: Complex fractional shares")
txs4 = [
    MockTransaction("buy", 1.234567, 100.0, "2023-01-01"),
    MockTransaction("sell", 1.234567, 110.0, "2023-01-02")
]
recalculate_position_logic(txs4)
