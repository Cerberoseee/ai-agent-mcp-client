from pydantic import BaseModel
from typing import Any, List, Optional

class Order(BaseModel):
    order_id: str
    customer_id: str
    products: Any

class AdjustmentSuggestion(BaseModel):
    type: Optional[str]  = ""
    suggested_value: Any = {}

class ApprovalRequest(BaseModel):
    order_id: str
    suggested_adjustments: Optional[List[AdjustmentSuggestion]] = []
    description: Optional[str] = ""