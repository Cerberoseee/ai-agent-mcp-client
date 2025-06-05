import logging
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import os

logger = logging.getLogger(__name__)

class VectorDatabase:
    _instance = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorDatabase, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, db_name: str = "vector_db"):
        connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        
        try:
            cls._client = MongoClient(connection_string)
            cls._db = cls._client[db_name]
            cls._client.admin.command('ping')
            logger.info("Vector database connection established successfully")
            
            cls._ensure_vector_indexes()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to vector database: {e}")
            return False
    
    @classmethod
    def _ensure_vector_indexes(cls):
        if "embeddings" not in cls._db.list_collection_names():
            cls._db.create_collection("embeddings")
            
        try:
            cls._db.embeddings.create_index([("embedding", "vector")])
            logger.info("Vector index created successfully")
        except Exception as e:
            logger.warning(f"Could not create vector index: {e}. Vector search may not work properly.")
    
    @classmethod
    def get_collection(cls, collection_name: str = "embeddings") -> Collection:
        if cls._db is None:
            raise ValueError("Vector database not initialized. Call initialize() first.")
        return cls._db[collection_name]
    
    @classmethod
    def store_embedding(
        cls, 
        keyword: str, 
        embedding: List[float], 
        metadata: Dict[Any, Any] = None
    ) -> str:
        collection = cls.get_collection()
        
        document = {
            "keyword": keyword,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    @classmethod
    def batch_store_embeddings(cls, keyword_embeddings: List[Dict[str, Any]]) -> List[str]:
        collection = cls.get_collection()
        
        documents = []
        for item in keyword_embeddings:
            documents.append({
                "keyword": item["keyword"],
                "embedding": item["embedding"],
                "metadata": item.get("metadata", {})
            })
        
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    @classmethod
    def find_similar(
        cls, 
        query_embedding: List[float], 
        limit: int = 5, 
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        collection = cls.get_collection()
        
        results = collection.aggregate([
            {
                "$vectorSearch": {
                    "index": "embedding",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "limit": limit,
                    "numCandidates": limit * 10,
                    "minScore": min_score
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "keyword": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ])
        
        return list(results)
    
    @classmethod
    def cleanup(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None