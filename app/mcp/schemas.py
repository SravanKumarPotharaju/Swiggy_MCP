from typing import Any, Dict, Optional
from pydantic import BaseModel


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    tool_name: str
    result: Any
    success: bool = True
    error: Optional[str] = None
