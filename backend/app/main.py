"""
CAWNCADE AI v3.0 — Main FastAPI Application.
Serves React SPA + API from one container on port 7860.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config.settings import get_settings
from .api.routes.analysis import router as analysis_router
from .api.routes.auth import router as auth_router
from .api.routes.admin import router as admin_router
from .db.session import init_db
from .utils.logger import log

settings = get_settings()

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "CAWNCADE AI v3.0 — Context-Aware News Verification Platform. "
        "ContextLens for text/news/YouTube, VisualLens for image verification. "
        "Powered by Llama 3.1 8B ReAct Agent + 5-Tier Search Engine."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
if settings.ENVIRONMENT == "production":
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                      allow_methods=["*"], allow_headers=["*"])
else:
    app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                      allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup():
    log.info(f"{'='*60}")
    log.info(f"  CAWNCADE AI v{settings.APP_VERSION} — Starting...")
    log.info(f"  Environment: {settings.ENVIRONMENT} | Log Level: {settings.LOG_LEVEL}")
    log.info(f"{'='*60}")

    # ── Google API Key — 5-in-1 Status ──
    gkey = bool(settings.GOOGLE_API_KEY)
    log.info(f"  [Google] API Key: {'CONFIGURED (5 services)' if gkey else 'NOT SET'}")
    if gkey:
        log.info(f"    ├─ Custom Search API: {'READY' if settings.GOOGLE_CSE_ID else 'NO CSE ID'}")
        log.info(f"    ├─ Fact Check Tools API: READY")
        log.info(f"    ├─ Safe Browsing API: READY")
        log.info(f"    ├─ YouTube Data API v3: READY")
        log.info(f"    └─ Cloud Storage JSON API: {'ENABLED' if settings.GCS_BACKUP_ENABLED else 'DISABLED (set GCS_BACKUP_ENABLED=true + GCS_BUCKET_NAME)'}")

    # ── Other API Keys ──
    log.info(f"  [Tavily] {'CONFIGURED' if settings.TAVILY_API_KEY else 'NOT SET'}")
    log.info(f"  [NewsData.io] {'CONFIGURED' if settings.NEWSDATA_API_KEY else 'NOT SET'}")
    log.info(f"  [NewsAPI.org] {'CONFIGURED' if settings.NEWS_API_KEY else 'NOT SET'}")
    log.info(f"  [HuggingFace] {'CONFIGURED' if settings.HUGGINGFACE_API_TOKEN else 'NOT SET'}")

    # ── Proxy ──
    proxy_status = "CONFIGURED" if settings.WEBSHARE_PROXY_URL else "NOT SET"
    if settings.WEBSHARE_PROXY_URL and settings.WEBSHARE_PROXY_USER:
        proxy_status += " (with Webshare credentials)"
    log.info(f"  [Webshare Proxy] {proxy_status}")

    # ── Models ──
    log.info(f"  [LLM] Synthesis fallback: {settings.LLM_MODEL}")
    log.info(f"  [Agent] Reasoning engine: {settings.AGENT_MODEL}")
    log.info(f"  [Vision] Model: {settings.VISION_MODEL}")

    # ── Database ──
    init_db()
    log.info(f"  [DB] SQLite at {settings.DATABASE_URL} — initialized")

    log.info(f"{'='*60}")
    log.info(f"  CAWNCADE AI v{settings.APP_VERSION} READY on port {settings.PORT}")
    log.info(f"{'='*60}")


@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}


is_static_built = os.path.isdir(STATIC_DIR)


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if not is_static_built:
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running",
                "endpoints": {
                    "analyze": f"{settings.API_V1_PREFIX}/analysis/analyze",
                    "analyze_image": f"{settings.API_V1_PREFIX}/analysis/analyze/image",
                    "health": f"{settings.API_V1_PREFIX}/analysis/health",
                }}
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"error": "not found"}
