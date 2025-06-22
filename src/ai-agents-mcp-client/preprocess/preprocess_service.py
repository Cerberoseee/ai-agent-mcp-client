from .preprocess_dto import AddDocsToCollectionDto, SummaryContentDto
from core.vector_db import VectorDatabase
from mcp_client import MCPClient
from langchain_openai import OpenAIEmbeddings, OpenAI
import logging

class PreprocessService:
    embedding_client: OpenAIEmbeddings
    client: OpenAI

    def __init__(self, mcp_client: MCPClient):
        self.client = OpenAI(
            api_key=mcp_client.api_key
        )
        self.embedding_client = OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=mcp_client.api_key
        )

    async def add_docs(self, payload: AddDocsToCollectionDto):
        metadatas = payload.metadatas
        embeddings = await self.get_embedding_docs(payload.texts)

        data = []

        for i, embedding in enumerate(embeddings):
            embedding = embedding if payload.texts[i] else [0] * len(embedding)
            doc_data = {
                "embedding": embedding,
            }
            if len(metadatas) > i and metadatas[i] is not None:
                doc_data.update(metadatas[i])
            data.append(doc_data)

        VectorDatabase.batch_store_embeddings(
            collection_name=payload.collection_name,
            keyword_embeddings=data
        )

    async def summary_content(self, request: SummaryContentDto):
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """
                    ### Bot Profile for Enhanced Simplified Direct Content Summarization

                    **Function:** Enhanced Simplified Summarization Assistant  
                    **Language Adaptability:** Ensures the summary language matches exactly the language of the input content  
                    **Primary Task:** To provide straightforward, accurate summaries of the provided content, maintaining the same language as the input

                    ### Summarization Process

                    1. **Content Understanding:**
                        - Thoroughly read and comprehend the provided content to identify its main themes and key points.

                    2. **Enhanced Simplified Summarization:**
                        - Directly produce a summary that focuses only on the essential elements of the content, maintaining the exact language of the input.
                        - The summary should mirror the language style, tone, and linguistic nuances of the input content.
                        - **Verification Step:** Ensure that the summary is a clear, concise encapsulation of the key points of the input content.

                    3. **Summarization Output:**
                        - The output must be the summary itself, presented in the same language as the input content and as plain text.
                        - Remove any additional formatting or titles from the output to ensure it is only the summary content.

                    ### Output:
                    - The direct summary of the content in the same language, presented plainly without any additional formatting or context.
                """,
                },
                {"role": "user", "content": f"{request.content}"}
            ]
        )
        return response.choices[0].message.content
    
    async def get_embedding_docs(self, texts: list[str]):
        try:
            embeddings = await self.embedding_client.aembed_documents(texts)
            if embeddings:
                return embeddings
        except Exception as e:
            logging.error(f"Failed to get embedding: {e}")
            return None