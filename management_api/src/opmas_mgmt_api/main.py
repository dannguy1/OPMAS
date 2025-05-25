"""Main application module."""

import logging
import time
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opmas_mgmt_api.api.v1.api import api_router
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.services.websocket import WebSocketManager
from opmas_mgmt_api.db.session import init_db

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Any:
    """Add processing time to response headers.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response with processing time header
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Initialize NATS connection
        nats_manager = NATSManager()
        await nats_manager.connect()
        logger.info("NATS connection established")

        # Initialize WebSocket manager
        websocket_manager = WebSocketManager()
        logger.info("WebSocket manager initialized")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    try:
        # Disconnect from NATS
        nats_manager = NATSManager()
        await nats_manager.disconnect()
        logger.info("NATS connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Check API health status.

    Returns:
        Health status response
    """
    nats_manager = NATSManager()
    return JSONResponse(
        {
            "status": "healthy",
            "version": "1.0.0",
            "dependencies": {
                "nats": nats_manager.is_connected,
            },
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)
