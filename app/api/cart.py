from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from app.services.cart_service import cart_service
from app.schemas.cart import UpdateCartRequest, ApplyCouponRequest
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError
from app.schemas.common import APIResponse

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=APIResponse)
async def get_cart(
    request: Request,
    address_id: Optional[str] = Query(None, description="Delivery address ID (defaults to saved default address)"),
):
    """
    Phase 8: Retrieve the current live food cart and pricing breakdown from Swiggy MCP.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await cart_service.get_cart(address_id=address_id)
        msg = "Cart is empty." if data.is_empty else f"Cart retrieved with {data.item_count} items."
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=msg,
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=APIResponse)
async def update_cart(
    request: Request,
    cart_update: UpdateCartRequest,
):
    """
    Phase 8: Add, update, or remove items in the Swiggy Food cart.
    Note: Setting quantity to 0 removes the item from the cart.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await cart_service.update_cart(cart_update)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Cart updated. Total to pay: ₹{data.pricing.to_pay if data.pricing else 0}",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("", response_model=APIResponse)
async def flush_cart(request: Request):
    """
    Phase 8: Clear/flush the entire food cart on Swiggy MCP.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        await cart_service.flush_cart()
        return APIResponse(
            success=True,
            data={"cleared": True},
            message="Food cart cleared successfully.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/coupons", response_model=APIResponse)
async def get_coupons(
    request: Request,
    restaurant_id: str = Query(..., description="Swiggy Restaurant ID"),
    address_id: Optional[str] = Query(None, description="Delivery address ID (defaults to saved default address)"),
):
    """
    Phase 9: Fetch available discount coupons for the current restaurant & location.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await cart_service.fetch_coupons(restaurant_id=restaurant_id, address_id=address_id)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Found {data.total_coupons} available coupon(s).",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/coupons/apply", response_model=APIResponse)
async def apply_coupon(
    request: Request,
    body: ApplyCouponRequest,
):
    """
    Phase 9: Apply a promotional coupon to the active food cart.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await cart_service.apply_coupon(
            coupon_code=body.coupon_code,
            address_id=body.address_id,
        )
        return APIResponse(
            success=data.applied,
            data=data.model_dump(),
            message=data.message,
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary", response_model=APIResponse)
async def get_cart_summary(
    request: Request,
    address_id: Optional[str] = Query(None, description="Delivery address ID (defaults to saved default address)"),
):
    """
    Phase 9: Get complete cart summary & breakdown for explicit user confirmation before order placement.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await cart_service.get_cart_summary(address_id=address_id)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message="Order preview generated. Awaiting user confirmation to proceed to checkout.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
