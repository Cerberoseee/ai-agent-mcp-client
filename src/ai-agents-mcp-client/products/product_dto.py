from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ProductRequest(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None

class ProductFeature(BaseModel):
    feature: str
    relevance: float
    explanation: str

class ProductResponse(BaseModel):
    category_name: str
    category_confidence: float
    features: List[ProductFeature]
    reasoning_chain: List[str]
    final_explanation: str

class ProductPerformanceRequest(BaseModel):
    productId: str
    performanceChange: float
    productDetails: Dict[str, Any]

class AdjustmentSuggestion(BaseModel):
    type: str  # e.g., "price", "description", "promotion"
    current_value: Any
    suggested_value: Any
    reasoning: str
    confidence: float
    priority: int

class ProductPerformanceAnalysis(BaseModel):
    product_id: str
    performance_change: float
    market_analysis: str
    suggested_adjustments: List[AdjustmentSuggestion]
    analysis_summary: str

class ApprovalRequest(BaseModel):
    analysis_id: str
    product_id: str
    suggested_adjustments: List[AdjustmentSuggestion]
    approval_status: Optional[str] = "pending"  # pending, approved, rejected
    approval_notes: Optional[str] = None