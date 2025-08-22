"""
API package initialization for Memorial Website.
Configures main API router and includes all API versions.
"""

from fastapi import APIRouter

from app.api.v1 import api_router as v1_router
from app.core.config import get_settings

settings = get_settings()

# Create main API router
api_router = APIRouter()

# Include API v1 routes
api_router.include_router(
    v1_router,
    prefix=settings.API_V1_STR,
    tags=["API v1"]
)

# Main API health check
@api_router.get("/health", tags=["Health"])
async def api_health_check():
    """Main API health check endpoint."""
    return {
        "status": "healthy",
        "service": "Memorial Website API",
        "versions": ["v1"],
        "environment": settings.ENVIRONMENT
    }

# API root endpoint
@api_router.get("/", tags=["Root"])
async def api_root():
    """API root endpoint with available versions."""
    return {
        "name": "Memorial Website API",
        "description": "API for managing memorial websites and user accounts",
        "versions": {
            "v1": {
                "url": settings.API_V1_STR,
                "status": "active",
                "documentation": "/docs"
            }
        },
        "support": "admin@memorial-website.com"
    }