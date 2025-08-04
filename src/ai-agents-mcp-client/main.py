from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

from colorama import Fore, Style
from core.client_manager import ClientManager
from core.vector_db import VectorDatabase
from products import router as product_module_router
from products.product_performance_controller import router as performance_router
from recommendations.recommendations_controller import router as recommendations_router
from order_processing.order_processing_controller import router as order_processing_router

# Import error handling
from exceptions.service_exceptions import (
    ServiceError, AIServiceError, MCPConnectionError, 
    ConfigurationError, ValidationError, TimeoutError, VectorDatabaseError
)
from schemas.error_schemas import StandardErrorResponse, ErrorDetail, ErrorCode

load_dotenv()

class ColorizingStreamHandler(logging.StreamHandler):
    color_map = {
        logging.INFO: Fore.WHITE,
        logging.ERROR: Fore.RED,
        logging.DEBUG: Fore.WHITE,
        logging.WARNING: Fore.BLUE,
    }

    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(
                self.color_map.get(record.levelno, Style.RESET_ALL)
                + msg
                + Style.RESET_ALL
                + "\n"
            )
            self.flush()
        except Exception:
            self.handleError(record)


# Config logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = ColorizingStreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

app = FastAPI(
    title="AI Agents API",
    description="API for AI agents",
    version="1.0.0",
    docs_url="/docs",
)

# Error handlers for different exception types
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content=StandardErrorResponse(
            error_code=exc.error_code or ErrorCode.VALIDATION_ERROR,
            message=str(exc),
            details=exc.details,
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(MCPConnectionError)
async def mcp_connection_error_handler(request, exc: MCPConnectionError):
    return JSONResponse(
        status_code=503,
        content=StandardErrorResponse(
            error_code=exc.error_code or ErrorCode.MCP_CONNECTION_ERROR,
            message=str(exc),
            details=exc.details,
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(AIServiceError)
async def ai_service_error_handler(request, exc: AIServiceError):
    return JSONResponse(
        status_code=502,
        content=StandardErrorResponse(
            error_code=exc.error_code or ErrorCode.AI_SERVICE_ERROR,
            message=str(exc),
            details=exc.details,
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(TimeoutError)
async def timeout_error_handler(request, exc: TimeoutError):
    return JSONResponse(
        status_code=408,
        content=StandardErrorResponse(
            error_code=exc.error_code or ErrorCode.TIMEOUT_ERROR,
            message=str(exc),
            details=exc.details,
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(VectorDatabaseError)
async def vector_db_error_handler(request, exc: VectorDatabaseError):
    return JSONResponse(
        status_code=503,
        content=StandardErrorResponse(
            error_code=exc.error_code or ErrorCode.VECTOR_DB_ERROR,
            message=str(exc),
            details=exc.details,
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(ServiceError)
async def service_error_handler(request, exc: ServiceError):
    return JSONResponse(
        status_code=500,
        content=StandardErrorResponse(
            error_code=exc.error_code or ErrorCode.INTERNAL_ERROR,
            message=str(exc),
            details=exc.details,
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(Exception)
async def general_error_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=StandardErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            details={"exception_type": type(exc).__name__},
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.on_event("startup")
async def startup_event():
    try:
        server_script_path = os.getenv("MCP_SERVER_SCRIPT_PATH")
        if not server_script_path:
            raise ConfigurationError("MCP_SERVER_SCRIPT_PATH environment variable is not set", "MISSING_CONFIG")
        
        await ClientManager.initialize(server_script_path)
        logger.info("MCP Client initialized successfully")
        
        # Initialize vector database with error handling
        try:
            if VectorDatabase.initialize():
                logger.info("Vector database initialized successfully")
            else:
                raise VectorDatabaseError("Vector database initialization failed", "VECTOR_DB_INIT_FAILED")
        except Exception as e:
            logger.warning(f"Vector database initialization failed: {str(e)}. Vector search functionality may be limited.")
            # Don't fail startup for vector DB issues, just log the warning
            
    except (ConfigurationError, MCPConnectionError) as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected startup error: {str(e)}")
        raise ConfigurationError(f"Startup failed: {str(e)}", "STARTUP_ERROR")

@app.on_event("shutdown")
async def shutdown_event():
    await ClientManager.cleanup()
    logger.info("MCP Client cleaned up successfully")
    
    # Clean up vector database connection
    VectorDatabase.cleanup()
    logger.info("Vector database connection closed")

@app.get("/health-check")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(product_module_router)
app.include_router(performance_router, prefix="/products", tags=["product-performance"])
app.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
app.include_router(order_processing_router, prefix="/order-processing", tags=["order-processing"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 