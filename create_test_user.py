#!/usr/bin/env python3
"""
Create a test user for authentication testing
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_database
from app.services.auth import get_auth_service
from app.models.user import User

async def create_test_user():
    """Create a test user for authentication testing."""
    
    from app.core.database import create_database_engine, create_session_factory
    from app.core.config import get_settings
    
    # Initialize database
    settings = get_settings()
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    session_factory = create_session_factory(engine)
    
    auth_service = get_auth_service()
    
    # Get database session
    async with session_factory() as db:
        try:
            # Check if test user already exists
            from sqlalchemy import select
            stmt = select(User).where(User.email == "test@memorial.com")
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("✅ Test user test@memorial.com already exists")
                print(f"   User ID: {existing_user.id}")
                print(f"   Is Active: {existing_user.is_active}")
                print(f"   Is Verified: {existing_user.is_verified}")
                return existing_user
            
            # Create test user
            print("Creating test user: test@memorial.com")
            user, verification_token = await auth_service.register_user(
                db=db,
                email="test@memorial.com",
                password="TestPassword123!",
                first_name="Test",
                last_name="User",
                hebrew_name="משתמש בדיקה"
            )
            
            # Mark user as verified for testing
            user.is_verified = True
            user.verification_token = None
            await db.commit()
            await db.refresh(user)
            
            print("✅ Test user created successfully!")
            print(f"   Email: {user.email}")
            print(f"   User ID: {user.id}")
            print(f"   Name: {user.first_name} {user.last_name}")
            print(f"   Hebrew Name: {user.hebrew_name}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Is Verified: {user.is_verified}")
            
            return user
            
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(create_test_user())