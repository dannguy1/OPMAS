"""Main FastAPI application."""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Callable

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from opmas_mgmt_api.api.v1.api import api_router
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.db.init_db import init_db
from sqlalchemy.orm import Session

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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.10.8:3000"],  # Explicitly allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


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
        init_db()
        logger.info("Application startup complete")

        # Initialize NATS connection
        nats_manager = NATSManager()
        await nats_manager.connect()
        logger.info("NATS connection established")

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to OPMAS Management API",
        "docs": "/docs",
        "redoc": "/redoc",
        "api": settings.API_V1_STR,
    }
