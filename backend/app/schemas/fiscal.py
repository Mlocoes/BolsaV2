from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class FiscalResultItem(BaseModel):
    symbol: str
    date_sell: date
    date_buy: date
    quantity: float
    price_sell: float
    price_buy: float
    result: float

class FiscalResultResponse(BaseModel):
    items: List[FiscalResultItem]
    total_result: float
