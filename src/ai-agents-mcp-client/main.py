from fastapi import FastAPI
import uvicorn
import logging
import os
from dotenv import load_dotenv

from colorama import Fore, Style
from core.client_manager import ClientManager
from core.vector_db import VectorDatabase
from products import router as product_module_router
from products.product_performance_controller import router as performance_router
from recommendations.recommendations_controller import router as recommendations_router

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

@app.on_event("startup")
async def startup_event():
    server_script_path = os.getenv("MCP_SERVER_SCRIPT_PATH")
    if not server_script_path:
        raise ValueError("MCP_SERVER_SCRIPT_PATH environment variable is not set")
    await ClientManager.initialize(server_script_path)
    logger.info("MCP Client initialized successfully")
    
    # Initialize vector database
    mongodb_uri = os.getenv("MONGODB_URI")
    if VectorDatabase.initialize(mongodb_uri):
        logger.info("Vector database initialized successfully")
    else:
        logger.warning("Vector database initialization failed. Vector search functionality may be limited.")

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
app.include_router(recommendations_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 