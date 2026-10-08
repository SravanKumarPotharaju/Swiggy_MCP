from typing import Optional
from pydantic import BaseModel


class LoginInitiateResponse(BaseModel):
    authorization_url: str
    state: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user_id: Optional[str] = None
    expires_at: Optional[str] = None
    scope: Optional[str] = None
    message: Optional[str] = None


class CallbackResponse(BaseModel):
    authenticated: bool
    user_id: str
    message: str


class SendOtpRequest(BaseModel):
    phone: str
    country_code: str = "+91"


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str
