from .recommendations_dto import GetEmbeddingsRequest, GetEmbeddingsResponse, KeywordWithEmbedding, GetMostRelevantKeywordsRequest, GetMostRelevantKeywordsResponse
from core.client_manager import ClientManager
from core.vector_db import VectorDatabase
from mcp_client import MCPClient
import json
import numpy as np

class RecommendationsService:
    mcp_client: MCPClient
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    def get_embeddings(self, request: GetEmbeddingsRequest):
        completion = self.mcp_client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a keyword generation assistant. Generate relevant keywords based on the product name and description.
                    Consider:
                    1. Main product features and benefits
                    2. Target audience and use cases
                    3. Related product categories
                    4. Common search terms in this product space
                    5. Brand-specific terms if applicable
                    
                    Return a list of keywords (about 4-5 keywords) that would be most effective for product discovery and content filtering.
                    Output should be in the following format, with no other text, instructions or comments:
                    ```
                        ["keyword1", "keyword2", "keyword3"]
                    ```
                    """
                },
                {
                    "role": "user", 
                    "content": f"Generate keywords for this product:\nName: {request.name}\nDescription: {request.description}"
                }
            ]
        )

        content = completion.choices[0].message.content
        
        cleaned_content = content.strip()
        if "```" in cleaned_content:
            start_idx = cleaned_content.find("[")
            end_idx = cleaned_content.rfind("]") + 1
            if start_idx >= 0 and end_idx > start_idx:
                cleaned_content = cleaned_content[start_idx:end_idx]
        
        # Parse the keywords
        try:
            keywords = json.loads(cleaned_content)
        except json.JSONDecodeError:
            keywords = [k.strip().strip('"\'[]') for k in cleaned_content.strip('[]').split(',')]
        
        result = []
        keyword_embeddings = []
        
        for keyword in keywords:
            embedding_response = self.mcp_client.client.embeddings.create(
                model="text-embedding-3-small",
                input=keyword
            )
            embedding = embedding_response.data[0].embedding
            
            keyword_embeddings.append({
                "keyword": keyword,
                "embedding": embedding,
                "metadata": {
                    "product_name": request.name,
                    "source": "recommendations_service"
                }
            })
            
            # Add to result for response
            result.append(
                KeywordWithEmbedding(
                    keyword=keyword, 
                    embedding=embedding,
                )
            )
        
        VectorDatabase.batch_store_embeddings(keyword_embeddings)
        
        return GetEmbeddingsResponse(result=result)

    def get_most_relevant_keywords(self, request: GetMostRelevantKeywordsRequest):
        average_embedding = np.average(request.embedding_list, axis=0)

        similar_results = VectorDatabase.find_similar(
            query_embedding=average_embedding,
            limit=5
        )
        
        return GetMostRelevantKeywordsResponse(result=similar_results)
        
            
        
        