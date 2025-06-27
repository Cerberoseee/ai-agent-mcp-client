from pydantic import BaseModel
from typing import Any, List

class Order(BaseModel):
    order_id: str

class AdjustmentSuggestion(BaseModel):
    type: str 
    suggested_value: Any

class ApprovalRequest(BaseModel):
    order_id: str
    suggested_adjustments: List[AdjustmentSuggestion]