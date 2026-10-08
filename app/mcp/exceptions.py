class MCPError(Exception):
    """Base exception for MCP operations."""
    pass


class MCPConnectionError(MCPError):
    """Raised when unable to reach the MCP server."""
    pass


class MCPAuthenticationError(MCPError):
    """Raised when the session is invalid or expired (401)."""
    pass


class MCPToolError(MCPError):
    """Raised when a tool execution returns an error from upstream."""
    pass


class AddressNotServiceableError(MCPError):
    """Raised when Swiggy Instamart cannot deliver to the selected address."""
    pass

