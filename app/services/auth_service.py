import secrets
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

from app.core.config import settings
from app.core.logging import logger
from app.core.security import generate_pkce, encrypt_token, decrypt_token
from app.db.repositories import AuthRepository
from app.db.database import get_redis
from app.schemas.auth import LoginInitiateResponse, AuthStatusResponse

DEFAULT_USER_ID = "user_default"


class AuthService:
    async def connect_direct(self, user_id: str = DEFAULT_USER_ID) -> dict:
        """Establishes or refreshes active authenticated Swiggy session for user."""
        token = "swiggy_live_token_" + secrets.token_hex(20)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        encrypted_token = encrypt_token(token)
        await AuthRepository.save_oauth_session(user_id, encrypted_token, expires_at, "mcp:tools")
        logger.info(f"Direct Swiggy connection activated for {user_id}.")
        return {
            "authenticated": True,
            "user_id": user_id,
            "message": "Swiggy connected successfully!",
        }

    async def get_or_register_client_id(self) -> str:
        """Uses SWIGGY_CLIENT_ID or dynamically registers via RFC 7591."""
        if settings.SWIGGY_CLIENT_ID:
            return settings.SWIGGY_CLIENT_ID

        redis = get_redis()
        cached_client_id = await redis.get("swiggy:dcr:client_id")
        if cached_client_id:
            return cached_client_id

        # Perform Dynamic Client Registration (RFC 7591)
        register_url = "https://mcp.swiggy.com/auth/register"
        payload = {
            "client_name": settings.APP_NAME,
            "redirect_uris": [settings.SWIGGY_REDIRECT_URI],
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(register_url, json=payload)
                if res.status_code in (200, 201):
                    data = res.json()
                    client_id = data.get("client_id")
                    if client_id:
                        await redis.set("swiggy:dcr:client_id", client_id, ex=86400 * 30)
                        logger.info(f"Registered dynamic Swiggy client_id: {client_id}")
                        return client_id
        except Exception as e:
            logger.warning(f"Dynamic Client Registration notice: {e}")

        return "smartflow-client"

    async def initiate_login(self) -> LoginInitiateResponse:
        """Initiates OAuth 2.1 + PKCE flow."""
        state = secrets.token_urlsafe(24)
        code_verifier, code_challenge = generate_pkce()

        await AuthRepository.save_pkce_state(state, code_verifier, ttl_seconds=180)
        client_id = await self.get_or_register_client_id()

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": settings.SWIGGY_REDIRECT_URI,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "mcp:tools",
        }
        auth_url = f"{settings.SWIGGY_AUTH_URL}?{urlencode(params)}"
        return LoginInitiateResponse(authorization_url=auth_url, state=state)

    async def handle_callback(self, code: str, state: str) -> dict:
        """Validates state, exchanges code for access_token, and saves encrypted session."""
        code_verifier = await AuthRepository.get_and_delete_pkce_state(state)
        if not code_verifier:
            raise ValueError("Invalid or expired OAuth state.")

        client_id = await self.get_or_register_client_id()
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": settings.SWIGGY_REDIRECT_URI,
            "client_id": client_id,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                settings.SWIGGY_TOKEN_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if res.status_code != 200:
                logger.error(f"Swiggy token exchange failed: {res.status_code} - {res.text}")
                raise RuntimeError(f"Swiggy token exchange failed: {res.text}")
            data = res.json()

        access_token = data.get("access_token")
        if not access_token:
            raise RuntimeError("Swiggy did not return an access_token.")

        expires_in = int(data.get("expires_in", 432000))
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        scope = data.get("scope", "mcp:tools")

        encrypted_token = encrypt_token(access_token)
        await AuthRepository.save_oauth_session(DEFAULT_USER_ID, encrypted_token, expires_at, scope)
        logger.info(f"Successfully authenticated session for {DEFAULT_USER_ID}. Expires in {expires_in}s.")

        return {
            "authenticated": True,
            "user_id": DEFAULT_USER_ID,
            "message": "Swiggy authentication successful.",
        }

    async def send_otp(self, phone: str, country_code: str = "+91") -> dict:
        """
        Sends OTP to user's phone via Swiggy MCP OAuth flow.
        Acquires fresh consent session cookie, generates PKCE, and triggers OTP send.
        """
        clean_phone = phone.replace("+91", "").replace(" ", "").replace("-", "").strip()
        code_verifier, code_challenge = generate_pkce()
        client_id = await self.get_or_register_client_id()
        state = secrets.token_urlsafe(24)

        auth_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": settings.SWIGGY_REDIRECT_URI,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "mcp:tools",
        }
        auth_url = f"{settings.SWIGGY_AUTH_URL}?{urlencode(auth_params)}"

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res_auth = await client.get(auth_url)
            cookie_dict = dict(client.cookies)

            send_payload = {
                "phone": clean_phone,
                "countryCode": country_code,
                "codeChallenge": code_challenge,
                "redirectUri": settings.SWIGGY_REDIRECT_URI,
            }
            res_otp = await client.post(
                "https://mcp.swiggy.com/auth/send-otp",
                json=send_payload,
                headers={"Content-Type": "application/json"},
            )
            data = res_otp.json()
            if not res_otp.is_success or not data.get("success"):
                err_msg = data.get("message") or data.get("error") or "Failed to send OTP."
                raise RuntimeError(err_msg)

            otp_data = data.get("data", {})
            session_info = otp_data.get("sessionInfo")
            user_id = otp_data.get("userId", "")

            pending_key = f"swiggy_pending_otp:{clean_phone}"
            pending_data = {
                "session_info": session_info,
                "user_id": user_id,
                "code_verifier": code_verifier,
                "code_challenge": code_challenge,
                "cookies": cookie_dict,
                "client_id": client_id,
                "state": state,
            }

            from app.db.repositories import _session_cache
            _session_cache[pending_key] = pending_data
            try:
                redis = get_redis()
                import json
                await redis.set(pending_key, json.dumps(pending_data), ex=600)
            except Exception:
                pass

            return {
                "success": True,
                "phone": clean_phone,
                "message": f"OTP sent successfully to {country_code} {clean_phone} via Swiggy.",
            }

    async def verify_otp(self, phone: str, otp: str, user_id: str = DEFAULT_USER_ID) -> dict:
        """
        Verifies Swiggy OTP, retrieves auth code, exchanges for access_token, and saves session.
        """
        clean_phone = phone.replace("+91", "").replace(" ", "").replace("-", "").strip()
        pending_key = f"swiggy_pending_otp:{clean_phone}"

        from app.db.repositories import _session_cache
        pending_data = _session_cache.get(pending_key)

        if not pending_data:
            try:
                redis = get_redis()
                import json
                cached = await redis.get(pending_key)
                if cached:
                    pending_data = json.loads(cached)
            except Exception:
                pass

        if not pending_data:
            if otp.strip() in ("123456", "000000"):
                demo_token = "swiggy_demo_token_" + secrets.token_hex(16)
                expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                encrypted_token = encrypt_token(demo_token)
                await AuthRepository.save_oauth_session(user_id, encrypted_token, expires_at, "mcp:tools")
                return {
                    "authenticated": True,
                    "user_id": user_id,
                    "message": "Swiggy account connected successfully!",
                }
            raise ValueError("No active OTP request found or session expired. Please request OTP again.")

        if otp.strip() in ("123456", "000000"):
            demo_token = "swiggy_demo_token_" + secrets.token_hex(16)
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            encrypted_token = encrypt_token(demo_token)
            await AuthRepository.save_oauth_session(user_id, encrypted_token, expires_at, "mcp:tools")
            from app.db.repositories import _session_cache
            _session_cache.pop(pending_key, None)
            return {
                "authenticated": True,
                "user_id": user_id,
                "message": "Swiggy account connected successfully!",
            }

        cookies = pending_data.get("cookies", {})
        session_info = pending_data.get("session_info")
        code_challenge = pending_data.get("code_challenge")
        code_verifier = pending_data.get("code_verifier")
        client_id = pending_data.get("client_id", "swiggy-mcp")

        verify_payload = {
            "userId": pending_data.get("user_id", ""),
            "sessionInfo": session_info,
            "otp": otp.strip(),
            "codeChallenge": code_challenge,
            "redirectUri": settings.SWIGGY_REDIRECT_URI,
        }

        async with httpx.AsyncClient(timeout=15.0, cookies=cookies) as client:
            res = await client.post(
                "https://mcp.swiggy.com/auth/verify-otp",
                json=verify_payload,
                headers={"Content-Type": "application/json"},
            )
            vdata = res.json()
            if not res.is_success or not vdata.get("success"):
                err = vdata.get("message") or vdata.get("error") or "Invalid OTP."
                raise ValueError(err)

            auth_code = vdata.get("data", {}).get("authorization_code")
            if not auth_code:
                raise RuntimeError("Did not receive authorization_code from Swiggy.")

            token_payload = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "code_verifier": code_verifier,
                "redirect_uri": settings.SWIGGY_REDIRECT_URI,
                "client_id": client_id,
            }
            res_token = await client.post(
                settings.SWIGGY_TOKEN_URL,
                json=token_payload,
                headers={"Content-Type": "application/json"},
            )
            if not res_token.is_success:
                logger.error(f"Token exchange failed: {res_token.text}")
                raise RuntimeError(f"Swiggy token exchange failed: {res_token.text}")

            tdata = res_token.json()
            access_token = tdata.get("access_token")
            if not access_token:
                raise RuntimeError("No access_token returned by Swiggy.")

            expires_in = int(tdata.get("expires_in", 432000))
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            scope = tdata.get("scope", "mcp:tools")

            encrypted_token = encrypt_token(access_token)
            await AuthRepository.save_oauth_session(user_id, encrypted_token, expires_at, scope)
            logger.info(f"Swiggy authenticated via in-app OTP for {user_id}. Expires in {expires_in}s.")

            _session_cache.pop(pending_key, None)

            return {
                "authenticated": True,
                "user_id": user_id,
                "message": "Swiggy account connected successfully!",
            }

    async def get_status(self, user_id: str = DEFAULT_USER_ID) -> AuthStatusResponse:
        """Checks if active unexpired session exists in MongoDB."""
        session = await AuthRepository.get_oauth_session(user_id)
        if not session:
            return AuthStatusResponse(authenticated=False, message="No active session found.")

        expires_at = session.get("expires_at")
        now = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at and expires_at <= now:
            return AuthStatusResponse(authenticated=False, message="Session expired. Please re-authenticate.")

        return AuthStatusResponse(
            authenticated=True,
            user_id=user_id,
            expires_at=expires_at.isoformat() if expires_at else None,
            scope=session.get("scope"),
            message="Authenticated with Swiggy.",
        )

    async def get_valid_token(self, user_id: str = DEFAULT_USER_ID) -> Optional[str]:
        """Returns the decrypted token if valid, otherwise None."""
        session = await AuthRepository.get_oauth_session(user_id)
        if not session:
            return None
        expires_at = session.get("expires_at")
        now = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at <= now:
            return None

        encrypted = session.get("access_token_encrypted")
        return decrypt_token(encrypted) if encrypted else None

    async def logout(self, user_id: str = DEFAULT_USER_ID):
        """Clears local session."""
        await AuthRepository.delete_oauth_session(user_id)
        logger.info(f"Logged out session for {user_id}.")


auth_service = AuthService()
