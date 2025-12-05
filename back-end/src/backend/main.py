from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from contextlib import asynccontextmanager
import os

from backend.db import init_db
from backend.settings import get_settings
from backend.api import auth, media, requests, notifications
from backend.services.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield

app = FastAPI(
    title="Emby Subscription Manager",
    lifespan=lifespan,
    openapi_url=f"{get_settings().API_V1_STR}/openapi.json",
    docs_url=f"{get_settings().API_V1_STR}/docs",
)

app.include_router(auth.router, prefix=f"{get_settings().API_V1_STR}/auth", tags=["auth"])
app.include_router(media.router, prefix=f"{get_settings().API_V1_STR}/media", tags=["media"])
app.include_router(requests.router, prefix=f"{get_settings().API_V1_STR}/requests", tags=["requests"])
app.include_router(notifications.router, prefix=f"{get_settings().API_V1_STR}/notifications", tags=["notifications"])

# Serve React/Vue Frontend in Production
# Assuming static files are located at /app/static in Docker
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
# If running from /app/src, dirname x 3 might go up to /app/static?
# __file__ = /app/src/backend/main.py
# dirname = /app/src/backend
# dirname = /app/src
# dirname = /app
# join "static" -> /app/static. Yes.

if os.path.exists(static_dir):
    # Mount assets folder specifically
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Catch-all route for SPA
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Check if requesting a specific file that exists in static (e.g. vite.svg, favicon.ico)
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Otherwise return index.html for SPA routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not found"}

@app.get("/api_health")
def read_root():
    return {"message": "Welcome to Emby Subscription Manager API"}

