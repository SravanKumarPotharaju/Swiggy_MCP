from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CartItemInput(BaseModel):
    menu_item_id: str = Field(..., description="Swiggy Menu Item ID (e.g. 86416530)")
    quantity: int = Field(default=1, ge=0, description="Quantity (set to 0 to remove item)")
    variants: Optional[List[Dict[str, Any]]] = Field(default=None, description="Legacy variants if applicable")
    variantsV2: Optional[List[Dict[str, Any]]] = Field(default=None, description="V2 variants if applicable")
    addons: Optional[List[Dict[str, Any]]] = Field(default=None, description="Selected addon choices")


class UpdateCartRequest(BaseModel):
    restaurant_id: str = Field(..., description="Swiggy Restaurant ID (e.g. 288893)")
    restaurant_name: Optional[str] = Field(default=None, description="Restaurant name (e.g. Meghana Foods)")
    items: List[CartItemInput] = Field(..., description="List of items with quantities")
    address_id: Optional[str] = Field(default=None, description="Delivery address ID (defaults to user's saved default address)")
    cutlery_opt_in: Optional[bool] = Field(default=False, description="Whether cutlery is requested")


class CartItemResponse(BaseModel):
    menu_item_id: str
    name: str
    quantity: int
    price: float
    subtotal: float
    image_url: Optional[str] = None
    in_stock: bool = True
    is_veg: Optional[bool] = None


class CartPricing(BaseModel):
    item_total: float = 0.0
    delivery_charge: float = 0.0
    taxes_and_charges: float = 0.0
    to_pay: float = 0.0
    discount: float = 0.0


class CartResponse(BaseModel):
    cart_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name: Optional[str] = None
    item_count: int = 0
    items: List[CartItemResponse] = []
    pricing: Optional[CartPricing] = None
    is_empty: bool = True
    address_id: Optional[str] = None


class Coupon(BaseModel):
    code: str
    title: Optional[str] = None
    description: Optional[str] = None
    discount_amount: Optional[float] = None
    is_applicable: bool = True


class CouponsResponse(BaseModel):
    coupons: List[Coupon] = []
    total_coupons: int = 0
    message: Optional[str] = None


class ApplyCouponRequest(BaseModel):
    coupon_code: str = Field(..., description="Coupon code to apply (e.g. WELCOME50, SWIGGYIT)")
    address_id: Optional[str] = Field(default=None, description="Delivery address ID")


class ApplyCouponResponse(BaseModel):
    applied: bool
    message: str
    cart: Optional[CartResponse] = None


class CartSummaryResponse(BaseModel):
    cart_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name: Optional[str] = None
    items: List[CartItemResponse] = []
    pricing: Optional[CartPricing] = None
    delivery_address: Optional[Dict[str, Any]] = None
    can_proceed_to_payment: bool = False
