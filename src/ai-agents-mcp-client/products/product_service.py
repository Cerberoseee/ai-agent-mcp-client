from .product_dto import ProductRequest, ProductResponse, ProductFeature
from mcp_client import MCPClient
import json

class ProductService:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    async def categorize_product(self, request: ProductRequest) -> ProductResponse:
        # Initial system prompt to guide the analysis
        messages = [
            {
                "role": "system",
                "content": """You are a product classification expert. Analyze products using the following steps:
1. Extract key features and specifications from the product description
2. Identify the product type and category based on features
3. Validate the classification against known categories
4. Provide confidence score and reasoning
Be thorough and explain your thought process."""
            },
            {
                "role": "user",
                "content": f"""Product Title: {request.title}
Description: {request.description}
Please analyze this product and classify it into the appropriate category."""
            }
        ]

        # Get available tools from MCP server
        tools_response = await self.mcp_client.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        } for tool in tools_response.tools]

        reasoning_chain = []
        features = []
        
        # Step 1: Initial analysis
        completion = await self.mcp_client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=available_tools,
            tool_choice="auto"
        )

        # Process the initial analysis
        for choice in completion.choices:
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool call
                    tool_result = await self.mcp_client.session.call_tool(
                        tool_call.function.name, 
                        tool_args
                    )
                    
                    # Add tool results to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result.content)
                    })
                    
                    reasoning_chain.append(f"Tool {tool_call.function.name} called: {tool_result.content}")
            else:
                content = choice.message.content
                reasoning_chain.append(content)
                
                # Extract features if present in the analysis
                if "Features identified:" in content:
                    feature_section = content.split("Features identified:")[1].split("\n")
                    for feature in feature_section:
                        if feature.strip():
                            features.append(ProductFeature(
                                feature=feature.strip(),
                                relevance=0.8,  # Default relevance
                                explanation="Extracted from initial analysis"
                            ))

        # Step 2: Category validation and confidence scoring
        messages.append({
            "role": "user",
            "content": "Based on the analysis above, what is the final category classification? Please provide:\n1. Category name\n2. Confidence score (0-1)\n3. Final explanation"
        })

        final_completion = await self.mcp_client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        final_content = final_completion.choices[0].message.content
        reasoning_chain.append(final_content)

        # Parse the final response
        lines = final_content.split("\n")
        category_name = ""
        category_confidence = 0.0
        final_explanation = ""

        for line in lines:
            if line.startswith("1."):
                category_name = line.split("1.")[1].strip()
            elif line.startswith("2."):
                confidence_str = line.split("2.")[1].strip()
                try:
                    category_confidence = float(confidence_str)
                except ValueError:
                    # Extract the first number found in the string
                    import re
                    numbers = re.findall(r"0\.\d+|\d+", confidence_str)
                    if numbers:
                        category_confidence = float(numbers[0])
            elif line.startswith("3."):
                final_explanation = line.split("3.")[1].strip()

        return ProductResponse(
            category_name=category_name,
            category_confidence=category_confidence,
            features=features,
            reasoning_chain=reasoning_chain,
            final_explanation=final_explanation
        )
