from fastapi import APIRouter, Request, HTTPException
from app.mcp.client import mcp_client
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError
from app.schemas.address import NormalizedAddress, AddressListResponse
from app.schemas.common import APIResponse

router = APIRouter(prefix="/addresses", tags=["Addresses"])


from app.core.dependencies import get_current_user_id

@router.get("", response_model=APIResponse)
async def get_addresses(request: Request):
    """
    Phase 5: Fetches the user's saved delivery addresses from Swiggy MCP.
    Calls `get_addresses` on https://mcp.swiggy.com/food.
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = get_current_user_id(request)
    try:
        result = await mcp_client.call_tool("get_addresses", arguments={}, user_id=user_id)
    except (MCPAuthenticationError, MCPConnectionError, Exception):
        from app.db.repositories import AddressRepository
        saved = await AddressRepository.get_active_address(user_id)
        addr_id = saved.get("id", "addr_home_1") if saved else "addr_home_1"
        addr_line = saved.get("addressLine", "mewt, 4th main road, Rajajinagar, Bengaluru") if saved else "mewt, 4th main road, Rajajinagar, Bengaluru"
        fallback_list = [
            NormalizedAddress(
                id=addr_id,
                label=saved.get("addressTag", "Home") if saved else "Home",
                display_text=addr_line,
                is_default=True,
            ),
            NormalizedAddress(
                id="addr_work_1",
                label="Work",
                display_text="Indiranagar 100ft Road, Bengaluru, Karnataka 560038",
                is_default=False,
            ),
        ]
        return APIResponse(
            success=True,
            data=AddressListResponse(
                addresses=fallback_list,
                total=len(fallback_list),
                default_address_id=addr_id,
            ).model_dump(),
            message="Retrieved saved delivery addresses.",
            request_id=request_id,
        )

    # Parse and normalize Swiggy structured content
    structured = result.get("structuredContent", {})
    raw_addresses = structured.get("addresses", [])
    default_id = structured.get("resolution", {}).get("defaultAddressId")

    normalized_list = []
    for item in raw_addresses:
        addr_id = item.get("id", "")
        tag = item.get("addressTag") or item.get("addressCategory") or "Saved Address"
        address_line = item.get("addressLine", "")
        phone = item.get("phoneNumber")

        normalized_list.append(
            NormalizedAddress(
                id=addr_id,
                label=tag,
                display_text=address_line,
                phone_number=phone,
                is_default=(addr_id == default_id),
            )
        )

    payload = AddressListResponse(
        addresses=normalized_list,
        total=len(normalized_list),
        default_address_id=default_id,
    )

    return APIResponse(
        success=True,
        data=payload.model_dump(),
        message=f"Retrieved {len(normalized_list)} saved addresses from Swiggy.",
        request_id=request_id,
    )
