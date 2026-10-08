from typing import Optional, List, Dict, Any
from app.mcp.client import mcp_client
from app.core.logging import logger
from app.schemas.payment import (
    PaymentMethodOption,
    PaymentOptionsResponse,
    PaymentStatusResponse,
)


class PaymentService:
    async def _resolve_address_id(self, address_id: Optional[str]) -> str:
        if address_id:
            return address_id

        res = await mcp_client.call_tool("get_addresses", {})
        structured = res.get("structuredContent", {})
        default_id = structured.get("resolution", {}).get("defaultAddressId")
        if default_id:
            return default_id

        addresses = structured.get("addresses", [])
        if addresses:
            return addresses[0].get("id")

        raise ValueError("No delivery address available. Please provide an address_id.")

    async def get_payment_options(self, address_id: Optional[str] = None) -> PaymentOptionsResponse:
        """Fetches live payment options (UPI apps, QR, COD) from Swiggy MCP."""
        resolved_address_id = await self._resolve_address_id(address_id)
        res = await mcp_client.call_tool("get_payment_options", {"addressId": resolved_address_id})
        structured = res.get("structuredContent", {})

        payment_amount = float(structured.get("paymentAmount") or 0.0)
        raw_all = structured.get("allMethods", [])
        all_methods: List[PaymentMethodOption] = []
        for m in raw_all:
            all_methods.append(
                PaymentMethodOption(
                    id=m.get("id", ""),
                    display_name=m.get("displayName", m.get("id", "")),
                    group_name=m.get("groupName", "Other"),
                    icon_url=m.get("iconUrl"),
                    enabled=bool(m.get("enabled", True)),
                )
            )

        mobile_methods_raw = structured.get("platforms", {}).get("mobile", {}).get("methods", [])
        mobile_upi: List[PaymentMethodOption] = []
        for m in mobile_methods_raw:
            mobile_upi.append(
                PaymentMethodOption(
                    id=m.get("id", ""),
                    display_name=m.get("displayName", m.get("id", "")),
                    group_name="UPI",
                    kind=m.get("kind", "intent"),
                    icon_url=m.get("iconUrl"),
                    enabled=True,
                )
            )

        desktop_methods = structured.get("platforms", {}).get("desktop", {}).get("methods", [])
        desktop_qr_available = any(m.get("kind") == "qr" or m.get("id") == "PayWithQR" for m in desktop_methods)

        cod_info = structured.get("cod") or {}
        cod_available = bool(cod_info.get("available", False))

        return PaymentOptionsResponse(
            payment_amount=payment_amount,
            all_methods=all_methods,
            mobile_upi_methods=mobile_upi,
            desktop_qr_available=desktop_qr_available,
            cod_available=cod_available,
            agentic_payment_eligible=bool(structured.get("agenticPaymentEligible", False)),
            address_id=resolved_address_id,
        )

    async def check_payment_status(
        self,
        paas_id: str,
        order_id: Optional[str] = None,
        address_id: Optional[str] = None,
        cart_id: Optional[str] = None,
    ) -> PaymentStatusResponse:
        """Polls / checks status of an in-flight payment transaction."""
        resolved_address_id = await self._resolve_address_id(address_id)
        args: Dict[str, Any] = {
            "paasId": paas_id,
            "addressId": resolved_address_id,
        }
        if order_id:
            args["orderId"] = order_id
        if cart_id:
            args["cartId"] = cart_id

        res = await mcp_client.call_tool("check_payment_status", args)
        structured = res.get("structuredContent", {})
        status = structured.get("status") or structured.get("paymentStatus") or "PENDING"
        is_terminal = status.upper() in ("SUCCESS", "PAID", "FAILED", "TIMEOUT", "REFUND-INITIATED")

        return PaymentStatusResponse(
            paas_id=paas_id,
            order_id=order_id,
            status=status.upper(),
            is_terminal=is_terminal,
            raw_response=structured,
        )


payment_service = PaymentService()
