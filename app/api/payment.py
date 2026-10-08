from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from app.services.payment_service import payment_service
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError
from app.schemas.common import APIResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


from app.core.dependencies import get_current_user_id

@router.get("/options", response_model=APIResponse)
async def get_payment_options(
    request: Request,
    address_id: Optional[str] = Query(None, description="Delivery address ID (defaults to saved default address)"),
):
    """
    Phase 10: Fetch live available payment options for the active cart (Mobile UPI apps, Scan QR, COD).
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = get_current_user_id(request)
    try:
        data = await payment_service.get_payment_options(address_id=address_id, user_id=user_id)
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Retrieved {len(data.all_methods)} payment methods for ₹{data.payment_amount}.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{paas_id}/status", response_model=APIResponse)
async def check_payment_status(
    request: Request,
    paas_id: str,
    order_id: Optional[str] = Query(None, description="Order ID from checkout response"),
    address_id: Optional[str] = Query(None, description="Delivery address ID"),
):
    """
    Phase 12: Check the real-time status of an in-flight payment transaction.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await payment_service.check_payment_status(
            paas_id=paas_id,
            order_id=order_id,
            address_id=address_id,
        )
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Payment status is {data.status}.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
