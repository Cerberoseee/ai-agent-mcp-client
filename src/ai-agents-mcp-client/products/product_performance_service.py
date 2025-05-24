from typing import List, Dict, Any, Optional
import json
from .product_dto import (
    ProductPerformanceRequest,
    AdjustmentSuggestion,
    ApprovalRequest,
    AnalysisResponse
)
from mcp_client import MCPClient
import logging
class ProductPerformanceService:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.logger = logging.getLogger(__name__)

    async def analyze_performance(self, request: ProductPerformanceRequest) -> AnalysisResponse:
        try:
            analysis_context = {
                "product": request.productDetails,
                "performance_change": request.performanceChange,
                "current_state": request.productDetails
            }

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
                    "content": """You are a product performance analyst. Analyze the product's performance and suggest improvements.
                    Consider:
                    1. Price competitiveness
                    2. Description quality and SEO
                    3. Market trends and seasonality, in monthly timeframe
                    4. Historical performance patterns
                    5. Category-specific factors
                    Provide specific, actionable recommendations.
                    """
                },
                {
                    "role": "user",
                    "content": f"""
                    Analyze this product's performance decline ({request.performanceChange}%) and suggest improvements:
                    {json.dumps(analysis_context, indent=2)}
                    """
                }
            ]

        
            completion = self.mcp_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=available_tools,
                tool_choice="auto"
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
            

            # Make follow-up request
            analysis_completion = self.mcp_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=follow_up_messages + [{
                    "role": "user",
                    "content": """
                    Based on this data, please provide a comprehensive analysis of the product's performance decline.
                    """
                }],
            )

            suggested_adjustments_completion = self.mcp_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=follow_up_messages+ [{
                    "role": "user",
                    "content": """
                    Based on this data, please provide suggestions for improvements via tools.
                    """
                }],
                tools=available_tools,
                tool_choice="auto"
            )

            analysis_result = analysis_completion.choices[0].message.content or ""
            suggested_adjustments_result = suggested_adjustments_completion.choices[0].message.tool_calls
            suggested_adjustments = []

            # Process tool calls for suggested adjustments
            for tool_call in suggested_adjustments_result:
                tool_args = json.loads(tool_call.function.arguments)
                suggested_adjustments.append(
                    AdjustmentSuggestion(
                        type=tool_call.function.name,
                        current_value=request.productDetails,
                        suggested_value=tool_args,
                    )
                )

            self.logger.info(f"Analysis: {analysis_result}")
            self.logger.info(f"Adjustments: {suggested_adjustments}")

            return AnalysisResponse(
                suggested_adjustments=suggested_adjustments,
                analysis=analysis_result
            )
        except Exception as e:
            self.logger.error(f"Error in analyze_performance: {e}")
            return None

    async def process_approval(self, approval_request: ApprovalRequest) -> Dict[str, Any]:
        results = []
        for adjustment in approval_request.suggested_adjustments:
            try:
                result =  await self.mcp_client.session.call_tool(adjustment.type, adjustment.suggested_value)
                results.append({
                    "type": adjustment.type,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                self.logger.error(f"Error in process_approval: {e}")
                results.append({
                    "type": adjustment.type,
                    "success": False,
                    "error": str(e)
                })

        return {
            "product_id": approval_request.product_id,
            "status": "completed",
            "results": results
        }   