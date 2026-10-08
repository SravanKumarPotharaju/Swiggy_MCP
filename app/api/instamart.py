"""
FastAPI Router for Swiggy Instamart endpoints.
Exposes Instamart discovery, addresses, cart, payment, checkout, and tracking via real Swiggy MCP.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.services.instamart_service import instamart_service
from app.core.logging import logger
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError, AddressNotServiceableError
from app.schemas.common import APIResponse
from app.schemas.instamart import (
    InstamartCartUpdateRequest,
    InstamartCartItemActionRequest,
    InstamartApplyCouponRequest,
    InstamartCheckoutRequest,
    InstamartConfirmOrderRequest,
)

router = APIRouter(prefix="/instamart", tags=["Instamart"])




@router.get("/addresses", response_model=APIResponse)
async def get_instamart_addresses(request: Request):
    """
    Phase 5: Fetches the user's saved delivery addresses from Swiggy Instamart MCP.
    Internally calls `get_addresses` on https://mcp.swiggy.com/im.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        response_data = await instamart_service.get_addresses(user_id="user_default")
        return APIResponse(
            success=True,
            data=response_data.model_dump(),
            message=response_data.message or "Instamart delivery addresses retrieved successfully.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MCPConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPToolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products", response_model=APIResponse)
async def search_instamart_products(
    request: Request,
    query: str,
    address_id: str = None,
    limit: int = None,
    category: str = None,
):
    """
    Phase 6: Searches for grocery products on Swiggy Instamart for a given address.
    Returns normalized products with SKU-level `spinId` variations required for cart operations.
    """
    from fastapi.responses import JSONResponse
    from app.mcp.exceptions import AddressNotServiceableError

    request_id = getattr(request.state, "request_id", None)
    clean_query = query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query must not be empty.")

    try:
        results = await instamart_service.search_products(
            query=clean_query,
            address_id=address_id,
            limit=limit,
            category=category,
            user_id="user_default",
        )
        return APIResponse(
            success=True,
            data=results.model_dump(),
            message=f"Found {results.total} products for '{clean_query}'.",
            request_id=request_id,
        )
    except AddressNotServiceableError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "message": "Instamart is not available at this delivery address.",
                "error": {
                    "code": "ADDRESS_NOT_SERVICEABLE",
                    "message": str(e),
                    "suggestions": [
                        "Select or provide another delivery address using GET /api/v1/instamart/addresses.",
                        "Use Swiggy Food instead for meals and snacks.",
                    ],
                },
                "request_id": request_id,
            },
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MCPConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPToolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/go-to-items", response_model=APIResponse)
async def get_instamart_go_to_items(
    request: Request,
    address_id: str = None,
):
    """
    Phase 7: Fetches the user's frequently or recently purchased Instamart items for fast reordering.
    Returns SKU-level items and variants with `spinId`.
    """
    from fastapi.responses import JSONResponse
    from app.mcp.exceptions import AddressNotServiceableError

    request_id = getattr(request.state, "request_id", None)
    try:
        results = await instamart_service.get_go_to_items(
            address_id=address_id,
            user_id="user_default",
        )
        return APIResponse(
            success=True,
            data=results.model_dump(),
            message=results.message or f"Retrieved {results.total} go-to items.",
            request_id=request_id,
        )
    except AddressNotServiceableError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "message": "Instamart is not available at this delivery address.",
                "error": {
                    "code": "ADDRESS_NOT_SERVICEABLE",
                    "message": str(e),
                    "suggestions": [
                        "Select or provide another delivery address using GET /api/v1/instamart/addresses.",
                        "Use Swiggy Food instead for meals and snacks.",
                    ],
                },
                "request_id": request_id,
            },
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MCPConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPToolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cart", response_model=APIResponse)
async def get_instamart_cart(request: Request):
    """
    Phase 8: Fetches current Instamart cart and bill breakdown.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        cart = await instamart_service.get_cart(user_id="user_default")
        return APIResponse(
            success=True,
            data=cart.model_dump(),
            message="Instamart cart retrieved.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MCPConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except (MCPToolError, AddressNotServiceableError) as e:
        from app.schemas.instamart import InstamartCartResponse
        return APIResponse(
            success=True,
            data=InstamartCartResponse(items=[], total_items=0, total_amount="₹0", is_empty=True).model_dump(),
            message=f"Instamart store notice: {str(e)}",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cart", response_model=APIResponse)
@router.put("/cart", response_model=APIResponse)
async def update_instamart_cart(
    request: Request,
    body: InstamartCartUpdateRequest,
):
    """
    Phase 8: Updates the complete Instamart cart.
    Note: Replaces the entire cart with the desired list of SKU spinIds and quantities.
    """
    from fastapi.responses import JSONResponse
    from app.mcp.exceptions import AddressNotServiceableError

    request_id = getattr(request.state, "request_id", None)
    try:
        cart = await instamart_service.update_cart(
            items=body.items,
            address_id=body.address_id,
            user_id="user_default",
        )
        return APIResponse(
            success=True,
            data=cart.model_dump(),
            message=f"Instamart cart updated with {cart.total_items} items.",
            request_id=request_id,
        )
    except AddressNotServiceableError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "message": "Instamart is not available at this delivery address.",
                "error": {
                    "code": "ADDRESS_NOT_SERVICEABLE",
                    "message": str(e),
                    "suggestions": [
                        "Select or provide another delivery address using GET /api/v1/instamart/addresses.",
                        "Use Swiggy Food instead for meals and snacks.",
                    ],
                },
                "request_id": request_id,
            },
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MCPConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPToolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cart/item", response_model=APIResponse)
async def add_or_update_cart_item(
    request: Request,
    body: InstamartCartItemActionRequest,
):
    """
    Convenience endpoint: Increment, decrement, or update a single SKU item in the Instamart cart
    while preserving other existing items.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        cart = await instamart_service.add_or_update_item(
            spin_id=body.spinId,
            quantity_delta=body.quantity_delta or (1 if body.quantity is None else 0),
            absolute_quantity=body.quantity,
            address_id=body.address_id,
            user_id="user_default",
        )
        return APIResponse(
            success=True,
            data=cart.model_dump(),
            message=f"Cart item updated. Total items: {cart.total_items}.",
            request_id=request_id,
        )
    except (MCPToolError, AddressNotServiceableError, ValueError) as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "message": str(e),
                "request_id": request_id,
            },
        )
    except Exception as e:
        logger.error(f"Error in add_or_update_cart_item: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "message": str(e),
                "request_id": request_id,
            },
        )


