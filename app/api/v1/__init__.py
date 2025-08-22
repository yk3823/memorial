"""
API v1 package initialization for Memorial Website.
Configures and combines all v1 API routes.
"""

from fastapi import APIRouter

from . import auth, memorial, hebrew, photos, dashboard, files, subscription

# Create main API v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(memorial.router, prefix="/memorials")
api_router.include_router(photos.router, prefix="/photos")
api_router.include_router(files.router, prefix="/files")
api_router.include_router(subscription.router, prefix="/subscription")
api_router.include_router(dashboard.router, prefix="/dashboard")
api_router.include_router(hebrew.router)  # Hebrew endpoints already have /hebrew prefix

# Health check endpoint for API v1
@api_router.get("/health", tags=["Health"])
async def health_check():
    """API v1 health check endpoint."""
    return {
        "status": "healthy",
        "version": "v1",
        "service": "Memorial Website API"
    }

# API info endpoint
@api_router.get("/info", tags=["Info"])
async def api_info():
    """API v1 information endpoint."""
    return {
        "name": "Memorial Website API",
        "version": "v1",
        "endpoints": {
            "auth": "Authentication and user management",
            "memorials": "Memorial management with Hebrew calendar integration",
            "hebrew": "Hebrew-specific API endpoints for names, verses, and RTL functionality",
            "photos": "Photo upload and management with 6 photo types support",
            "dashboard": "Dashboard statistics and analytics in Hebrew",
            "users": "User management (coming soon)"
        },
        "documentation": "/docs",
        "status": "active"
    }