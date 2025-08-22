"""
Memorial Website - FastAPI Application
Production-ready FastAPI application with comprehensive security, monitoring, and architecture.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings_for_environment
from app.core.database import create_database_engine, get_database
from app.core.logging import setup_logging
from app.core.security import setup_security_headers

# Initialize settings
settings = get_settings_for_environment()

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Setup static files and templates paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Handles database connections, cleanup, and resource management.
    """
    logger.info("Starting Memorial Website application...")
    
    try:
        # Initialize database connection
        from app.core.database import create_session_factory
        engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        app.state.db_engine = engine
        
        # Create session factory
        session_factory = create_session_factory(engine)
        
        # Create storage directories if they don't exist
        storage_dirs = [
            Path(settings.UPLOAD_FOLDER),
            Path(settings.PHOTOS_FOLDER),
            Path(settings.VIDEOS_FOLDER),
            Path(settings.TEMP_FOLDER)
        ]
        for storage_dir in storage_dirs:
            storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Log successful startup
        logger.info(
            f"Application started successfully. "
            f"Environment: {settings.__class__.__name__}, "
            f"Debug mode: {settings.DEBUG}"
        )
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Memorial Website application...")
        
        # Close database connections
        if hasattr(app.state, 'db_engine'):
            await app.state.db_engine.dispose()
            logger.info("Database connections closed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance with all middleware and routes
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="A memorial website to honor and remember loved ones",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Setup security middleware
    setup_security_middleware(app)
    
    # Setup CORS
    setup_cors(app)
    
    # Setup session management
    setup_sessions(app)
    
    # Setup rate limiting
    setup_rate_limiting(app)
    
    # Setup static files and templates
    setup_static_and_templates(app)
    
    # Setup routes
    setup_routes(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_security_middleware(app: FastAPI) -> None:
    """Setup security-related middleware."""
    
    # Trusted host middleware - protect against Host header attacks
    if not settings.DEBUG:
        trusted_hosts = ["localhost", "127.0.0.1", "::1"]
        if settings.SERVER_HOST:
            # Extract hostname from SERVER_HOST URL
            from urllib.parse import urlparse
            parsed = urlparse(str(settings.SERVER_HOST))
            if parsed.hostname:
                trusted_hosts.append(parsed.hostname)
        
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=trusted_hosts
        )
    
    # Simple security headers only - no complex auth middleware
    
    # Security headers middleware
    app.middleware("http")(setup_security_headers)


def setup_cors(app: FastAPI) -> None:
    """Setup CORS middleware for cross-origin requests."""
    
    # Default CORS origins for development
    allowed_origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
        "http://127.0.0.1:8000",
    ]
    
    # Add configured origins
    if settings.BACKEND_CORS_ORIGINS:
        allowed_origins.extend([str(origin) for origin in settings.BACKEND_CORS_ORIGINS])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if settings.DEBUG else settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        expose_headers=["X-Total-Count", "X-Page-Count"]
    )


def setup_sessions(app: FastAPI) -> None:
    """Setup session management middleware."""
    
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        max_age=settings.SESSION_TIMEOUT_MINUTES * 60,  # Convert to seconds
        same_site="lax",
        https_only=not settings.DEBUG,
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """Setup rate limiting middleware."""
    
    if settings.RATE_LIMIT_ENABLED:
        app.state.limiter = limiter
        app.add_middleware(SlowAPIMiddleware)
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def setup_static_and_templates(app: FastAPI) -> None:
    """Setup static file serving and Jinja2 templates."""
    
    # Mount static files
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static"
    )
    
    # Mount storage files (photos and videos)
    upload_path = Path(settings.UPLOAD_FOLDER)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/storage",
        StaticFiles(directory=str(upload_path)),
        name="storage"
    )
    
    # Setup Jinja2 templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    
    # Add custom template functions and filters
    def url_for(name: str, **params: Any) -> str:
        """Template function to generate URLs."""
        # This will be enhanced when we add routing
        return f"/{name}"
    
    def format_hebrew_date(date_obj) -> str:
        """Template filter for Hebrew date formatting."""
        # Placeholder - will be implemented with Hebrew calendar service
        return str(date_obj) if date_obj else ""
    
    # Add custom functions to template environment
    templates.env.globals["url_for"] = url_for
    templates.env.filters["hebrew_date"] = format_hebrew_date
    templates.env.globals["settings"] = settings
    
    # Store templates in app state for use in route handlers
    app.state.templates = templates


def setup_routes(app: FastAPI) -> None:
    """Setup application routes and API endpoints."""
    
    # Import API router
    from app.api import api_router
    
    # Import web routes
    from app.web_routes import router as web_router
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Include web routes (HTML templates)
    app.include_router(web_router)
    
    @app.get("/health", name="health_check")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "environment": settings.__class__.__name__
        }

    
    # Rate limited example endpoint
    @app.get("/api/v1/limited")
    @limiter.limit("10/minute")
    async def limited_endpoint(request: Request):
        """Example rate-limited endpoint."""
        return {"message": "This endpoint is rate limited to 10 requests per minute"}


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers."""
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Custom 404 error handler."""
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                content={"error": "Not found", "status_code": 404},
                status_code=404
            )
        
        return app.state.templates.TemplateResponse(
            "errors/404.html",
            {
                "request": request,
                "title": "Page Not Found"
            },
            status_code=404
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        """Custom 500 error handler."""
        logger.error(f"Internal server error: {exc}")
        
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                content={"error": "Internal server error", "status_code": 500},
                status_code=500
            )
        
        return app.state.templates.TemplateResponse(
            "errors/500.html",
            {
                "request": request,
                "title": "Server Error"
            },
            status_code=500
        )


# Create the application instance
app = create_app()

# Development server startup
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )