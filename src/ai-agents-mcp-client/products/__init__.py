from fastapi import APIRouter
from .product_controller import router as product_module_router
from .product_performance_controller import router as performance_router

router = APIRouter()

router.include_router(product_module_router, prefix="/products", tags=["product"])
router.include_router(performance_router, prefix="/products", tags=["product-performance"])
