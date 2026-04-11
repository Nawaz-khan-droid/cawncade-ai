import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .api.routes import analysis, auth, admin # Your dynamic routes

app = FastAPI()

# --- 1. THE DYNAMIC PART (API) ---
# These routes do the heavy lifting: Searching, Analyzing, AI Reasoning
app.include_router(analysis.router, prefix="/api/v1/analysis")
app.include_router(auth.router, prefix="/api/v1/auth")

# --- 2. THE UI DELIVERY (Static Mount) ---
# This serves the React "Remote Control"
static_path = os.path.join(os.getcwd(), "static")

if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="assets")

# --- 3. THE "SPARK" (Dynamic Route Handler) ---
# This ensures that if a user refreshes the page, React takes over
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # If the request is for an API that doesn't exist, return error
    if full_path.startswith("api/"):
        return {"error": "API Route not found"}
    
    # Otherwise, serve the React App
    index_file = os.path.join(static_path, "index.html")
    return FileResponse(index_file)