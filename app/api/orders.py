from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from app.services.order_service import order_service
from app.schemas.order import (
    CheckoutRequest,
    ConfirmOrderRequest,
)
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError
from app.schemas.common import APIResponse

from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/checkout", response_model=APIResponse)
async def checkout(
    request: Request,
    body: CheckoutRequest,
):
    """
    Phase 11: Place order and initiate checkout on Swiggy MCP.
    Returns orderId, paasId, payment amount, and UPI Intent / QR payload.
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = get_current_user_id(request)
    try:
        data = await order_service.checkout(body, user_id=user_id)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=data.message or f"Order {data.order_id} created with status {data.status}.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/confirm", response_model=APIResponse)
async def confirm_order(
    request: Request,
    order_id: str,
    address_id: Optional[str] = Query(None, description="Delivery address ID"),
    cart_id: Optional[str] = Query(None, description="Cart ID from checkout"),
    lat: Optional[float] = Query(None, description="Delivery latitude"),
    lng: Optional[float] = Query(None, description="Delivery longitude"),
):
    """
    Phase 12: Finalize an order from PENDING_PAYMENT to PLACED status upon successful payment.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        req = ConfirmOrderRequest(
            order_id=order_id,
            address_id=address_id,
            cart_id=cart_id,
            lat=lat,
            lng=lng,
        )
        res = await order_service.confirm_order(req)
        return APIResponse(
            success=True,
            data=res,
            message=f"Order {order_id} confirmed and placed successfully.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=APIResponse)
async def get_orders(
    request: Request,
    active_only: bool = Query(False, description="Filter only in-flight / active orders"),
    count: int = Query(5, ge=1, le=15, description="Number of past orders (max 15)"),
    address_id: Optional[str] = Query(None, description="Delivery address ID"),
):
    """
    Phase 13: Fetch order history and active orders.
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = get_current_user_id(request)
    try:
        data = await order_service.get_orders(
            active_only=active_only,
            count=count,
            address_id=address_id,
            user_id=user_id,
        )
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Retrieved {data.total} orders.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/frequent", response_model=APIResponse)
async def get_frequent_orders(
    request: Request,
    threshold: int = Query(3, ge=1, description="Order count threshold"),
):
    """
    Returns restaurants and Instamart stores ordered MORE THAN threshold TIMES.
    Also returns raw counts_by_restaurant so UI components can evaluate custom thresholds (e.g. > 2).
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = get_current_user_id(request)
    if hasattr(threshold, "default"):
        threshold = threshold.default
    threshold = int(threshold)
    try:
        data = await order_service.get_orders(count=15, user_id=user_id)
        rest_counts = {}
        im_order_count = 0
        for o in data.orders:
            r = (o.restaurant_name or "").strip()
            if not r or r.lower() == "unknown":
                continue
            if "instamart" in r.lower():
                im_order_count += 1
            else:
                rest_counts[r] = rest_counts.get(r, 0) + 1
        
        frequent_restaurants = []
        for r_name, cnt in rest_counts.items():
            if cnt > threshold:
                frequent_restaurants.append({
                    "restaurant_name": r_name,
                    "order_count": cnt,
                    "display_text": f"🔥 {r_name} (Ordered {cnt} times)",
                })
        
        frequent_restaurants.sort(key=lambda x: x["order_count"], reverse=True)

        return APIResponse(
            success=True,
            data={
                "frequent_restaurants": frequent_restaurants,
                "counts_by_restaurant": rest_counts,
                "instamart": {
                    "order_count": im_order_count,
                    "is_frequent": im_order_count > threshold,
                    "display_text": f"⚡ Instamart (Ordered {im_order_count} times)" if im_order_count > threshold else None,
                },
                "threshold": threshold,
            },
            message="Frequent orders calculated.",
            request_id=request_id,
        )
    except Exception as e:
        return APIResponse(
            success=True,
            data={"frequent_restaurants": [], "instamart": {"order_count": 0, "is_frequent": False}, "threshold": 3},
            message="No frequent orders.",
            request_id=request_id,
        )


@router.get("/{order_id}", response_model=APIResponse)
async def get_order_details(
    request: Request,
    order_id: str,
):
    """
    Phase 14: Get detailed receipt and items for a specific order.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await order_service.get_order_details(order_id)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Order details retrieved for {order_id}.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}/track", response_model=APIResponse)
async def track_order(
    request: Request,
    order_id: str,
):
    """
    Phase 15: Track live order preparation and delivery ETA.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await order_service.track_order(order_id)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=data.status_message or f"Tracking status: {data.status}",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
