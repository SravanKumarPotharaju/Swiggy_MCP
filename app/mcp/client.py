import uuid
import httpx
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.auth_service import auth_service
from app.mcp.exceptions import MCPConnectionError, MCPAuthenticationError, MCPToolError


class SwiggyMCPClient:
    def __init__(self, base_url: Optional[str] = None, service_name: str = "Swiggy"):
        self.base_url = base_url or settings.SWIGGY_MCP_URL
        self.service_name = service_name

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        user_id: str = "user_default",
    ) -> Dict[str, Any]:
        """Calls a tool on the Swiggy MCP server using the authenticated session."""
        token = await auth_service.get_valid_token(user_id)
        if not token:
            raise MCPAuthenticationError("No active or valid Swiggy session. Please authenticate via /api/v1/auth/login.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        rpc_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }

        logger.info(f"Calling {self.service_name} MCP tool '{tool_name}' (RPC ID: {rpc_id})")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(self.base_url, json=payload, headers=headers)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error(f"Failed to connect to {self.service_name} MCP: {e}")
            raise MCPConnectionError(f"Could not connect to {self.service_name} MCP server: {e}")

        if res.status_code == 401:
            logger.warning(f"{self.service_name} token expired or rejected (401).")
            raise MCPAuthenticationError(f"{self.service_name} session has expired. Please re-authenticate.")

        if res.status_code != 200:
            logger.error(f"{self.service_name} MCP error {res.status_code}: {res.text}")
            raise MCPConnectionError(f"{self.service_name} MCP server returned HTTP {res.status_code}: {res.text}")

        try:
            data = res.json()
        except Exception:
            raise MCPToolError(f"Failed to parse JSON response from {self.service_name} MCP.")

        if "error" in data:
            err = data["error"]
            err_msg = err.get("message", f"Unknown {self.service_name} MCP tool error")
            logger.error(f"{self.service_name} MCP tool error: {err}")
            raise MCPToolError(err_msg)

        result = data.get("result", {})
        return result


class FoodMCPClient(SwiggyMCPClient):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url=base_url or settings.SWIGGY_MCP_URL, service_name="Food")


class InstamartMCPClient(SwiggyMCPClient):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url=base_url or settings.INSTAMART_MCP_URL, service_name="Instamart")


food_mcp_client = FoodMCPClient()
instamart_mcp_client = InstamartMCPClient()
# Preserve mcp_client for backwards compatibility with existing food modules
mcp_client = food_mcp_client

