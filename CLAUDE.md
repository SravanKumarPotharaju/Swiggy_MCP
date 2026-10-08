# Project Conventions (managed by heimdall)

## Rules
- All code, configs, docs go in this project directory
- Planning state lives in `.planning/` (human-readable, git-committed)
- Each completed task = one atomic git commit
- Acceptance criteria must be runnable (grep, curl, test commands)

## Quality Gates (enforced before git push)
- All tests passing
- Lint clean (zero warnings)
- Code review completed
- No untested changes

## Code Quality — Zero Tolerance
- NEVER write stub, dummy, placeholder, shim, mock, TODO, or skeleton code
- Every line must be real, working, production-ready
- No `// TODO: implement`, no `pass`, no empty function bodies, no fake data
- If you cannot implement something fully, say so — do not fake it

## Style
- Follow existing patterns in the codebase
- Prefer small, focused files over large monoliths
- Name things clearly — a reader should understand without context

## Token Efficiency
- Caveman compression active: terse output, abbreviations, arrows for causality
- Level is owned by hmd directly (`heimdall-caveman get|set|rules`), not by the caveman plugin — do not hardcode a level here; read it live
- Drop articles, filler, hedging — code and paths stay exact

## Project Context

### Purpose
- SmartFlow: AI food/grocery concierge on Swiggy MCP (Food + Instamart). Chat/voice/WhatsApp agent (Gemini) searches, builds cart, checks out (UPI QR), tracks orders.
- Long-form spec: `SMARTFLOW_FEATURES_AND_ARCHITECTURE.md`. `README.md` structure tree is stale (omits instamart/agent/whatsapp/db/static).

### Stack
- Python, FastAPI + uvicorn, httpx, pydantic v2 + pydantic-settings, motor (MongoDB), redis.asyncio, cryptography (Fernet), google-genai (Gemini), twilio, qrcode/pillow, pytest + pytest-asyncio (`requirements.txt`; `mcp` pkg listed but client is hand-rolled httpx JSON-RPC).

### Run
- `pip install -r requirements.txt` → `cp .env.example .env` → `uvicorn app.main:app --reload` (entry `app/main.py`, obj `app`).
- Docs `/docs`, `/redoc`; UI at `/` (static/index.html); health `/health`.
- Mongo/Redis unreachable at startup → warn only, app still boots (memory cache fallback).

### Layout
- `app/main.py` — app, CORS, request-id/timing middleware, global 500 handler, router registration, `/static` mount, `/` serves index.html.
- `app/core/` — `config.py` (Settings, `.env`), `security.py` (PKCE, Fernet token enc; key = sha256(ENCRYPTION_KEY)), `logging.py`.
- `app/api/` — routers (below). `app/schemas/` — pydantic req/resp (`APIResponse` envelope in `common.py`). `app/models/schemas.py` — older models.
- `app/services/` — business logic: auth, food, cart, restaurant, order, payment, tracking, instamart (+`instamart_policy.py` checkout policy), `llm_agent.py` (Gemini), `whatsapp_service.py`, `voice_call_service.py`.
- `app/mcp/` — Swiggy MCP client. `app/db/` — `database.py` (connections), `repositories.py`.
- `app/workers/`, `app/websocket/` — see gotchas. `static/` — vanilla JS SPA. `tests/` — pytest.

### API (all under `/api/v1` except health)
- `/health`; `/auth` (login, send-otp, verify-otp, callback, status, connect, logout); `/addresses`; `/restaurants` (+`/{id}/menu`); `/cart` (+coupons, summary); `/payments`; `/orders` (checkout, confirm, list, frequent, `/{id}`, `/{id}/track`); `/whatsapp/webhook` (Twilio form POST); `/agent` (chat, address, call-user, initial-state); `/instamart` (addresses, products, go-to-items, cart, coupons, checkout, payments, orders, tracking).
- `app/api/tracking.py` exists but NOT registered in main.py.

