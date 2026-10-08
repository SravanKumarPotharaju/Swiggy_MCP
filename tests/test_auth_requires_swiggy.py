"""A Swiggy session may only ever hold a token that Swiggy issued.

Guards two former bypasses: the demo OTPs (123456 / 000000) that minted a local token
without calling Swiggy, and POST /auth/connect, which minted and stored a fake token.

Only the outbound Swiggy HTTP call is replaced (at the httpx transport layer). The routes,
the auth service, the OAuth/PKCE state and the session store all run for real.
"""
import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db import database, repositories
from app.db.repositories import AuthRepository
from app.main import app
from app.services.auth_service import auth_service

PHONE = "9390787901"
REAL_OTP = "482913"
SWIGGY_ISSUED_TOKEN = "tok-issued-by-swiggy"
SWIGGY_AUTH_CODE = "auth-code-from-swiggy"

SEND_OTP_URL = "https://mcp.swiggy.com/auth/send-otp"
VERIFY_OTP_URL = "https://mcp.swiggy.com/auth/verify-otp"

OTP_REJECTED = {"status_code": 400, "json": {"success": False, "message": "Invalid OTP"}}
OTP_ACCEPTED = {
    "status_code": 200,
    "json": {"success": True, "data": {"authorization_code": SWIGGY_AUTH_CODE}},
}
TOKEN_ISSUED = {
    "status_code": 200,
    "json": {"access_token": SWIGGY_ISSUED_TOKEN, "expires_in": 3600, "scope": "mcp:tools"},
}


def otp_flow_replies(verify, token=None):
    """Swiggy's replies for send-otp, then verify-otp, then (optionally) the token exchange."""
    replies = {
        settings.SWIGGY_AUTH_URL: {"status_code": 200, "text": "<html>consent</html>"},
        SEND_OTP_URL: {
            "status_code": 200,
            "json": {"success": True, "data": {"sessionInfo": "sess-1", "userId": "swiggy-user-1"}},
        },
        VERIFY_OTP_URL: verify,
    }
    if token is not None:
        replies[settings.SWIGGY_TOKEN_URL] = token
    return replies


class SwiggyHttp:
    """Answers outbound httpx requests from `replies`, keyed by URL without its query string.

    Nothing leaves the process. Every request is recorded as (method, url, json body), and a
    request to a URL that has no reply raises, so an unexpected Swiggy call cannot go unnoticed.
    """

    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    async def handle(self, request):
        url = str(request.url).split("?", 1)[0]
        body = json.loads(request.content) if request.content else None
        self.calls.append((request.method, url, body))
        if url not in self.replies:
            raise AssertionError(f"unexpected outbound call: {request.method} {url}")
        return httpx.Response(**self.replies[url])


@contextmanager
def swiggy_http(replies):
    swiggy = SwiggyHttp(replies)
    with patch.object(
        httpx.AsyncHTTPTransport,
        "handle_async_request",
        new_callable=AsyncMock,
        side_effect=swiggy.handle,
    ):
        yield swiggy


def api_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def in_process_auth_state(monkeypatch):
    """Use only the in-process session tier: no Redis/Mongo, a fresh cache, a fixed client id."""
    monkeypatch.setattr(database, "redis_client", None)
    monkeypatch.setattr(database, "mongodb", None)
    monkeypatch.setattr(repositories, "_session_cache", {})
    monkeypatch.setattr(settings, "SWIGGY_CLIENT_ID", "test-client-id")


async def request_otp(client):
    res = await client.post("/api/v1/auth/send-otp", json={"phone": PHONE})
    assert res.status_code == 200, res.text


async def submit_otp(client, otp):
    return await client.post("/api/v1/auth/verify-otp", json={"phone": PHONE, "otp": otp})


async def assert_no_swiggy_session(client):
    status = (await client.get("/api/v1/auth/status")).json()["data"]
    assert status["authenticated"] is False
    assert await auth_service.get_valid_token() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("demo_otp", ["123456", "000000"])