@router.delete("/cart", response_model=APIResponse)
async def clear_instamart_cart(request: Request):
    """
    Phase 8: Clears all items from the Instamart cart.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.clear_cart(user_id="user_default")
        return APIResponse(
            success=True,
            data=res,
            message="Instamart cart cleared successfully.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except MCPConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPToolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- COUPONS (Phase 9) ---

@router.get("/coupons", response_model=APIResponse)
async def list_instamart_coupons(request: Request, address_id: str = None):
    """
    Phase 9: Lists available coupons for Instamart order.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.list_coupons(address_id=address_id, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=res.message or f"Retrieved {res.total} coupons.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coupons/apply", response_model=APIResponse)
async def apply_instamart_coupon(request: Request, body: InstamartApplyCouponRequest):
    """
    Phase 9: Applies coupon code to Instamart cart and returns refreshed cart bill.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.apply_coupon(coupon_code=body.coupon_code, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=res.message,
            request_id=request_id,
        )
    except MCPToolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- PAYMENT OPTIONS (Phase 10) ---

@router.get("/payment/options", response_model=APIResponse)
async def get_instamart_payment_options(request: Request):
    """
    Phase 10: Fetches live payment options eligible for current Instamart cart.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.get_payment_options(user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=f"Retrieved {len(res.options)} payment options.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- CHECKOUT (Phase 11 & 12) ---

@router.post("/checkout", response_model=APIResponse)
async def checkout_instamart(request: Request, body: InstamartCheckoutRequest):
    """
    Phase 11 & 12: Executes mutating Instamart checkout with explicit confirmation.
    Returns PENDING_PAYMENT status and UPI Intent / QR payload.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.checkout(request=body, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=res.message,
            request_id=request_id,
        )
    except AddressNotServiceableError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "message": "Instamart is not available at this delivery address.",
                "error": {
                    "code": "ADDRESS_NOT_SERVICEABLE",
                    "message": str(e),
                    "suggestions": [
                        "Select or provide another delivery address using GET /api/v1/instamart/addresses.",
                        "Use Swiggy Food instead for meals and snacks.",
                    ],
                },
                "request_id": request_id,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=409 if "confirmation" in str(e).lower() else 400, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- PAYMENT STATUS & ORDER CONFIRMATION (Phase 13 & 14) ---

@router.get("/payments/{paas_id}/status", response_model=APIResponse)
async def check_instamart_payment_status(
    request: Request,
    paas_id: str,
    order_id: str = None,
):
    """
    Phase 13: Checks status of pending UPI / Gateway payment.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.check_payment_status(paas_id=paas_id, order_id=order_id, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=res.message,
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/confirm", response_model=APIResponse)
async def confirm_instamart_order(request: Request, order_id: str):
    """
    Phase 14: Confirms Instamart order after payment confirmation.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.confirm_order(order_id=order_id, user_id="user_default")
        return APIResponse(
            success=True,
            data=res,
            message="Instamart order confirmed.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ORDERS & TRACKING (Phase 15 & 16) ---

@router.get("/orders", response_model=APIResponse)
async def get_instamart_orders(request: Request):
    """
    Phase 15: Fetches past and active Instamart orders.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.get_orders(user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=f"Retrieved {res.total} orders.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=APIResponse)
async def get_instamart_order_details(request: Request, order_id: str):
    """
    Phase 15: Fetches receipt and items for a specific Instamart order.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.get_order_details(order_id=order_id, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message="Order details retrieved.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/delivery-status", response_model=APIResponse)
async def get_instamart_delivery_status(request: Request, order_id: str):
    """
    Phase 16: Fetches lightweight delivery status and ETA.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.get_delivery_status(order_id=order_id, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=f"Order status: {res.status}",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/tracking", response_model=APIResponse)
async def track_instamart_order(request: Request, order_id: str):
    """
    Phase 16: Fetches full live tracking with partner location and status.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await instamart_service.track_order(order_id=order_id, user_id="user_default")
        return APIResponse(
            success=True,
            data=res.model_dump(),
            message=f"Live tracking for order {order_id}.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




