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
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
)

# 1. CORS - Open wide for Production/HF
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Register API Routers FIRST
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)

# 3. Simple API Health (No Prefix)
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": settings.APP_NAME}

# 4. SPA Catch-all (LAST)
is_static_built = os.path.isdir(STATIC_DIR)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Prevent SPA from intercepting API calls that might have trailed off
    if full_path.startswith("api/"):
        return {"error": "API route not found", "path": full_path}
        
    if not is_static_built:
        return {"status": "Backend Running", "info": "Static files not found. Build frontend."}
    
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)