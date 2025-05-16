from typing import List, Dict, Any, Optional
import json
from .product_dto import (
    ProductPerformanceRequest,
    ProductPerformanceAnalysis,
    AdjustmentSuggestion,
    ApprovalRequest
)
from mcp_client import MCPClient

class ProductPerformanceService:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self._approval_requests: Dict[str, ApprovalRequest] = {}

    async def analyze_performance(self, request: ProductPerformanceRequest) -> ProductPerformanceAnalysis:
        product_data = await self._get_product_data(request.productId)
        order_history = await self._get_order_history(request.productId)
        market_trends = await self._get_market_trends(request.productDetails.get('categoryId'))

        analysis_context = {
            "product": product_data,
            "performance_change": request.performanceChange,
            "order_history": order_history,
            "market_trends": market_trends,
            "current_state": request.productDetails
        }

        tools_response = await self.mcp_client.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        } for tool in tools_response.tools]

        messages = [
            {
                "role": "system",
                "content": """You are a product performance analyst. Analyze the product's performance and suggest improvements.
                Consider:
                1. Price competitiveness
                2. Description quality and SEO
                3. Market trends and seasonality
                4. Historical performance patterns
                5. Category-specific factors
                Provide specific, actionable recommendations."""
            },
            {
                "role": "user",
                "content": f"Analyze this product's performance decline ({request.performanceChange}%) and suggest improvements:\n{json.dumps(analysis_context, indent=2)}"
            }
        ]

        completion = await self.mcp_client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=available_tools,
            tool_choice="auto"
        )

        analysis_result = completion.choices[0].message.content
        suggested_adjustments = []

        # Process each tool call in the analysis
        if completion.choices[0].message.tool_calls:
            for tool_call in completion.choices[0].message.tool_calls:
                tool_args = json.loads(tool_call.function.arguments)
                suggested_adjustments.append(
                    AdjustmentSuggestion(
                        type=tool_call.function.name,
                        current_value=self._get_current_value(request.productDetails, tool_call.function.name),
                        suggested_value=tool_args,
                        reasoning=f"Based on analysis of {tool_call.function.name}",
                        confidence=0.85,  # This could be derived from the analysis
                        priority=len(suggested_adjustments) + 1
                    )
                )

        # Create analysis response
        analysis = ProductPerformanceAnalysis(
            product_id=request.productId,
            performance_change=request.performanceChange,
            market_analysis=analysis_result,
            suggested_adjustments=suggested_adjustments,
            analysis_summary=self._generate_summary(analysis_result, suggested_adjustments)
        )

        # Create approval request
        approval_request = ApprovalRequest(
            analysis_id=f"analysis_{request.productId}_{len(self._approval_requests)}",
            product_id=request.productId,
            suggested_adjustments=suggested_adjustments
        )
        self._approval_requests[approval_request.analysis_id] = approval_request

        return analysis
            
    async def process_approval(self, analysis_id: str, approved: bool, notes: Optional[str] = None) -> Dict[str, Any]:
        if analysis_id not in self._approval_requests:
            raise ValueError(f"No approval request found for analysis ID: {analysis_id}")

        approval_request = self._approval_requests[analysis_id]
        approval_request.approval_status = "approved" if approved else "rejected"
        approval_request.approval_notes = notes

        if approved:
            results = []
            for adjustment in approval_request.suggested_adjustments:
                try:
                    result = await self._apply_adjustment(
                        approval_request.product_id,
                        adjustment
                    )
                    results.append({
                        "type": adjustment.type,
                        "success": True,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "type": adjustment.type,
                        "success": False,
                        "error": str(e)
                    })

            return {
                "analysis_id": analysis_id,
                "status": "completed",
                "results": results
            }
        
        return {
            "analysis_id": analysis_id,
            "status": "rejected",
            "notes": notes
        }

    async def _get_product_data(self, product_id: str) -> Dict[str, Any]:
        result = await self.mcp_client.session.call_tool("get_product_data", {"product_id": product_id})
        return result.content

    async def _get_order_history(self, product_id: str) -> Dict[str, Any]:
        result = await self.mcp_client.session.call_tool("get_order_history", {"product_id": product_id})
        return result.content

    async def _get_market_trends(self, category_id: str) -> Dict[str, Any]:
        result = await self.mcp_client.session.call_tool("get_market_trends", {"category_id": category_id})
        return result.content

    async def _apply_adjustment(self, product_id: str, adjustment: AdjustmentSuggestion) -> Any:
        tool_name = f"update_{adjustment.type}"
        args = {
            "product_id": product_id,
            **adjustment.suggested_value
        }
        result = await self.mcp_client.session.call_tool(tool_name, args)
        return result.content

    def _get_current_value(self, product_details: Dict[str, Any], tool_name: str) -> Any:
        # Map tool names to product detail fields
        field_mapping = {
            "update_price": "retailPrice",
            "update_description": "description",
            "create_product_promotion": "promotions"
        }
        field = field_mapping.get(tool_name)
        return product_details.get(field) if field else None

    def _generate_summary(self, analysis: str, adjustments: List[AdjustmentSuggestion]) -> str:
        summary_parts = [
            "Performance Analysis Summary:",
            "------------------------",
            analysis[:200] + "..." if len(analysis) > 200 else analysis,
            "\nProposed Adjustments:",
            "-------------------"
        ]
        
        for adj in adjustments:
            summary_parts.append(f"- {adj.type}: {adj.reasoning} (Priority: {adj.priority})")
        
        return "\n".join(summary_parts) 