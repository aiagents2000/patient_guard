"""
PatientGuard Backend — FastAPI Application.

Entry point:
    cd backend
    python3 -m uvicorn main:app --reload --port 8000
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import get_settings
from backend.routers import alerts, llm, patients, predictions, stats

# Settings
settings = get_settings()

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("patientguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"PatientGuard API v{settings.app_version} avviata")
    logger.info(f"Modalità dati: {'Supabase' if settings.use_supabase else 'JSON Demo'}")
    logger.info(f"LLM disponibile: {settings.use_llm}")

    # Pre-carica il DataStore per evitare latenza alla prima richiesta
    from backend.models.database import get_datastore

    get_datastore()

    yield
    # Shutdown
    logger.info("PatientGuard API arrestata")


# App
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API backend per PatientGuard — piattaforma AI di analisi predittiva EHR per il SSN italiano.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} — {response.status_code} ({duration:.0f}ms)")
    return response


# Routers
app.include_router(patients.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(llm.router)
app.include_router(stats.router)


# Health check
@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "mode": "supabase" if settings.use_supabase else "json_demo",
        "llm_available": settings.use_llm,
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("backend/routers/favicon.ico")


# Standalone run
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
