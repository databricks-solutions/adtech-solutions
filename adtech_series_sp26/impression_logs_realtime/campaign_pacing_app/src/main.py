import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.campaigns import router as campaigns_router
from .seed import init_db, seed_campaigns

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed demo data on startup."""
    init_db()
    seed_campaigns()
    logger.info("Startup complete — tables created and campaigns seeded.")
    yield


app = FastAPI(title="Campaign Pacing Dashboard", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(campaigns_router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Serve built React frontend (built by `npm run build` in frontend/)
# ---------------------------------------------------------------------------
_FRONTEND_DIST = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)
_ASSETS_DIR = os.path.join(_FRONTEND_DIST, "assets")

if os.path.isdir(_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="static-assets")


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def serve_spa(full_path: str):
    """Serve static files from dist if they exist (favicon, logos, etc.), else SPA fallback."""
    if full_path:
        candidate = os.path.normpath(os.path.join(_FRONTEND_DIST, full_path))
        if candidate.startswith(_FRONTEND_DIST) and os.path.isfile(candidate):
            return FileResponse(candidate)
    index = os.path.join(_FRONTEND_DIST, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse(
        {"status": "API running", "note": "frontend not built — run: cd frontend && npm run build"},
        status_code=200,
    )
