from fastapi import APIRouter, Depends
from .order_processing_dto import Order, ApprovalRequest
from .order_processing_service import OrderProcessingService
from core.client_manager import ClientManager
from typing import List

router = APIRouter()

def get_order_processing_service() -> OrderProcessingService:
    return OrderProcessingService(ClientManager.get_mcp_client())

@router.post("/process-order")
async def process_order(order: Order, service: OrderProcessingService = Depends(get_order_processing_service)) -> List[ApprovalRequest]:
    return await service.create_process_order_request(order)

@router.post("/process-order-approval")
async def process_order_approval(approval_request: ApprovalRequest, service: OrderProcessingService = Depends(get_order_processing_service)):
    return await service.order_processing_approval(approval_request)