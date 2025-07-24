from .order_processing_dto import Order, ApprovalRequest, AdjustmentSuggestion
import json
import asyncio
import logging
from mcp.types import TextContent  # Ensure this import is at the top of your file

class OrderProcessingService:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.logger = logging.getLogger(__name__)

    async def create_process_order_request(self, order: Order):
        try:
            # #Step 1: Listing availables and suitable tools
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
                Also, if possible, call the tools to get shipping rates, coupon codes, etc.
                ONLY call reading tools, not creating, updating, or deleting tools.
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": order.model_dump_json()}
            ]

            response = self.mcp_client.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=available_tools
            )

            print(response.choices[0].message.tool_calls)

            tool_results = {}
            if response.choices[0].message.tool_calls:
                for tc1 in response.choices[0].message.tool_calls:
                    tool_name = tc1.function.name
                    tool_args = json.loads(tc1.function.arguments)
                    tool_result = await self.mcp_client.session.call_tool(tool_name, tool_args)
                    tool_results[tool_name] = tool_result.content

            # #Step 1.5: Storing tool results in a structured format
            tool_analyzed_result_messages = []

            tool_analyzed_result_messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc2.id,
                        "type": "function",
                        "function": {
                            "name": tc2.function.name,
                            "arguments": tc2.function.arguments
                        }
                    } for tc2 in response.choices[0].message.tool_calls
                ] 
            })

            for tc3 in response.choices[0].message.tool_calls:
                tool_name = tc3.function.name
                result = tool_results.get(tool_name, None)
                if result:
                    tool_analyzed_result_messages.append({
                        "tool_call_id": tc3.id,
                        "role": "tool",
                        "content": result,
                    })
            # #Step 2: Listing processes to be done to process the order        
            processing_prompt = """
                Based on the tool results, list the all the processes needed to be done to process the order.
                For examples:
                - Create a new order in the system.
                - Notify the customer and agent that the order is processed.
                - Calculate the shipping rate with shipping services.
                - Validate coupon codes.
                - etc.
                Be mindful that these processes are not exhaustive, you can come up with more processes as needed or exclude the above processes if they are not needed.
                The output should be a list of processes, in the following format:
                [
                    {
                        "process": "process_name",
                        "description": "process_description"
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
                    - Tool name: {tool['function']['name']}
                    - Tool description: {tool['function']['description']}
                    - Tool input schema: {tool['function']['parameters']}
                \n
                """  

            processing_messages.append({
                "role": "system",
                "content": available_tools_prompt
            })

            print(processing_messages)
            print("_______________________")

            processing_response = self.mcp_client.client.chat.completions.create(
                model="gpt-4o",
                messages=processing_messages,
            )

            print(processing_response)
            print("_______________________")
            
            #Step 3: Processing the order
            processes = json.loads(processing_response.choices[0].message.content)

            completion_results = []
            
            for process in processes:
                process_name = process["process"]
                process_description = process["description"]
                prompt = f"""
                    You are a order processing agent.
                    Based on the tool results, process the order.
                    The order is: {order.order_id}
                    The process is: {process_name}
                    The process description is: {process_description}
                    If the process can't be done with the provided tools, don't return any tool calls.
                """
                messages = [{"role": "system", "content": prompt}] + tool_analyzed_result_messages

                completion_result = None

                try:
                    completion_result = self.mcp_client.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=available_tools
                    )
                except Exception as e:
                    self.logger.error(f"Error in create_process_order_request: {e}")
                    completion_result = None
                
                completion_results.append(completion_result)

            process_list = []
            
            for completed_result in completion_results:
                if completed_result is None:
                    continue

                if completed_result.choices[0].message.content is not None:
                    process_list.append(ApprovalRequest(
                        order_id=order.order_id,
                        description=completed_result.choices[0].message.content
                    ))
                    continue

                for tool_call in completed_result.choices[0].message.tool_calls:
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

            return process_list
        
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