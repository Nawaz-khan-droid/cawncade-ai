"""
CAWNCADE AI — Main FastAPI Application.
Context Aware Watch News Confirmation Authenticity Detection Engine.

In production (Hugging Face Spaces / Docker):
  FastAPI serves BOTH the API and the built React frontend.
  API routes are under /api/v1/
  Everything else serves the React SPA from /app/static/
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config.settings import get_settings
from .api.routes.analysis import router as analysis_router
from .api.routes.auth import router as auth_router
from .api.routes.admin import router as admin_router
from .db.session import init_db
from .utils.logger import log

settings = get_settings()

# Path to built React frontend (set by Dockerfile)
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

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
# Use allow_all_origins in production (HF Spaces) since frontend and API are same-origin
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
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


# --- Mount static frontend (React build) ---
# This serves the built React app for all non-API routes
is_static_built = os.path.isdir(STATIC_DIR)


# --- API Endpoints ---
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": settings.APP_NAME}


# --- SPA Fallback ---
# For production: serve React frontend for all non-API routes
# Must be registered AFTER all API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve React SPA for all non-API routes.
    API routes (/api/v1/*) are handled by their routers above.
    This catch-all serves index.html so React Router works.
    """
    if not is_static_built:
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running",
                "docs": "/docs", "endpoints": {
                    "analyze": f"{settings.API_V1_PREFIX}/analysis/analyze",
                    "health": f"{settings.API_V1_PREFIX}/analysis/health",
                }}

    # Try to serve the exact file first (JS, CSS, images, favicon)
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # Otherwise serve index.html (React Router handles client-side routing)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    return {"error": "not found"}
