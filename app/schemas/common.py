from typing import Any, Optional, Dict
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    request_id: Optional[str] = None


class APIErrorDetails(BaseModel):
    code: str
    details: Optional[Dict[str, Any]] = None


class APIErrorResponse(BaseModel):
    success: bool = False
    data: Optional[Any] = None
    message: str
    error: APIErrorDetails
    request_id: Optional[str] = None
