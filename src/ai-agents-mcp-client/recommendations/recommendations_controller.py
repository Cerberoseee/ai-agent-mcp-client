from fastapi import APIRouter
from .recommendations_dto import GetEmbeddingsRequest, GetEmbeddingsResponse
from .recommendations_service import RecommendationsService
from core.client_manager import ClientManager
from fastapi import Depends

router = APIRouter()

def get_recommendations_service() -> RecommendationsService:
    return RecommendationsService(ClientManager.get_mcp_client())    

@router.post("/get-embeddings", response_model=GetEmbeddingsResponse)
async def get_embeddings(request: GetEmbeddingsRequest, service: RecommendationsService = Depends(get_recommendations_service)):    
    result = service.get_embeddings(request)
    return result

@router.post("/get-most-relevant-keywords", response_model=GetEmbeddingsResponse)
async def get_most_relevant_keywords(request: GetEmbeddingsRequest, service: RecommendationsService = Depends(get_recommendations_service)):
    result = service.get_most_relevant_keywords(request)
    return result