async def test_demo_otp_without_a_pending_request_is_a_401_and_stores_no_session(demo_otp):
    with swiggy_http({}) as swiggy:
        async with api_client() as client:
            res = await submit_otp(client, demo_otp)
            assert res.status_code == 401
            assert res.json()["detail"]
            await assert_no_swiggy_session(client)
    assert swiggy.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("demo_otp", ["123456", "000000"])
async def test_demo_otp_is_checked_by_swiggy_and_its_rejection_is_a_401(demo_otp):
    with swiggy_http(otp_flow_replies(verify=OTP_REJECTED)) as swiggy:
        async with api_client() as client:
            await request_otp(client)
            res = await submit_otp(client, demo_otp)
            assert res.status_code == 401
            assert res.json()["detail"] == "Invalid OTP"
            await assert_no_swiggy_session(client)
    assert [(method, url) for method, url, _ in swiggy.calls] == [
        ("GET", settings.SWIGGY_AUTH_URL),
        ("POST", SEND_OTP_URL),
        ("POST", VERIFY_OTP_URL),
    ]
    assert swiggy.calls[-1][2]["otp"] == demo_otp


@pytest.mark.asyncio
async def test_real_otp_stores_exactly_the_token_swiggy_issued():
    with swiggy_http(otp_flow_replies(verify=OTP_ACCEPTED, token=TOKEN_ISSUED)) as swiggy:
        async with api_client() as client:
            await request_otp(client)
            res = await submit_otp(client, REAL_OTP)
            assert res.status_code == 200
            assert res.json()["data"]["authenticated"] is True
            status = (await client.get("/api/v1/auth/status")).json()["data"]
            assert status["authenticated"] is True
    assert await auth_service.get_valid_token() == SWIGGY_ISSUED_TOKEN
    assert [(method, url) for method, url, _ in swiggy.calls] == [
        ("GET", settings.SWIGGY_AUTH_URL),
        ("POST", SEND_OTP_URL),
        ("POST", VERIFY_OTP_URL),
        ("POST", settings.SWIGGY_TOKEN_URL),
    ]
    assert swiggy.calls[2][2]["otp"] == REAL_OTP
    assert swiggy.calls[3][2]["code"] == SWIGGY_AUTH_CODE


@pytest.mark.asyncio
async def test_connect_stores_no_token_and_does_not_claim_to_be_authenticated():
    with swiggy_http({}) as swiggy:
        async with api_client() as client:
            res = await client.post(
                "/api/v1/auth/connect", headers={"Content-Type": "application/json"}
            )
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            assert not body["data"].get("authenticated")
            await assert_no_swiggy_session(client)
    assert swiggy.calls == []


@pytest.mark.asyncio
async def test_connect_returns_the_login_payload_and_arms_the_oauth_callback():
    with swiggy_http({}):
        async with api_client() as client:
            login = (await client.get("/api/v1/auth/login")).json()
            connect = (await client.post("/api/v1/auth/connect")).json()
    data = connect["data"]
    assert data.keys() == login["data"].keys() == {"authorization_url", "state"}
    url = urlparse(data["authorization_url"])
    assert f"{url.scheme}://{url.netloc}{url.path}" == settings.SWIGGY_AUTH_URL
    query = parse_qs(url.query)
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["client_id"] == ["test-client-id"]
    assert query["redirect_uri"] == [settings.SWIGGY_REDIRECT_URI]
    assert query["state"] == [data["state"]]
    # /auth/callback can only complete if the PKCE verifier for this state was persisted.
    assert await AuthRepository.get_and_delete_pkce_state(data["state"]) is not None


@pytest.mark.asyncio
async def test_connect_leaves_an_existing_swiggy_session_untouched():
    with swiggy_http(otp_flow_replies(verify=OTP_ACCEPTED, token=TOKEN_ISSUED)):
        async with api_client() as client:
            await request_otp(client)
            assert (await submit_otp(client, REAL_OTP)).status_code == 200
            res = await client.post("/api/v1/auth/connect")
            assert res.status_code == 200
    assert await auth_service.get_valid_token() == SWIGGY_ISSUED_TOKEN
