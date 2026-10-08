import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import logger
from app.db.database import connect_db, close_db
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.addresses import router as addresses_router
from app.api.restaurants import router as restaurants_router
from app.api.cart import router as cart_router
from app.api.payment import router as payments_router
from app.api.orders import router as orders_router
from app.api.whatsapp import router as whatsapp_router
from app.api.agent import router as agent_router
from app.api.instamart import router as instamart_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} ({settings.ENVIRONMENT})...")
    await connect_db()
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Your AI Food Delivery Concierge — Swiggy MCP Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({process_time:.4f}s)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(f"[{request_id}] Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "Internal Server Error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "details": {},
            },
            "request_id": request_id,
        },
    )


# Register Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(addresses_router, prefix=settings.API_V1_PREFIX)
app.include_router(restaurants_router, prefix=settings.API_V1_PREFIX)
app.include_router(cart_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(whatsapp_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(instamart_router, prefix=settings.API_V1_PREFIX)

# Mount static files for generated QR codes, CSS, JS
app.mount("/static", StaticFiles(directory="/Users/auto/Desktop/SmartFlow/static"), name="static")


@app.get("/", tags=["Root"])
async def root(request: Request):
    import os
    index_path = "/Users/auto/Desktop/SmartFlow/static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "success": True,
        "data": {
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "docs": "/docs",
        },
        "message": f"Welcome to {settings.APP_NAME}",
    }
