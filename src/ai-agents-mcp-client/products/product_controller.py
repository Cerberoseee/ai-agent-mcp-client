from fastapi import APIRouter, Depends
from .product_service import ProductService
from .product_dto import ProductRequest, ProductResponse
from core.client_manager import ClientManager

router = APIRouter()

def get_product_service() -> ProductService:
    return ProductService(ClientManager.get_mcp_client())

@router.post("/categorize", response_model=ProductResponse)
async def categorize_product(
    request: ProductRequest,
    service: ProductService = Depends(get_product_service)
) -> ProductResponse:
    return await service.categorize_product(request)