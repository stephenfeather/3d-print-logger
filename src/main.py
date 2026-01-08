"""
3D Print Logger - FastAPI Application Entry Point

This module initializes the FastAPI application, registers routes,
configures middleware, and manages application lifecycle events.

Usage:
    uvicorn src.main:app --reload
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import admin, analytics, jobs, printers
from src.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# Determine static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"
SERVE_STATIC = STATIC_DIR.exists() and os.getenv("SERVE_STATIC", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks for the application.
    """
    # Startup
    from src.database.engine import get_db
    from src.moonraker.manager import MoonrakerManager

    logger.info("Starting application")

    # Start Moonraker manager and connect to printers
    db = next(get_db())
    try:
        manager = MoonrakerManager.get_instance()
        await manager.start(db)
        logger.info("Moonraker manager initialized")
    except Exception as e:
        logger.error(f"Failed to start Moonraker manager: {e}")
        # Continue startup even if Moonraker fails (printers may be offline)
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down application")
    try:
        manager = MoonrakerManager.get_instance()
        await manager.stop()
        logger.info("Moonraker manager stopped")
    except Exception as e:
        logger.error(f"Error stopping Moonraker manager: {e}")


app = FastAPI(
    title="3D Print Logger",
    description="Self-hosted application for logging and analyzing 3D print jobs",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(printers.router, prefix="/api/printers", tags=["printers"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}


# Serve static frontend files in production
if SERVE_STATIC:
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", tags=["frontend"])
    async def serve_spa(full_path: str) -> FileResponse:
        """
        Serve the SPA frontend.

        For any path not matching /api/* or /health, serve index.html
        to allow client-side routing.
        """
        # Check if requesting a specific file that exists
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(STATIC_DIR / "index.html")


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
