from pydantic import BaseModel
from typing import Optional

class ProductRequest(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    categories_name: str
    description: str
    confidence_score: float
    reasoning: str