from typing import Optional
from mcp_client import MCPClient

class ClientManager:
    _instance = None
    _mcp_client: Optional[MCPClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_mcp_client(cls) -> MCPClient:
        if cls._mcp_client is None:
            cls._mcp_client = MCPClient()
        return cls._mcp_client

    @classmethod
    async def initialize(cls, server_script_path: str):
        client = cls.get_mcp_client()
        await client.connect_to_server(server_script_path)

    @classmethod
    async def cleanup(cls):
        if cls._mcp_client:
            await cls._mcp_client.exit_stack.aclose()
            cls._mcp_client = None 