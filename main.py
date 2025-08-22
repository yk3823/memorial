#!/usr/bin/env python3
"""
Memorial Website - Simple Main Runner
Run this file directly when PostgreSQL and Redis are up.
"""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("🚀 Starting Memorial Website...")
    print("📊 Make sure PostgreSQL and Redis are running:")
    print("   docker-compose up -d")
    print("")
    print("📚 API Documentation will be available at:")
    print("   http://localhost:8000/docs")
    print("")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )