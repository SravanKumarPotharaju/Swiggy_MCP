import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm_agent import LLMAgent
from app.schemas.cart import CartSummaryResponse, CartItemResponse, CartPricing
from app.schemas.instamart import InstamartCartResponse


@pytest.fixture
def mock_agent():
    agent = LLMAgent()
    agent.client = MagicMock()  # Mock client to ensure it is considered configured
    return agent


@pytest.mark.asyncio
async def test_voice_command_food_cart_navigation(mock_agent):
    commands = [
        "open food cart",
        "food cart",
        "go to food cart",
        "show food cart",
        "navigate to the food cart",
    ]
    for cmd in commands:
        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message=cmd)
        assert res.get("ui_action", {}).get("action") == "open_cart", f"Failed for cmd: {cmd}"
        assert res.get("ui_action", {}).get("cart_type") == "food", f"Failed for cmd: {cmd}"


@pytest.mark.asyncio
async def test_voice_command_instamart_cart_navigation(mock_agent):
    commands = [
        "open instamart cart",
        "instamart cart",
        "grocery cart",
        "open grocery cart",
        "go to instamart cart",
    ]
    for cmd in commands:
        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message=cmd)
        assert res.get("ui_action", {}).get("action") == "open_cart", f"Failed for cmd: {cmd}"
        assert res.get("ui_action", {}).get("cart_type") == "instamart", f"Failed for cmd: {cmd}"


@pytest.mark.asyncio
async def test_voice_command_generic_cart(mock_agent):
    commands = ["cart", "open cart", "my cart", "show cart"]
    for cmd in commands:
        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message=cmd)
        assert res.get("ui_action", {}).get("action") == "open_cart", f"Failed for cmd: {cmd}"
        assert res.get("ui_action", {}).get("cart_type") == "active", f"Failed for cmd: {cmd}"


@pytest.mark.asyncio
async def test_voice_command_close_cart(mock_agent):
    commands = ["close cart", "close the cart", "hide cart"]
    for cmd in commands:
        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message=cmd)
        assert res.get("ui_action", {}).get("action") == "close_cart", f"Failed for cmd: {cmd}"


@pytest.mark.asyncio
async def test_voice_command_checkout_when_cart_empty(mock_agent):
    """When cart is empty, checkout voice command must warn user and open cart drawer."""
    with patch("app.services.llm_agent.cart_service.get_cart_summary", new_callable=AsyncMock) as mock_food_cart, \
         patch("app.services.instamart_service.instamart_service.get_cart", new_callable=AsyncMock) as mock_im_cart:
        
        # Empty carts
        mock_food_cart.return_value = CartSummaryResponse(items=[], pricing=CartPricing(to_pay=0))
        mock_im_cart.return_value = InstamartCartResponse(items=[], total_amount="0")

        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message="proceed to pay")
        
        assert "cart is currently empty" in res["reply"].lower()
        ui_action = res.get("ui_action", {})
        assert ui_action.get("action") == "open_cart"
        assert ui_action.get("is_empty") is True


@pytest.mark.asyncio
async def test_voice_command_checkout_when_cart_has_items(mock_agent):
    """When cart has items, checkout voice command must trigger open_payment action."""
    with patch("app.services.llm_agent.cart_service.get_cart_summary", new_callable=AsyncMock) as mock_food_cart, \
         patch("app.services.instamart_service.instamart_service.get_cart", new_callable=AsyncMock) as mock_im_cart:
        
        # Food cart has 1 Biryani
        item = CartItemResponse(menu_item_id="1", name="Chicken Biryani", price=350, subtotal=350, quantity=1)
        mock_food_cart.return_value = CartSummaryResponse(items=[item], pricing=CartPricing(to_pay=350))
        mock_im_cart.return_value = InstamartCartResponse(items=[], total_amount="0")

        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message="checkout")
        
        assert "payment" in res["reply"].lower()
        ui_action = res.get("ui_action", {})
        assert ui_action.get("action") == "open_payment"
        assert ui_action.get("cart_type") == "food"


@pytest.mark.asyncio
async def test_voice_command_tab_switching(mock_agent):
    # Menu tab
    res_menu = await mock_agent.process_user_message(user_phone="+919876543210", text_message="open menu")
    assert res_menu.get("ui_action", {}).get("action") == "switch_tab"
    assert res_menu.get("ui_action", {}).get("tab") == "pane-menu"

    # Instamart tab
    res_im = await mock_agent.process_user_message(user_phone="+919876543210", text_message="browse groceries")
    assert res_im.get("ui_action", {}).get("action") == "switch_tab"
    assert res_im.get("ui_action", {}).get("tab") == "pane-instamart"


@pytest.mark.asyncio
async def test_voice_command_cash_on_delivery_disabled(mock_agent):
    """Verifies that requesting Cash on Delivery or COD warns the user and directs to UPI."""
    cod_commands = ["cash on delivery", "COD", "pay by cash", "cash payment"]
    for cmd in cod_commands:
        res = await mock_agent.process_user_message(user_phone="+919876543210", text_message=cmd)
        assert "disabled" in res["reply"].lower()
        assert "upi" in res["reply"].lower()
        assert res.get("ui_action", {}).get("action") == "open_payment"


@pytest.mark.asyncio
async def test_order_service_checkout_rejects_cash():
    """Verifies that backend OrderService rejects Cash on Delivery requests."""
    from app.services.order_service import OrderService
    from app.schemas.order import CheckoutRequest

    service = OrderService()
    with patch.object(service, "_resolve_address_id", new_callable=AsyncMock) as mock_addr:
        mock_addr.return_value = "addr_test_123"
        req = CheckoutRequest(payment_method="Cash", address_id="addr_test_123")
        with pytest.raises(ValueError, match="Cash on Delivery \\(COD\\) is disabled"):
            await service.checkout(req)
