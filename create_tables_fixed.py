#!/usr/bin/env python3
"""
Fixed script to create all database tables using SQLAlchemy with proper enum handling
"""
import asyncio
from app.core.database import create_database_engine, init_database
from app.core.config import get_settings_for_environment

async def create_tables():
    """Create all database tables."""
    print("Creating all database tables...")
    
    # Initialize settings
    settings = get_settings_for_environment()
    print(f"Database URL: {settings.SQLALCHEMY_DATABASE_URI}")
    
    # Create database engine
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=True)
    
    try:
        # Import all models to ensure they're registered
        print("Importing all models...")
        from app.models import Base
        from app.models import (
            audit, base, memorial, permission, photo, user, psalm_119, qr_memorial, 
            contact, location, notification
        )
        print(f"Base metadata tables: {list(Base.metadata.tables.keys())}")
        
        # Create all tables directly using Base metadata
        async with engine.begin() as conn:
            # First create all enum types manually to avoid conflicts
            from sqlalchemy import text
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE userrole AS ENUM ('admin', 'user', 'moderator');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE subscriptionstatus AS ENUM ('free', 'basic', 'premium', 'enterprise');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE contacttype AS ENUM ('email', 'whatsapp');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE notificationtype AS ENUM ('yahrzeit_reminder', 'memorial_update', 'system', 'welcome', 'verification_reminder');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE notificationstatus AS ENUM ('pending', 'scheduled', 'sent', 'failed', 'cancelled', 'retry');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE qrorderstatus AS ENUM ('draft', 'pending_payment', 'paid', 'manufacturing', 'shipped', 'delivered', 'cancelled');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE qrdesigntemplate AS ENUM ('classic', 'modern', 'traditional', 'elegant', 'simple');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Now create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ All tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Close the engine
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())