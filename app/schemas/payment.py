from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentMethodOption(BaseModel):
    id: str = Field(..., description="Method identifier (e.g. gpay://upi/, PayWithQR, COD)")
    display_name: str
    group_name: str
    kind: Optional[str] = None  # "intent", "qr", "cod"
    icon_url: Optional[str] = None
    enabled: bool = True


class PaymentOptionsResponse(BaseModel):
    payment_amount: float
    all_methods: List[PaymentMethodOption] = []
    mobile_upi_methods: List[PaymentMethodOption] = []
    desktop_qr_available: bool = False
    cod_available: bool = False
    agentic_payment_eligible: bool = False
    address_id: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    paas_id: str
    order_id: Optional[str] = None
    status: str
    is_terminal: bool = False
    raw_response: Optional[Dict[str, Any]] = None
