from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
import uvicorn
import logging
import os
from dotenv import load_dotenv

from colorama import Fore, Style
from products.product_dto import ProductRequest, ProductResponse
from mcp_client import MCPClient
from products.product_service import ProductService

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

mcp_client = MCPClient()

@app.on_event("startup")
async def startup_event():
    server_script_path = os.getenv("MCP_SERVER_SCRIPT_PATH", "path/to/your/server/script.py")
    await mcp_client.connect_to_server(server_script_path)

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_client.exit_stack.aclose()

def get_product_service() -> ProductService:
    return ProductService(mcp_client)

@app.get("/health-check")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 