"""
Pydantic Schemas for Swiggy Instamart integration.
Follows official Swiggy Instamart MCP specifications without fabricating fields.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- ADDRESS SCHEMAS ---

class InstamartAddress(BaseModel):
    id: str = Field(..., description="Unique address identifier on Swiggy Instamart")
    label: str = Field(..., description="Address tag or category (e.g. Home, Work, Hostel)")
    display_text: str = Field(..., description="Full street and building address line")
    phone_number: Optional[str] = Field(None, description="Phone number associated with address")
    category: Optional[str] = Field(None, description="Category returned by Swiggy (Home, Work, Other)")
    is_default: bool = Field(False, description="Whether this is the user's default delivery address")
    raw: Optional[Dict[str, Any]] = Field(None, description="Original Swiggy address payload")


class InstamartAddressListResponse(BaseModel):
    addresses: List[InstamartAddress] = Field(default_factory=list)
    total: int = 0
    default_address_id: Optional[str] = None
    requires_address_selection: bool = False
    message: Optional[str] = None


class InstamartAddressCreateRequest(BaseModel):
    full_address: str = Field(..., description="Full street address including city and pincode")
    address_line: Optional[str] = Field(None, description="Door/Flat/Building details")
    address_line2: Optional[str] = Field(None, description="Landmark or additional street details")
    locality: Optional[str] = Field(None, description="Area/Locality")
    city: Optional[str] = Field("Bengaluru", description="City")
    postal_code: Optional[str] = Field("560010", description="Postal / PIN code")
    address_category: Optional[str] = Field("HOME", description="HOME, WORK, or OTHER")
    address_tag: Optional[str] = Field("Home", description="Display label tag")
    user_name: Optional[str] = Field("Sravan Kumar", description="Recipient name")
    user_phone: Optional[str] = Field(None, description="10-digit mobile number")


# --- DISCOVERY SCHEMAS (Prepared for Phase 6 & 7) ---

class InstamartProductVariant(BaseModel):
    spin_id: str = Field(..., description="SKU-level variant identifier required for cart")
    name: str = Field(..., description="Variant name / pack size")
    price: Optional[float] = Field(None, description="Price in INR")
    mrp: Optional[float] = Field(None, description="Maximum retail price in INR")
    quantity_description: Optional[str] = Field(None, description="e.g. 500 ml, 1 kg")
    available: bool = Field(True, description="Whether this SKU is currently in stock")
    raw: Optional[Dict[str, Any]] = None


class InstamartProduct(BaseModel):
    product_id: str = Field(..., description="Parent product identifier")
    name: str = Field(..., description="Product name")
    brand: Optional[str] = Field(None, description="Brand name if returned")
    image: Optional[str] = Field(None, description="Product image URL if returned")
    description: Optional[str] = Field(None, description="Product description")
    variants: List[InstamartProductVariant] = Field(default_factory=list)
    similar_products: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None


class InstamartSearchResponse(BaseModel):
    products: List[InstamartProduct] = Field(default_factory=list)
    total: int = 0
    query: str
    address_id: str


class InstamartGoToItemsResponse(BaseModel):
    products: List[InstamartProduct] = Field(default_factory=list)
    total: int = 0
    address_id: str
    message: Optional[str] = None



# --- CART SCHEMAS (Phase 8) ---

class InstamartCartItemInput(BaseModel):
    spinId: str = Field(..., description="SKU-level variant spinId")
    quantity: int = Field(..., ge=0, description="Quantity to set in cart (0 removes item)")


class InstamartCartUpdateRequest(BaseModel):
    items: List[InstamartCartItemInput] = Field(..., description="Complete desired list of cart items with spinId and quantity")
    address_id: Optional[str] = Field(None, description="Optional delivery address ID (defaults to active address)")


class InstamartCartItemActionRequest(BaseModel):
    spinId: str = Field(..., description="SKU-level variant spinId")
    quantity_delta: Optional[int] = Field(None, description="Increment or decrement by this amount (e.g. +1 or -1)")
    quantity: Optional[int] = Field(None, description="Absolute quantity to set (0 removes item)")
    address_id: Optional[str] = Field(None, description="Optional delivery address ID")


class InstamartCartItem(BaseModel):
    spin_id: str
    sku_id: Optional[str] = None
    product_id: Optional[str] = None
    name: str
    variant: Optional[str] = None
    quantity: int
    price: float
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    is_available: bool = True
    max_quantity: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None


class InstamartBillLineItem(BaseModel):
    label: str
    value: str


class InstamartBillBreakdown(BaseModel):
    line_items: List[InstamartBillLineItem] = Field(default_factory=list)
    to_pay_label: str = "To Pay"
    to_pay_value: str = "0"


class InstamartCartResponse(BaseModel):
    cart_id: Optional[str] = None
    items: List[InstamartCartItem] = Field(default_factory=list)
    total_items: int = 0
    total_amount: str = "₹0"
    bill_breakdown: Optional[InstamartBillBreakdown] = None
    selected_address_id: Optional[str] = None
    selected_address: Optional[Dict[str, Any]] = None
    is_empty: bool = True
    raw: Optional[Dict[str, Any]] = None



# --- COUPON SCHEMAS (Phase 9) ---

class InstamartCoupon(BaseModel):
    code: str
    title: Optional[str] = None
    description: Optional[str] = None
    discount_amount: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None


class InstamartCouponListResponse(BaseModel):
    coupons: List[InstamartCoupon] = Field(default_factory=list)
    total: int = 0
    message: Optional[str] = None


class InstamartApplyCouponRequest(BaseModel):
    coupon_code: str = Field(..., description="Coupon code to apply")


class InstamartApplyCouponResponse(BaseModel):
    applied: bool
    coupon_code: str
    message: str
    cart: InstamartCartResponse


# --- PAYMENT OPTIONS SCHEMAS (Phase 10) ---

class InstamartPaymentOption(BaseModel):
    method: str = Field(..., description="UPI, Cash, Card, NetBanking")
    display_name: str
    intent_app_id: Optional[str] = None
    is_eligible: bool = True
    raw: Optional[Dict[str, Any]] = None


class InstamartPaymentOptionsResponse(BaseModel):
    options: List[InstamartPaymentOption] = Field(default_factory=list)
    payment_amount: Optional[str] = None
    agentic_eligible: bool = False
    raw: Optional[Dict[str, Any]] = None


# --- CHECKOUT SCHEMAS (Phase 11 & 12) ---

class InstamartCheckoutRequest(BaseModel):
    address_id: Optional[str] = Field(None, description="Selected delivery address ID (defaults to active address)")
    payment_method: str = Field("UPI", description="UPI or Cash (if available)")
    intent_app: Optional[str] = Field(None, description="UPI app ID returned by get_payment_options")
    generate_upi_qr: bool = Field(True, description="Generate UPI QR for web checkout")
    user_confirmed: bool = Field(False, description="Explicit user confirmation flag required before checkout")


class InstamartCheckoutResponse(BaseModel):
    order_id: str
    status: str = Field(..., description="PENDING_PAYMENT, PLACED, etc.")
    total_amount: str
    paas_id: Optional[str] = None
    transaction_id: Optional[str] = None
    upi_intent_url: Optional[str] = None
    upi_qr_data: Optional[str] = None
    is_qr_flow: bool = False
    polling_interval_ms: int = 5000
    max_time_to_poll_ms: int = 300000
    payment_method: str = "UPI"
    message: str = "Instamart order initiated."
    raw: Optional[Dict[str, Any]] = None


# --- PAYMENT STATUS & ORDER CONFIRMATION SCHEMAS (Phase 13 & 14) ---

class InstamartPaymentStatusResponse(BaseModel):
    status: str = Field(..., description="PAYMENT_SUCCESS, PAYMENT_PENDING, PAYMENT_FAILED, PAYMENT_CANCELLED")
    paas_id: str
    order_id: Optional[str] = None
    message: str
    raw: Optional[Dict[str, Any]] = None


class InstamartConfirmOrderRequest(BaseModel):
    order_id: str


# --- ORDERS & TRACKING SCHEMAS (Phase 15 & 16) ---

class InstamartOrder(BaseModel):
    order_id: str
    status: str
    placed_at: Optional[str] = None
    total_amount: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None


class InstamartOrderListResponse(BaseModel):
    orders: List[InstamartOrder] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


class InstamartDeliveryStatusResponse(BaseModel):
    order_id: str
    status: str
    eta_minutes: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None


class InstamartTrackingResponse(BaseModel):
    order_id: str
    status: str
    eta_minutes: Optional[int] = None
    delivery_partner: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None

