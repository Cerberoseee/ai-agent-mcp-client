from fastapi import APIRouter
from .recommendations_dto import GetEmbeddingsRequest, GetEmbeddingsResponse, GetMostRelevantProductsRequest, GetMostRelevantProductsResponse
from .recommendations_service import RecommendationsService
from core.client_manager import ClientManager
from fastapi import Depends

router = APIRouter()

def get_recommendations_service() -> RecommendationsService:
    return RecommendationsService(ClientManager.get_mcp_client())    

@router.post("/add-product-to-vector-db", response_model=GetEmbeddingsResponse)
async def add_product_to_vector_db(request: GetEmbeddingsRequest, service: RecommendationsService = Depends(get_recommendations_service)):    
    result = service.add_product_to_vector_db(request)
    return result

@router.post("/get-most-relevant-products", response_model=GetMostRelevantProductsResponse)
async def get_most_relevant_products(request: GetMostRelevantProductsRequest, service: RecommendationsService = Depends(get_recommendations_service)):
    result = service.get_most_relevant_products(request)
    return result

@router.post("/build-user-profile")
async def build_user_profile(request, service: RecommendationsService = Depends(get_recommendations_service)):
    result = service.build_user_profile(request)
    return result