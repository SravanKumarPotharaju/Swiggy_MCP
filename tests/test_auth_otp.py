import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_auth_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/auth/status")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "authenticated" in data["data"]


@pytest.mark.asyncio
async def test_auth_send_otp_mocked():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.services.auth_service.auth_service.send_otp", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {
                "success": True,
                "phone": "9390787901",
                "message": "OTP sent successfully."
            }
            res = await client.post(
                "/api/v1/auth/send-otp",
                json={"phone": "9390787901", "country_code": "+91"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["data"]["phone"] == "9390787901"


@pytest.mark.asyncio
async def test_auth_verify_otp_mocked():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.services.auth_service.auth_service.verify_otp", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "authenticated": True,
                "user_id": "user_default",
                "message": "Swiggy account connected successfully!"
            }
            res = await client.post(
                "/api/v1/auth/verify-otp",
                json={"phone": "9390787901", "otp": "123456"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["data"]["authenticated"] is True
