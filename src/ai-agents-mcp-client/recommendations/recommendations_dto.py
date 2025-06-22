from pydantic import BaseModel

class GetEmbeddingsRequest(BaseModel):
    name: str
    description: str
    product_id: str

class KeywordWithEmbedding(BaseModel):
    keyword: str
    embedding: list[float]

class GetEmbeddingsResponse(BaseModel):
    result: list[KeywordWithEmbedding]

class BuildUserProfileRequest(BaseModel):
    user_id: str

class BuildUserProfileResponse(BaseModel):
    result: str

class GetMostRelevantProductsRequest(BaseModel):
    user_profile: str

class GetMostRelevantProductsResponse(BaseModel):
    result: list[str]