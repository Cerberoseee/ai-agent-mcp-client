import logging
from typing import List, Dict, Any, Optional
import os
import uuid
import pinecone
from pinecone.grpc import PineconeGRPC, GRPCClientConfig

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class VectorDatabase:
    _instance = None
    _index = None

    @classmethod
    def initialize(cls):
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENVIRONMENT")
        index_name = os.getenv("PINECONE_INDEX_NAME", "vector_index")
        host = os.getenv("PINECONE_HOST", "http://localhost:5080")  

        pinecone_client = PineconeGRPC(api_key=api_key, host=host)

        index_spec = {
            "serverless": {
                "cloud": "aws",
                "region": "us-east-1"
            }
        }
        indexes = pinecone_client.list_indexes()

        if not any(idx.get("name") == index_name for idx in indexes):
            pinecone_client.create_index(index_name, dimension=3072, metric="cosine", spec=index_spec)
        else:
            logger.info(f"Index '{index_name}' already exists. Skipping creation.")
        
        cls._index = pinecone_client.Index(index_name, grpc_config=GRPCClientConfig(secure=False))
        logger.info("Pinecone index initialized successfully")
        return True

    @classmethod
    def store_embedding(cls, collection_name: str, embedding: List[float], metadata: Dict[Any, Any] = None) -> str:
        if cls._index is None:
            raise ValueError("Pinecone index not initialized. Call initialize() first.")

        vector_id = str(uuid.uuid4())
        cls._index.upsert([{
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        }])
        return vector_id

    @classmethod
    def batch_store_embeddings(cls, collection_name: str, keyword_embeddings: List[Dict[str, Any]]) -> List[str]:
        if cls._index is None:
            raise ValueError("Pinecone index not initialized. Call initialize() first.")

        vectors = [{
            "id": str(uuid.uuid4()),
            "values": item["embedding"][0],
            "metadata": item.get("metadata", {})
        } for item in keyword_embeddings]
        cls._index.upsert(vectors)
        return True

    @classmethod
    def find_similar(cls, query_embedding: List[float], limit: int = 5, min_score: float = 0.7) -> List[Dict[str, Any]]:
        if cls._index is None:
            raise ValueError("Pinecone index not initialized. Call initialize() first.")

        results = cls._index.query(query_embedding, top_k=limit, include_metadata=True)
        return [result for result in results.matches if result['score'] >= min_score]

    @classmethod
    def cleanup(cls):
        cls._index = None