import pytest
from unittest.mock import AsyncMock, patch
from app.services.instamart_service import InstamartService


@pytest.mark.asyncio
async def test_instamart_get_addresses_normalization():
    mock_mcp_response = {
        "structuredContent": {
            "addresses": [
                {
                    "id": "addr_123",
                    "addressLine": "Flat 101, Green Acres, Kondapur",
                    "phoneNumber": "9999988888",
                    "addressCategory": "Work",
                    "addressTag": "Work",
                }
            ],
            "total": 1,
            "resolution": {
                "defaultAddressId": "addr_123",
            },
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.get_addresses("test_user")

        assert res.total == 1
        assert len(res.addresses) == 1
        assert res.default_address_id == "addr_123"
        assert res.requires_address_selection is False
        assert res.addresses[0].id == "addr_123"
        assert res.addresses[0].label == "Work"
        assert res.addresses[0].display_text == "Flat 101, Green Acres, Kondapur"
        assert res.addresses[0].is_default is True


@pytest.mark.asyncio
async def test_instamart_get_addresses_empty():
    mock_mcp_response = {
        "structuredContent": {
            "addresses": [],
            "total": 0,
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.get_addresses("test_user")

        assert res.total == 0
        assert len(res.addresses) == 0
        assert res.requires_address_selection is True
        assert "No saved addresses found" in res.message
