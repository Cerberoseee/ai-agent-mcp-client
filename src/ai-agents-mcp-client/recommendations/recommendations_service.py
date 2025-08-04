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
from collections import defaultdict
import logging

class RecommendationsService:
    mcp_client: MCPClient
    chunking_service: ChunkingService
    preprocess_service: PreprocessService
    openai_context_limit = 1000
    logger = logging.getLogger(__name__)
    weight_exponent = 1.5

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.chunking_service = ChunkingService()
        self.preprocess_service = PreprocessService(self.mcp_client)

    async def add_product_to_vector_db(self, request: GetEmbeddingsRequest):
        try:
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
        except Exception as e:
            self.logger.error(f"Error in add_product_to_vector_db: {e}")
            return False

    async def get_most_relevant_products(self, request: GetMostRelevantProductsRequest):
        prompt = f"""
            You are a product recommendation system. You are given a user profile.
            You need to return query terms and phrases so that we can search for the most relevant products in a vector database.
            User profile: {request.user_profile}
            Return results in a json format, with no other text, no explanation, no markdown, no formatting.
            The json format should be like this:
            {{
                "relevant_results": {{
                    "text": "query term or phrases inferred from the profile",
                    "weight": "weight of the query term or phrases, from 0 to 1"
                }}[]
            }}
        """

        query_term = self.mcp_client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": request.user_profile}
            ]
        )
        term_results = json.loads(query_term.choices[0].message.content)

        self.logger.info(f"Term results: {term_results}")

        relevant_results = term_results.get("relevant_results", [])
        # Get the embedding for each result in relevant_results
        embedding_with_weight = []
        for relevant_result in relevant_results:
            embedding = self.mcp_client.client.embeddings.create(
                model="text-embedding-3-large",
                input=relevant_result.get('text')
            )
            # The embedding vector is typically in embedding.data[0].embedding
            embedding_with_weight.append({
                "embedding": embedding.data[0].embedding,
                "weight": relevant_result.get("weight", 0)
            })
    

        product_scores = defaultdict(list)
        for embedding_with_weight in embedding_with_weight:
            similar_results = VectorDatabase.find_similar(
                query_embedding=embedding_with_weight.get("embedding"),
                limit=10,
                min_score=0.5
            )
        
            for result in similar_results:
                product_id = result["metadata"].get("product_id")
                distance = result.get("score", 0)
                if product_id:
                    term_weight = embedding_with_weight.get("weight", 0)
                    if distance > 0 and term_weight > 0:
                        combined_score = distance * (term_weight ** self.weight_exponent)
                    else:
                        combined_score = 0

                    product_scores[product_id].append(combined_score)

        all_counts = [len(scores) for scores in product_scores.values()]
        all_avg_scores = [sum(scores)/len(scores) for scores in product_scores.values()]

        max_count = max(all_counts) if all_counts else 1
        max_avg_score = max(all_avg_scores) if all_avg_scores else 1

        weight = 0.5

        product_rankings = []
        for product_id, scores in product_scores.items():
            count = len(scores)
            avg_score = sum(scores) / count if count else 0
            quantity_weight = count / max_count if max_count else 0
            distance_weight = avg_score / max_avg_score if max_avg_score else 0
            final_score = weight * quantity_weight + (1 - weight) * distance_weight
            product_rankings.append((product_id, final_score))

        product_rankings.sort(key=lambda x: x[1], reverse=True)

        product_ids = [product_id for product_id, _ in product_rankings]

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
                You are a customer profile builder. Based on the tools provided, call the tools to build the customer profile.
                """
            },
            {
                "role": "user",
                "content": f"""
                Customer id: {request.customer_id}
                """
            }
        ]

        completion = self.mcp_client.client.chat.completions.create(
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
            Based on this data, build the customer profile based on this template:
            ### Customer Profile Summary ###

            **Customer ID:** [Customer ID]
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
        follow_up_messages.append({
            "role": "user",
            "content": follow_up_prompt
        })

        response = self.mcp_client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=follow_up_messages,
        )

        return BuildUserProfileResponse(result=response.choices[0].message.content)
        
        