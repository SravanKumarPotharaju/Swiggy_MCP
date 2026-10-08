from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from app.services.restaurant_service import restaurant_service
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError
from app.schemas.common import APIResponse

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.get("", response_model=APIResponse)
async def search_restaurants(
    request: Request,
    query: str = Query("biryani", description="Search keyword for food or restaurant"),
    address_id: Optional[str] = Query(None, description="Delivery address ID (defaults to saved default address)"),
    cuisine: Optional[str] = Query(None, description="Optional cuisine filter (e.g. North Indian, Biryani)"),
    limit: Optional[int] = Query(10, description="Max restaurants to return"),
):
    """
    Phase 6: Search restaurants available at the delivery location via Swiggy MCP.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await restaurant_service.search_restaurants(
            query=query,
            address_id=address_id,
            cuisine=cuisine,
            limit=limit,
        )
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Found {data.total} restaurants for '{query}'.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{restaurant_id}/menu", response_model=APIResponse)
async def get_restaurant_menu(
    request: Request,
    restaurant_id: str,
    address_id: Optional[str] = Query(None, description="Delivery address ID (defaults to saved default address)"),
):
    """
    Phase 7: Browse a restaurant's categorized menu with exact dish IDs, prices, variants & add-ons.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await restaurant_service.get_menu(
            restaurant_id=restaurant_id,
            address_id=address_id,
        )
        return APIResponse(
            success=True,
            data=data.model_dump(),
            message=f"Retrieved menu for restaurant {restaurant_id}.",
            request_id=request_id,
        )
    except MCPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except (MCPConnectionError, MCPToolError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
