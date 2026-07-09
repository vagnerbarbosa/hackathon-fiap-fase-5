"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health, threat_model
from src.core.config import settings
from src.core.logging import get_logger, setup_logging
from src.core.security import setup_security
from src.infrastructure.database import close_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    Setup on startup, cleanup on shutdown.
    """
    # Startup
    setup_logging()
    logger.info(
        "Starting up",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
        },
    )
    yield
    # Shutdown
    logger.info("Shutting down")
    await close_engine()


app = FastAPI(
    title=settings.app_name,
    description="API for automated STRIDE threat modeling from architecture diagrams",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Setup security middleware (must be before CORS)
setup_security(app)

# CORS middleware
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(health.router)
app.include_router(threat_model.router)


@app.get("/version")
async def get_version() -> dict:
    """Get API version information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
