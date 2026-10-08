from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from app.services.auth_service import auth_service
from app.schemas.auth import (
    LoginInitiateResponse,
    AuthStatusResponse,
    CallbackResponse,
    SendOtpRequest,
    VerifyOtpRequest,
)
from app.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/login", response_model=APIResponse)
async def login(request: Request):
    """
    Step 1: Initiates Swiggy OAuth 2.1 + PKCE flow.
    Returns the Swiggy authorization URL to open in browser.
    """
    request_id = getattr(request.state, "request_id", None)
    res = await auth_service.initiate_login()
    return APIResponse(
        success=True,
        data=res.model_dump(),
        message="Please open authorization_url in browser to authenticate with Swiggy OTP.",
        request_id=request_id,
    )


@router.post("/send-otp", response_model=APIResponse)
async def send_otp(request: Request, body: SendOtpRequest):
    """
    Initiates seamless OTP dispatch directly to user's mobile number via Swiggy.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await auth_service.send_otp(body.phone, body.country_code)
        return APIResponse(
            success=True,
            data=res,
            message=res.get("message", "OTP sent successfully."),
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-otp", response_model=APIResponse)
async def verify_otp(request: Request, body: VerifyOtpRequest):
    """
    Verifies OTP and completes Swiggy OAuth token exchange directly in-app.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        res = await auth_service.verify_otp(body.phone, body.otp)
        return APIResponse(
            success=True,
            data=res,
            message="Swiggy authentication successful.",
            request_id=request_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback")
async def callback(request: Request, code: str = Query(...), state: str = Query(...)):
    """
    Step 2: Receives redirect from Swiggy with auth code and state.
    Exchanges for access token and securely stores session in MongoDB.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        data = await auth_service.handle_callback(code, state)
        # If user opened in a browser window, return friendly auto-closing confirmation
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Swiggy Connected - SmartFlow</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #0f172a; color: #fff; }
    .card { background: #1e293b; padding: 40px; border-radius: 16px; text-align: center; max-width: 420px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }
    h2 { color: #10b981; margin-top: 0; font-size: 24px; }
    p { color: #94a3b8; font-size: 15px; line-height: 1.5; }
    .btn { display: inline-block; margin-top: 20px; padding: 12px 24px; background: #fc8019; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; cursor: pointer; border: none; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 54px; margin-bottom: 16px;">🟢</div>
    <h2>Swiggy Connected!</h2>
    <p>Your Swiggy account has been securely authenticated with SmartFlow. You can now close this tab or return to SmartFlow.</p>
    <button class="btn" onclick="window.close(); window.location.href='/';">Return to SmartFlow</button>
  </div>
  <script>
    if (window.opener) {
      window.opener.postMessage({ type: 'SWIGGY_AUTH_SUCCESS' }, '*');
      setTimeout(() => window.close(), 1800);
    } else {
      setTimeout(() => { window.location.href = '/'; }, 2500);
    }
  </script>
</body>
</html>"""
            return HTMLResponse(content=html)

        return APIResponse(
            success=True,
            data=data,
            message="Swiggy authentication successful.",
            request_id=request_id,
        )
    except Exception as e:
        if "text/html" in request.headers.get("accept", ""):
            html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Auth Error</title>
<style>body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #0f172a; color: #fff; }}
.card {{ background: #1e293b; padding: 30px; border-radius: 12px; text-align: center; }}
</style></head>
<body>
<div class="card">
  <h2>⚠️ Authentication Failed</h2>
  <p style="color:#ef4444">{str(e)}</p>
  <a href="/" style="color:#fc8019; font-weight:bold;">Return to SmartFlow</a>
</div>
</body></html>"""
            return HTMLResponse(content=html, status_code=400)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", response_model=APIResponse)
async def status(request: Request):
    """
    Checks if active, unexpired Swiggy OAuth session exists.
    """
    request_id = getattr(request.state, "request_id", None)
    res = await auth_service.get_status()
    return APIResponse(
        success=True,
        data=res.model_dump(),
        message=res.message,
        request_id=request_id,
    )


@router.post("/connect", response_model=APIResponse)
async def direct_connect(request: Request):
    """
    Direct connect to Swiggy MCP account.
    Establishes active authenticated session and updates state.
    """
    request_id = getattr(request.state, "request_id", None)
    res = await auth_service.connect_direct()
    return APIResponse(
        success=True,
        data=res,
        message="Swiggy connected successfully!",
        request_id=request_id,
    )


@router.post("/logout", response_model=APIResponse)
async def logout(request: Request):
    """
    Logs out and deletes active Swiggy session from MongoDB.
    """
    request_id = getattr(request.state, "request_id", None)
    await auth_service.logout()
    return APIResponse(
        success=True,
        data={"authenticated": False},
        message="Logged out successfully.",
        request_id=request_id,
    )
