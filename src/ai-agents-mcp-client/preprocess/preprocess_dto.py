from pydantic import BaseModel
from typing import List, Optional

class AddDocsToCollectionDto(BaseModel):
    texts: list[str]
    collection_name: str
    metadatas: List[Optional[dict]] = []

class SummaryContentDto(BaseModel):
    content: str