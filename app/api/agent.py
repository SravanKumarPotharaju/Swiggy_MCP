from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, HTTPException
from app.services.llm_agent import llm_agent
from app.services.voice_call_service import voice_call_service
from app.services.cart_service import cart_service
from app.services.restaurant_service import restaurant_service
from app.mcp.client import mcp_client
from app.schemas.common import APIResponse
from app.core.logging import logger

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="User message or voice transcript")
    user_phone: Optional[str] = Field("user_web", description="User identifier")


class CallUserRequest(BaseModel):
    phone_number: Optional[str] = Field(None, description="Phone number to call")
    message: Optional[str] = Field(None, description="Custom message to speak")


class SetAddressRequest(BaseModel):
    address: Dict[str, Any] = Field(default_factory=dict, description="Address object to set as active")


@router.post("/chat", response_model=APIResponse)
async def chat_with_agent(
    request: Request,
    body: ChatMessageRequest,
):
    """
    Web Chat endpoint: Sends user message or voice transcript to Gemini AI Concierge,
    executes Swiggy MCP tools, and returns the AI's response.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await llm_agent.process_user_message(
            user_phone=body.user_phone,
            text_message=body.message,
        )
        if isinstance(res, dict):
            reply_text = res.get("reply", "")
            order_data = res.get("order")
            updated_address = res.get("updated_address")
            ui_action = res.get("ui_action")
            cart_type = res.get("cart_type")
        else:
            reply_text = str(res)
            order_data = None
            updated_address = None
            ui_action = None
            cart_type = None

        return APIResponse(
            success=True,
            data={
                "reply": reply_text,
                "order": order_data,
                "updated_address": updated_address,
                "ui_action": ui_action,
                "cart_type": cart_type,
            },
            message="Agent response generated.",
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/address", response_model=APIResponse)
async def set_active_address(request: Request, body: SetAddressRequest):
    """
    Sets the active delivery address from the UI selector.
    """
    request_id = getattr(request.state, "request_id", None)
    from app.db.repositories import AddressRepository
    address_data = body.address
    await AddressRepository.set_active_address("user_default", address_data)
    return APIResponse(
        success=True,
        data=address_data,
        message="Active delivery address updated successfully.",
        request_id=request_id,
    )


@router.post("/call-user", response_model=APIResponse)
async def call_user_phone(
    request: Request,
    body: CallUserRequest,
):
    """
    Triggers an automated phone call to the customer via Twilio Voice.
    """
    request_id = getattr(request.state, "request_id", None)
    result = voice_call_service.make_automated_call(
        to_phone=body.phone_number,
        message=body.message,
    )

    # Also dispatch proactive WhatsApp alert to user's phone
    try:
        from app.services.whatsapp_service import whatsapp_service
        wa_text = (
            "🚨 *SmartFlow Gate Arrival Alert!*\n\n"
            "🛵 Your Swiggy delivery partner *Ravi Kumar* is *2 minutes* away from your building gate in Rajajinagar.\n\n"
            "Please come downstairs to collect your food! 🍛"
        )
        whatsapp_service.send_whatsapp_message(wa_text, to_phone=body.phone_number)
    except Exception as wa_err:
        logger.warning(f"Could not send WhatsApp arrival notification: {wa_err}")

    return APIResponse(
        success=result.get("success", False),
        data=result,
        message=result.get("message") or result.get("error", "Call request processed"),
        request_id=request_id,
    )


@router.get("/initial-state", response_model=APIResponse)
async def get_initial_state(request: Request):
    """
    Returns initial state for the Web UI:
    - Default address
    - Active cart items & pricing
    - Meghana Foods menu
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        # 1. Address
        addresses = []
        try:
            addr_res = await mcp_client.call_tool("get_addresses", {})
            addresses = addr_res.get("structuredContent", {}).get("addresses", [])
        except Exception:
            pass

        from app.db.repositories import AddressRepository
        saved_active = await AddressRepository.get_active_address("user_default")
        default_addr = saved_active if saved_active else (addresses[0] if addresses else {
            "id": "addr_home_1",
            "addressTag": "Home",
            "addressLine": "mewt, 4th main road, Rajajinagar, Bengaluru",
            "locality": "Rajajinagar",
            "city": "Bengaluru",
            "postalCode": "560010",
        })
        if not addresses:
            addresses = [default_addr]

        # 2. Cart (Swiggy Food)
        cart = await cart_service.get_cart()

        # 3. Cart (Swiggy Instamart)
        instamart_cart = None
        try:
            from app.services.instamart_service import instamart_service
            im_res = await instamart_service.get_cart(user_id="user_default")
            instamart_cart = im_res.model_dump()
        except Exception as im_err:
            logger.warning(f"Failed to fetch initial Instamart cart: {im_err}")

        # 4. Default restaurant menu (Meghana Foods 288893)
        menu = await restaurant_service.get_menu(restaurant_id="288893")

        return APIResponse(
            success=True,
            data={
                "default_address": default_addr,
                "all_addresses": addresses,
                "cart": cart.model_dump(),
                "instamart_cart": instamart_cart,
                "featured_restaurant": {
                    "id": menu.restaurant_id,
                    "name": menu.restaurant_name,
                    "categories": [c.model_dump() for c in menu.categories],
                },
            },
            message="Initial state loaded.",
            request_id=request_id,
        )
    except Exception as e:

        logger.error(f"Error loading initial state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
