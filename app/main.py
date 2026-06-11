"""
IndustryEar — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import router as api_router
from app.services.telegram_service import start_polling, stop_polling

# ── Logging ──────────────────────────────────────────────────────
setup_logging()


# ── Lifespan (startup / shutdown) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start Telegram bot polling on startup, stop on shutdown."""
    start_polling()
    yield
    stop_polling()


# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────
# All API endpoints live under /api/v1
app.include_router(api_router, prefix="/api/v1")


# ── Root health probe ───────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": settings.APP_TITLE, "version": settings.APP_VERSION}

