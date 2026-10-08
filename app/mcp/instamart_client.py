"""
Swiggy Instamart MCP Client.
Connects to https://mcp.swiggy.com/im using authenticated OAuth sessions.
"""

from app.mcp.client import InstamartMCPClient, instamart_mcp_client

__all__ = ["InstamartMCPClient", "instamart_mcp_client"]
