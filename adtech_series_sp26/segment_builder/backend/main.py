"""FastAPI application for Audience Segmentation Databricks App."""

from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports read env vars

import os
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config.constants import GENERIC_ERROR_MESSAGE
from backend.config.settings import get_settings
from backend.routers import agent, features, segments, settings
from backend.services.agent_service import get_agent_service
from backend.services.databricks_client import get_databricks_client

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- App Setup ---
app = FastAPI(
    title="Audience Segmentation App",
    description="Databricks App for building audience segments without SQL",
    version="1.0.0",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log unhandled exceptions and return generic 500; let HTTPException pass through."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.exception(
        "Unhandled exception: %s",
        exc,
        extra={"path": getattr(request, "url", None) and request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": GENERIC_ERROR_MESSAGE},
    )


# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routers ---
app.include_router(features.router)
app.include_router(segments.router)
app.include_router(agent.router)
app.include_router(settings.router)


# --- Health Check (resilient: never 500s so Apps and load balancers get 200) ---
@app.get("/api/health")
async def health_check():
    """Health check endpoint. Works in Databricks Apps and locally; never returns 500."""
    logger.info("Health check at /api/health")

    databricks_connected = False
    agent_mode = "unavailable"
    model_endpoint = ""

    try:
        app_settings = get_settings()
        model_endpoint = app_settings.databricks_model_endpoint or ""
    except Exception as e:
        logger.warning("Health: settings unavailable: %s", e)

    try:
        db = get_databricks_client()
        databricks_connected = db.is_configured
    except Exception as e:
        logger.warning("Health: Databricks client unavailable: %s", e)

    try:
        agent_svc = get_agent_service()
        agent_mode = agent_svc.agent_mode
    except Exception:
        pass

    return {
        "status": "healthy",
        "databricks_connected": databricks_connected,
        "agent_mode": agent_mode,
        "model_endpoint": model_endpoint,
    }


# --- Static Files Setup ---
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
assets_dir = os.path.join(static_dir, "assets")

# Create directories if they don't exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(assets_dir, exist_ok=True)

# Mount static files AFTER API routes
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


# --- Catch-all for React Routes ---
def _media_type(path: str) -> str:
    if path.endswith(".png"):
        return "image/png"
    if path.endswith(".jpg") or path.endswith(".jpeg"):
        return "image/jpeg"
    if path.endswith(".svg"):
        return "image/svg+xml"
    if path.endswith(".ico"):
        return "image/x-icon"
    return "application/octet-stream"


@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    """Serve static files from static_dir if they exist, else index.html for SPA routing."""
    if not isinstance(full_path, str):
        full_path = str(full_path) if full_path is not None else ""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    try:
        index_html = os.path.join(static_dir, "index.html")
    except Exception as e:
        logger.exception("Bad static_dir path: %s", e)
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)

    if not os.path.exists(index_html):
        logger.error("Frontend not built. index.html missing at %s", index_html)
        raise HTTPException(
            status_code=404,
            detail="Frontend not built. Please run 'bun run build' first.",
        )

    # Serve existing files from static root (e.g. logo from public/)
    if full_path and full_path != "/":
        try:
            safe_path = os.path.normpath(full_path).lstrip("/").replace("\\", "/")
            if ".." not in safe_path and safe_path:
                file_path = os.path.normpath(os.path.join(static_dir, *safe_path.split("/")))
                static_real = os.path.realpath(static_dir)
                if os.path.isfile(file_path):
                    file_real = os.path.realpath(file_path)
                    if file_real.startswith(static_real):
                        return FileResponse(file_path, media_type=_media_type(safe_path))
        except Exception as e:
            logger.debug("Static file check for %s: %s", full_path, e)

    logger.info("Serving React frontend for path: /%s", full_path or "/")
    return FileResponse(index_html, media_type="text/html")
