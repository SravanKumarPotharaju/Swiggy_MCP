from typing import List, Optional
from pydantic import BaseModel, Field


# Auth Schemas
class LoginRequest(BaseModel):
    phone_or_email: str
    password: Optional[str] = None
    otp: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Address Schemas
class AddressBase(BaseModel):
    title: str = "Home"
    street: str
    city: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: str


# Restaurant & Food Schemas
class MenuItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True


class RestaurantResponse(BaseModel):
    id: str
    name: str
    cuisine: List[str] = []
    rating: float = 0.0
    menu: List[MenuItem] = []


# Cart Schemas
class CartItem(BaseModel):
    item_id: str
    name: str
    quantity: int = 1
    price: float


class CartResponse(BaseModel):
    items: List[CartItem] = []
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    total: float = 0.0


# Payment Schemas
class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    payment_method: str = "card"


class PaymentResponse(BaseModel):
    transaction_id: str
    order_id: str
    status: str
    amount: float


# Order Schemas
class OrderCreate(BaseModel):
    restaurant_id: str
    items: List[CartItem]
    address_id: str
    payment_method: str = "card"


class OrderResponse(BaseModel):
    order_id: str
    status: str
    total_amount: float
    restaurant_id: str
    items: List[CartItem]
    created_at: Optional[str] = None


# Tracking Schemas
class TrackingStatusResponse(BaseModel):
    order_id: str
    status: str
    estimated_arrival_minutes: Optional[int] = None
    driver_latitude: Optional[float] = None
    driver_longitude: Optional[float] = None
    updated_at: Optional[str] = None