### MCP client (`app/mcp/client.py`)
- `SwiggyMCPClient.call_tool(name, args, user_id)` → POST JSON-RPC `tools/call` to `SWIGGY_MCP_URL` (Food, default https://mcp.swiggy.com/food) or `INSTAMART_MCP_URL` (https://mcp.swiggy.com/im), `Bearer` token from `auth_service.get_valid_token`. Singletons `food_mcp_client`, `instamart_mcp_client`, alias `mcp_client`. Errors in `app/mcp/exceptions.py` (Connection/Authentication/Tool).
- Auth (`app/services/auth_service.py`), single hardcoded user `user_default`:
  - OAuth2.1+PKCE: `/auth/login` → Swiggy authorize URL (state→verifier in Redis, TTL 180s) → `/auth/callback` exchanges code at `SWIGGY_TOKEN_URL`.
  - In-app OTP: `/auth/send-otp` hits mcp.swiggy.com/auth/send-otp (endpoints hardcoded), pending state in memory+Redis (600s); `/auth/verify-otp` → auth code → token.
  - `SWIGGY_CLIENT_ID` default `swiggy-mcp`; falls back to RFC 7591 dynamic registration if unset.
  - `SWIGGY_REDIRECT_URI` used verbatim everywhere (default localhost callback).

### DB (`app/db/`)
- MongoDB via motor (db `MONGODB_DB_NAME`, falls back to 127.0.0.1) + Redis. Repos (static methods): `AuthRepository` (collection `oauth_sessions`; PKCE; read order memory→Redis→Mongo), `AddressRepository`, `CartRepository`, `OrderRepository`. Module-level `_session_cache`/`_address_cache` dicts.

### Integrations
- LLM: `llm_agent.py` Gemini chat per user key, function-calling tools (food + Instamart cart/checkout/address/navigate), model fallback list, needs `GEMINI_API_KEY`. Accepts text or audio bytes.
- WhatsApp: Twilio webhook → agent → TwiML reply (+QR image URL `/static/qr/order_<id>.png`); outbound via `whatsapp_service`.
- Voice: `voice_call_service.py` Twilio Voice outbound call (TwiML); browser TTS/voice in `static/js/voice.js`, `app.js`.
- Frontend: `static/index.html`, `static/css/style.css`, `static/js/{api,app,voice}.js`; API base `/api/v1`.

### Env var names (`app/core/config.py`; `.env.example` is partial)
- APP_NAME, ENVIRONMENT, DEBUG, API_V1_PREFIX, SECRET_KEY, ENCRYPTION_KEY, MONGODB_URL, MONGODB_DB_NAME, REDIS_URL, SWIGGY_MCP_URL, INSTAMART_MCP_URL, SWIGGY_AUTH_URL, SWIGGY_TOKEN_URL, SWIGGY_REDIRECT_URI, SWIGGY_CLIENT_ID, SWIGGY_CLIENT_SECRET, RENDER_EXTERNAL_URL, ARRIVAL_ALERT_THRESHOLD_MINUTES, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER, GEMINI_API_KEY.

### Deploy
- Render targeted (git history). No render.yaml/Dockerfile/Procfile in repo → config lives in Render dashboard. `.env` gitignored.

### Tests
- `tests/test_*.py` (auth OTP, cart/order persistence, frequent orders, instamart address/cart/products, voice chat commands). Run `pytest`. No pytest.ini/pyproject.

### Gotchas / risks
- CORS: `allow_origin_regex=".*"` + `allow_credentials=True` → any origin w/ credentials. Tighten before real auth.
- `SECRET_KEY`/`ENCRYPTION_KEY` have insecure in-code defaults; tokens decryptable if unset in prod.
- `auth_service.verify_otp`: OTP `123456`/`000000` mints a fake "demo" token (no Swiggy call) — auth bypass; `POST /auth/connect` also mints fake `swiggy_live_token_*` with no verification. Fake tokens then fail on real MCP calls (401).
- Single shared `user_default` session; no per-user auth on any endpoint.
- `repositories.py` has hardcoded `DEFAULT_ACTIVE_ADDRESS` (real-looking Bengaluru address).
- `RENDER_EXTERNAL_URL` defined but unused in code; redirect URI not derived dynamically in current tree despite commit message — verify before relying.
- `.env.example` uses `/oauth/authorize|token` URLs; config defaults use `/auth/authorize|token`. Mismatch.
- `app/workers/*` are idle sleep loops, never started from main.py; `app/websocket/` empty.
- `llm_agent.process_user_message` returns dict; `api/whatsapp.py` treats result as str (`"Order ID:" in reply_text`, TwiML) → likely broken WhatsApp path.
- `README.md` links an absolute path from another machine.
- Gemini sessions kept in in-process dict → lost on restart, not shared across workers.
