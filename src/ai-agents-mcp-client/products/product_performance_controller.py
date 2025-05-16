from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from .product_dto import ProductPerformanceRequest, ProductPerformanceAnalysis, ApprovalRequest
from .product_performance_service import ProductPerformanceService
from core.client_manager import ClientManager

router = APIRouter()

def get_performance_service() -> ProductPerformanceService:
    return ProductPerformanceService(ClientManager.get_mcp_client())

@router.post("/analyze-performance", response_model=ProductPerformanceAnalysis)
async def analyze_product_performance(
    request: ProductPerformanceRequest,
    service: ProductPerformanceService = Depends(get_performance_service)
) -> ProductPerformanceAnalysis:
    """
    Analyze product performance and suggest improvements based on sales decline.
    """
    try:
        return await service.analyze_performance(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-approval/{analysis_id}")
async def process_approval(
    analysis_id: str,
    approved: bool,
    notes: str = None,
    service: ProductPerformanceService = Depends(get_performance_service)
) -> Dict[str, Any]:
    """
    Process approval or rejection of suggested product adjustments.
    """
    try:
        return await service.process_approval(analysis_id, approved, notes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 