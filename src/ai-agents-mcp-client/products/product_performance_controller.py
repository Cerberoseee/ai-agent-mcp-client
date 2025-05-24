from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from .product_dto import ProductPerformanceRequest, ApprovalRequest, AnalysisResponse
from .product_performance_service import ProductPerformanceService
from core.client_manager import ClientManager

router = APIRouter()

def get_performance_service() -> ProductPerformanceService:
    return ProductPerformanceService(ClientManager.get_mcp_client())

@router.post("/analyze-performance", response_model=AnalysisResponse)
async def analyze_product_performance(
    request: ProductPerformanceRequest,
    service: ProductPerformanceService = Depends(get_performance_service)
) -> AnalysisResponse:
    """
    Analyze product performance and suggest improvements based on sales decline.
    """
    try:
        return await service.analyze_performance(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-approval")
async def process_approval(
    request: ApprovalRequest,
    service: ProductPerformanceService = Depends(get_performance_service)
) -> Dict[str, Any]:
    """
    Process approval or rejection of suggested product adjustments.
    """
    try:
        return await service.process_approval(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 