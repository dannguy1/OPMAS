"""Main FastAPI application."""

import logging
import time
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opmas_mgmt_api.api.v1.endpoints import (
    actions,
    agents,
    auth,
    dashboard,
    devices,
    findings,
    rules,
    websocket,
)
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.db.init_db import init_db
from opmas_mgmt_api.services.websocket import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OPMAS Management API",
    description="API for managing OPMAS devices, agents, and rules",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.10.8:3000"],  # Frontend URL
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
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application on startup."""
    try:
        await init_db()
        logger.info("Application startup complete")

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


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/v1", tags=["devices"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(rules.router, prefix="/api/v1", tags=["rules"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
app.include_router(findings.router, prefix="", tags=["findings"])
app.include_router(actions.router, prefix="", tags=["actions"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to OPMAS Management API"}
