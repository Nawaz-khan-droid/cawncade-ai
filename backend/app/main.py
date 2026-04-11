import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import analysis, auth, admin # Ensure these imports match your structure

app = FastAPI(title="CAWNCADE AI v3.0")

# 1. Wide CORS for Hugging Face subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. DYNAMIC API ROUTES (Must come BEFORE static mounting)
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(analysis.router, prefix="/api/v1/analysis")
app.include_router(admin.router, prefix="/api/v1/admin")

@app.get("/api/health")
async def health():
    return {"status": "online", "engine": "Llama 3.1 8B"}

# 3. STATIC UI SERVING
# Find the static folder we copied in the Dockerfile
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

if os.path.exists(static_path):
    # Serve CSS/JS/Images
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="static")

    # Catch-all: If it's not an API call, serve the React App
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Safety: Don't let the SPA catch-all break API 404s
        if full_path.startswith("api/"):
            return {"error": "Endpoint not found"}
        return FileResponse(os.path.join(static_path, "index.html"))