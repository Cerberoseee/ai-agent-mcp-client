from fastapi import APIRouter
from .product_controller import router as product_module_router

router = APIRouter()

router.include_router(product_module_router, prefix="/products", tags=["product"])