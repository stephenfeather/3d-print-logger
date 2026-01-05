"""
3D Print Logger - FastAPI Application Entry Point

This module initializes the FastAPI application, registers routes,
configures middleware, and manages application lifecycle events.

Usage:
    uvicorn src.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import admin, analytics, jobs, printers
from src.config import get_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks for the application.
    """
    # Startup
    # Note: Database initialization happens via get_db dependency
    # Moonraker manager start moved to background task
    # to avoid blocking startup if printers are offline
    yield
    # Shutdown
    # Clean up Moonraker connections if manager is initialized
    try:
        from src.moonraker.manager import MoonrakerManager

        manager = MoonrakerManager.get_instance()
        await manager.stop()
    except Exception:
        pass  # Manager may not be initialized


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
