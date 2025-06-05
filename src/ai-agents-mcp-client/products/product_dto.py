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
    type: str 
    current_value: Any
    suggested_value: Any

class AnalysisResponse(BaseModel):
    analysis: str
    suggested_adjustments: List[AdjustmentSuggestion]

class ApprovalRequest(BaseModel):
    product_id: str
    suggested_adjustments: List[AdjustmentSuggestion]

class LaunchPlanResponse(BaseModel):
    """Response model for new product launch plan"""
    product_id: str
    opportunity_score: float
    recommendation: str
    launch_price: float
    initial_inventory: int
    expected_roi: float
    marketing_content: Dict[str, Any]
    launch_timeline_days: int