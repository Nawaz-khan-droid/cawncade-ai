import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analysis, auth, admin
from app.config.settings import get_settings
from app.db.session import init_db
from app.core.cache import cache
from app.utils.logger import log
from app.services.news_service import close_shared_client

settings = get_settings()


# ── Periodic Cache Cleanup (PERF-03 FIX) ────────────────────────
async def _periodic_cache_cleanup():
    """Removes expired entries from the in-memory cache every hour."""
    while True:
        await asyncio.sleep(3600)
        cache.cleanup()
        log.debug("[Startup] Periodic cache cleanup executed.")


# ── REFACTOR-01 FIX: Use lifespan instead of deprecated @app.on_event ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    log.info("[Startup] Database initialized.")
    cleanup_task = asyncio.create_task(_periodic_cache_cleanup())
    log.info("[Startup] Periodic cache cleanup task started.")
    yield
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    await close_shared_client()  # REFACTOR-07: drain httpx connection pool
    log.info("[Shutdown] Background tasks stopped.")


app = FastAPI(title="CAWNCADE AI v3.0", lifespan=lifespan)

# ── SEC-07 FIX: Use settings.CORS_ORIGINS, not a hardcoded local-only list ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.hf\.space",  # Covers all HF Spaces subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes (must come BEFORE static mount) ─────────────────
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(analysis.router, prefix="/api/v1/analysis")
app.include_router(admin.router, prefix="/api/v1/admin")


@app.get("/api/health")
async def health():
    return {"status": "online", "engine": "Llama 3.1 8B"}


from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


from app.services.agent_service import cawncade_chat_agent


@app.post("/api/v1/chat")
async def handle_chat(req: ChatRequest):
    return await cawncade_chat_agent.chat(user_input=req.message, session_id=req.session_id)


# ── Static SPA Serving ───────────────────────────────────────────
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="static")

    # BUG-07 FIX: Return proper 404 JSON for unknown /api/ paths, not a 200 with error body
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"error": "Endpoint not found"}, status_code=404)
        index_file = os.path.join(static_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"error": "Frontend not built"}, status_code=503)