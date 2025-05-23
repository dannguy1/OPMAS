"""Main FastAPI application."""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .api.v1 import router as api_v1_router
from .auth.routers import router as auth_router
from .config import get_settings
from .monitoring import metrics_middleware, metrics_endpoint
from .security import SecurityMiddleware, RateLimiter
from .core.exceptions import OPMASException
from .services.nats import nats_manager
from .db.session import db_manager
from .db.init_db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ManagementAPI")

# Create FastAPI app
app = FastAPI(
    title="OPMAS Management API",
    description="Management API for OpenWRT Proactive Monitoring Agentic System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add security middleware
rate_limiter = RateLimiter(requests_per_minute=60)
app.add_middleware(
    SecurityMiddleware,
    rate_limiter=rate_limiter,
    allowed_hosts=["*"],  # Configure based on your environment
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowed_headers=["*"]
)

# Add CORS middleware with more permissive settings for docs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
app.middleware("http")(metrics_middleware)

# Add metrics endpoint
app.get("/metrics")(metrics_endpoint)

# Error handlers
@app.exception_handler(OPMASException)
async def opmas_exception_handler(request: Request, exc: OPMASException):
    logger.error(f"OPMAS Exception: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Management API starting up...")
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Connect to NATS
        await nats_manager.connect()
        logger.info("NATS connection established")
        
    except Exception as e:
        logger.critical(f"CRITICAL STARTUP ERROR: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize application: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Management API shutting down...")
    await nats_manager.close()
    logger.info("NATS connection closed")

# Include routers
API_V1_PREFIX = "/api/v1"
app.include_router(api_v1_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=API_V1_PREFIX)

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the OPMAS Management API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "database": "connected" if db_manager.engine is not None else "disconnected",
            "nats": "connected" if nats_manager.nc is not None else "disconnected"
        }
    }