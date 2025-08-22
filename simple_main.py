#!/usr/bin/env python3
"""
Simple FastAPI startup for Memorial Website - Development Mode
This is a simplified version for easy development and testing.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Memorial Website API",
    description="Digital Memorial Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Memorial Website API is running"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Memorial Website API", "docs": "/docs"}

# Import and include API routes (with error handling)
try:
    from app.api.v1.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    logging.info("✅ Auth routes loaded successfully")
except ImportError as e:
    logging.warning(f"⚠️  Could not load auth routes: {e}")

try:
    from app.api.v1.memorial import router as memorial_router
    app.include_router(memorial_router, prefix="/api/v1/memorials", tags=["memorials"])
    logging.info("✅ Memorial routes loaded successfully")
except ImportError as e:
    logging.warning(f"⚠️  Could not load memorial routes: {e}")

# Simple startup event
@app.on_event("startup")
async def startup_event():
    """Simple startup event."""
    logging.info("🚀 Memorial Website API started successfully!")
    print("=" * 50)
    print("🚀 Memorial Website API is running!")
    print(f"📚 API Documentation: http://localhost:8000/docs")
    print(f"🔍 Alternative Docs: http://localhost:8000/redoc")
    print(f"❤️  Health Check: http://localhost:8000/health")
    print("=" * 50)

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Memorial Website API...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )