"""
CAWNCADE AI — Main FastAPI Application.
Context Aware Watch News Confirmation Authenticity Detection Engine.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings
from .api.routes.analysis import router as analysis_router
from .api.routes.auth import router as auth_router
from .api.routes.admin import router as admin_router
from .db.session import init_db
from .utils.logger import log

settings = get_settings()

# --- App Initialization ---
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "CAWNCADE AI — Context-Aware News Verification Platform. "
        "ContextLens for text/news analysis, VisualLens for image/video verification. "
        "Provides probabilistic reliability scores, multi-source context, citations, and explainable outputs."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


# --- Startup Event ---
@app.on_event("startup")
async def startup():
    log.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    log.info(f"   Environment: {settings.ENVIRONMENT}")
    init_db()
    log.info("   Database initialized.")
    log.info("   All modules loaded. Ready.")


# --- Root Endpoint ---
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "endpoints": {
            "analyze": f"{settings.API_V1_PREFIX}/analysis/analyze",
            "health": f"{settings.API_V1_PREFIX}/analysis/health",
            "auth_login": f"{settings.API_V1_PREFIX}/auth/login",
            "auth_register": f"{settings.API_V1_PREFIX}/auth/register",
            "admin_sources": f"{settings.API_V1_PREFIX}/admin/sources",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}
