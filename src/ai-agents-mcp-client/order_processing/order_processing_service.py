from .order_processing_dto import Order, OrderProcessingResponse, ApprovalRequest, AdjustmentSuggestion
import json
import asyncio
import logging
class OrderProcessingService:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.logger = logging.getLogger(__name__)

    async def create_process_order_request(self, order: Order):
        try:
            #Step 1: Listing availables and suitable tools
            tools_response = await self.mcp_client.session.list_tools()
            available_tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in tools_response.tools]

            system_prompt = """
                You are a order processing agent. 
                Based on the tools provided, call the tools to acquire context such as product details, customer details, etc.
                ONLY call reading tools, not creating, updating, or deleting tools.
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": order.order_id}
            ]

            response = await self.mcp_client.session.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=available_tools
            )

            tool_results = {}
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_result = await self.mcp_client.session.call_tool(tool_name, tool_args)
                    tool_results[tool_name] = tool_result.content

            #Step 1.5: Storing tool results in a structured format
            tool_analyzed_result_messages = []

            tool_analyzed_result_messages.append({
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
                    } for tool_call in response.choices[0].message.tool_calls
                ] 
            })

            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                result = tool_results.get(tool_name, None)
                if result:
                    tool_analyzed_result_messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result,
                    })

            #Step 2: Listing processes to be done to process the order        
            processing_prompt = """
                Based on the tool results, list the all the processes needed to be done to process the order.
                This consists of the following processes:
                - Check if the order is valid.
                - Create a new order in the system.
                - Notify the customer and agent that the order is processed.
                - Calculate the shipping rate with shipping services.
                - Validate coupon codes.
                - etc.
                Be mindful that these processes are not exhaustive, you can come up with more processes as needed.
                The output should be a list of processes, in the following format:
                [
                    {
                        "process": "process_name",
                        "description": "process_description",
                    }
                ]
                Also make sure the result does not contain any other text than the list of processes.
            """

            processing_messages = []

            processing_messages.append({
                "role": "system",
                "content": processing_prompt
            })
            
            processing_messages.extend(tool_analyzed_result_messages)

            available_tools_prompt = "Available tools:\n"
            for index, tool in enumerate(available_tools):
                available_tools_prompt += f"""
                {index + 1}/{len(available_tools)}:
                    - Tool name: {tool.name}
                    - Tool description: {tool.description}
                    - Tool input schema: {tool.inputSchema}
                \n
                """

            processing_messages.append({
                "role": "system",
                "content": available_tools_prompt
            })

            processing_response = await self.mcp_client.session.chat.completions.create(
                model="gpt-4o-mini",
                messages=processing_messages,
            )

            #Step 3: Processing the order
            tasks = []
            for process in processing_response.choices[0].message.content:
                process_name = process["content"]["process"]
                process_description = process["content"]["description"]
                prompt = f"""
                    You are a order processing agent.
                    Based on the tool results, process the order.
                    The order is: {order.order_id}
                    The process is: {process_name}
                    The process description is: {process_description}
                """

                tasks.append(self.mcp_client.session.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
                        *tool_analyzed_result_messages
                    ],
                    tools=available_tools
                ))
            
            results = await asyncio.gather(*tasks)

            process_list = []
            
            for result in results:
                for tool_call in result.choices[0].message.tool_calls:
                    tool_args = json.loads(tool_call.function.arguments)
                    approval_request = ApprovalRequest(
                        order_id=order.order_id,
                        suggested_adjustments=[
                            AdjustmentSuggestion(
                                type=tool_call.function.name,
                                suggested_value=tool_args
                            )
                        ]
                    )
                    process_list.append(approval_request)

            return ApprovalRequest(
                order_id=order.order_id,
                suggested_adjustments=process_list
            )
        
        except Exception as e:
            self.logger.error(f"Error in create_process_order_request: {e}")
            raise e
        
    async def order_processing_approval(self, approval_request: ApprovalRequest):
        results = []
        for adjustment in approval_request.suggested_adjustments:
            try:
                result = await self.mcp_client.session.call_tool(adjustment.type, adjustment.suggested_value)
                results.append({
                    "type": adjustment.type,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                self.logger.error(f"Error in order_processing_approval: {e}")
                results.append({
                    "type": adjustment.type,
                    "success": False,
                    "error": str(e)
                })

        return {
            "order_id": approval_request.order_id,
            "status": "completed",
            "results": results
        }