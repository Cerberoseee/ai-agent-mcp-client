from .recommendations_dto import (
    GetEmbeddingsRequest, 
    GetMostRelevantProductsRequest, 
    GetMostRelevantProductsResponse, 
)
from core.client_manager import ClientManager
from core.vector_db import VectorDatabase
from mcp_client import MCPClient
import json
import numpy as np
from chunking.chunking_service import ChunkingService
import asyncio
from preprocess.preprocess_service import PreprocessService
from preprocess.preprocess_dto import AddDocsToCollectionDto, SummaryContentDto
from .recommendations_dto import BuildUserProfileRequest, BuildUserProfileResponse

class RecommendationsService:
    mcp_client: MCPClient
    chunking_service: ChunkingService
    preprocess_service: PreprocessService
    openai_context_limit = 1000

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.chunking_service = ChunkingService()
        self.preprocess_service = PreprocessService()

    async def add_product_to_vector_db(self, request: GetEmbeddingsRequest):
        document_chunks = await self.chunking_service.chunk_document(document=request.description)
        collection_name = f"vector_products"
        tasks = []
        for section in document_chunks.sections:
            section_id = section.get_id()
            sentence_tasks = []
            for paragraph in section.paragraphs:
                paragraph_id = paragraph.get_id()
                sentence_tasks.append(
                    self.preprocess_service.add_docs(
                        AddDocsToCollectionDto(
                            texts=[
                                sentence.get_content()
                                for sentence in paragraph.sentences
                            ],
                            collection_name=collection_name,
                            metadatas=[
                                {
                                    "product_id": request.product_id,
                                    "section_id": str(section_id),
                                    "paragraph_id": str(paragraph_id),
                                    "sentence_id": str(sentence.get_id()),
                                    "content": sentence.get_content(),
                                }
                                for sentence in paragraph.sentences
                            ],
                        )
                    )
                )
            await asyncio.gather(*sentence_tasks)
            summarized_paragraph = [
                await self.preprocess_service.summary_content(
                    SummaryContentDto(
                        content=paragraph.restore(),
                        api_key=self.mcp_client.api_key
                    )
            ) if len(paragraph.restore()) >= self.openai_context_limit else paragraph.restore() for paragraph in section.paragraphs]
            tasks.append(
                self.preprocess_service.add_docs(
                    AddDocsToCollectionDto(
                        texts= summarized_paragraph,
                        collection_name=collection_name,
                        metadatas=[
                            {
                                "product_id": request.product_id,
                                "section_id": str(section_id),
                                "paragraph_id": str(paragraph.get_id()),
                                "content": paragraph_content,
                            }
                            for paragraph, paragraph_content in zip(section.paragraphs,summarized_paragraph)
                        ],
                    )
                )
            )
        await asyncio.gather(*tasks)
        return True

    async def get_most_relevant_products(self, request: GetMostRelevantProductsRequest):
        prompt = f"""
            You are a product recommendation system. You are given a user profile.
            You need to return the query term so that we can search for the most relevant products in a vector database.
            User profile: {request.user_profile}
            Return only the query term, with no other text, no explanation, no markdown, no formatting.
        """

        query_term = await self.mcp_client.session.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": request.user_profile}
            ]
        )

        similar_results = VectorDatabase.find_similar(
            query_embedding=query_term,
            limit=5
        )

        product_ids = [result.metadata["product_id"] for result in similar_results]

        return GetMostRelevantProductsResponse(result=product_ids)

    async def build_user_profile(self, request: BuildUserProfileRequest):
        tools_response = await self.mcp_client.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in tools_response.tools]

        messages = [
            {
                "role": "system",
                "content": """
                You are a user profile builder. Based on the tools provided, call the tools to build the user profile.
                """
            },
            {
                "role": "user",
                "content": f"""
                User id: {request.user_id}
                """
            }
        ]

        completion = await self.mcp_client.session.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=available_tools
        )

        # Process each tool call and gather data
        tool_results = {}
        if completion.choices[0].message.tool_calls:
            for tool_call in completion.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = await self.mcp_client.session.call_tool(tool_name, tool_args)
                self.logger.info(f"Tool call result: {tool_result}")
                tool_results[tool_name] = tool_result.content
                
        # Make a follow-up request with the data from tool calls
        follow_up_messages = messages.copy()
        
        # Add assistant's tool call message
        follow_up_messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in completion.choices[0].message.tool_calls
            ]
        })
        
        # Add tool results as tool response messages
        for tool_call in completion.choices[0].message.tool_calls:
            tool_name = tool_call.function.name
            result = tool_results.get(tool_name, None)
            if result:
                follow_up_messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": result,
                })
        
        follow_up_prompt = """
            Based on this data, build the user profile based on this template:
            ### User Profile Summary ###

            **User ID:** [user_id]
            **Demographics (if available and relevant):**
            - Age Group: [e.g., Young Adult (18-24)]
            - Location: [e.g., Ho Chi Minh City, Vietnam]
            - Occupation/Interests (if gathered): [e.g., Student, Loves technology, Photography hobbyist]

            **Recent Activity & Explicit Preferences:**
            - **Recently Viewed Products:**
                - Product A: "High-end mirrorless camera with 4K video, compact design." (Viewed 2 days ago)
                - Product B: "Tripod with flexible legs, lightweight for travel." (Viewed 1 day ago)
            - **Recently Purchased Products:**
                - Product C: "Beginner drone with obstacle avoidance." (Purchased 3 weeks ago)
            - **Liked Categories/Brands:**
                - Category: Electronics, Photography, Outdoor Gear
                - Brands: Sony, DJI, Nikon
            - **Disliked Categories/Brands (if known):**
                - Category: Heavy machinery, Industrial tools
                - Brands: [e.g., Avoid Brand X, finds their products too bulky]
            - **Search History (summarized/key terms):**
                - "lightweight travel camera"
                - "drone for beginners"
                - "action camera waterproof"

            **Inferred Interests & Style:**
            - **Preferred Product Attributes:**
                - Emphasis on portability, high-resolution imagery, ease of use.
                - Values long battery life and good connectivity.
                - Prefers modern, sleek designs.
            - **Spending Habits:**
                - Mid-to-high budget for electronics.
                - Willing to invest in quality gear for hobbies.
            - **Engagement Patterns:**
                - Often explores product reviews and specifications in depth before purchasing.

        """
        
        response = await self.mcp_client.session.chat.completions.create(
            model="gpt-4o-mini",
            messages=follow_up_messages + [{
                "role": "user",
                "content": follow_up_prompt
            }],
        )

        return BuildUserProfileResponse(result=response.choices[0].message.content)
        
        