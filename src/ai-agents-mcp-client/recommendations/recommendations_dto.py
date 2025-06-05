from pydantic import BaseModel

class GetEmbeddingsRequest(BaseModel):
    name: str
    description: str

class KeywordWithEmbedding(BaseModel):
    keyword: str
    embedding: list[float]

class GetEmbeddingsResponse(BaseModel):
    result: list[KeywordWithEmbedding]

class GetMostRelevantKeywordsRequest(BaseModel):
    embedding_list: list[list[float]]

class GetMostRelevantKeywordsResponse(BaseModel):
    result: list[str]