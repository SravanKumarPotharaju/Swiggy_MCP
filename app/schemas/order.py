from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    payment_method: str = Field(default="UPI", description="'UPI' (Cash on Delivery is disabled)")
    intent_app: Optional[str] = Field(default=None, description="UPI intent app ID (e.g. gpay://upi/, phonepe://)")
    generate_upi_qr: Optional[bool] = Field(default=False, description="Set True to generate UPI QR code")
    address_id: Optional[str] = Field(default=None, description="Delivery address ID")
    note_to_restaurant: Optional[str] = Field(default=None, description="Instructions to restaurant")


class CheckoutResponse(BaseModel):
    order_id: str
    paas_id: Optional[str] = None
    status: str
    payment_method: str
    total_amount: Optional[float] = None
    upi_intent_url: Optional[str] = None
    upi_qr_data: Optional[str] = None
    requires_payment: bool = False
    message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class ConfirmOrderRequest(BaseModel):
    order_id: str
    address_id: Optional[str] = None
    cart_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class OrderSummary(BaseModel):
    order_id: str
    restaurant_name: str
    restaurant_id: Optional[str] = None
    order_total: str
    order_status: str
    ordered_items: str
    ordered_time: Optional[str] = None
    is_active: bool = False


class OrderHistoryResponse(BaseModel):
    orders: List[OrderSummary] = []
    total: int = 0


class OrderDetailsResponse(BaseModel):
    order_id: str
    details_text: str


class OrderTrackingResponse(BaseModel):
    order_id: Optional[str] = None
    status: str
    status_message: str
    eta_text: Optional[str] = None
    title: Optional[str] = None
    progress_percentage: Optional[int] = None
    raw_tracking: Optional[Dict[str, Any]] = None
