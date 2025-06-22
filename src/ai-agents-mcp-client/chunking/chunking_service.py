import logging
from typing import Any
from chunking import Document
from chunking.document_specific_chunking import DocumentSpecificChunker

class ChunkingService:
    max_length = 200
    def __init__(self, max_length=200) -> None:
        self.max_length = max_length

    async def chunk_document(self, document: Any) -> Document:
        try:
            chunker = DocumentSpecificChunker(self.max_length)
            single_document_chunks = await chunker.create_chunks(document)
            
            if (single_document_chunks):
                return single_document_chunks
            
            return None
        except Exception as e:
            logging.error(f"Failed to chunk document: {e}")
            return None