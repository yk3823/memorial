#!/usr/bin/env python3
"""
Simple debug script to investigate the memorial listing issue.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select, func, text

from app.core.config import get_settings
from app.core.database import create_database_engine, create_session_factory
from app.models.user import User
from app.models.memorial import Memorial

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target user credentials
TARGET_EMAIL = "eduardkozhevnikov@basebuykey.com"
TARGET_USER_ID = "4f4c1d3d-0d80-4264-b918-4e9cf9ddff1d"


async def investigate_memorial_issue():
    """Investigate the memorial listing issue."""
    
    logger.info("Starting memorial investigation...")
    
    # Initialize database
    settings = get_settings()
    engine = create_database_engine(settings.DATABASE_URL)
    session_factory = create_session_factory(engine)
    
    async with session_factory() as db:
        try:
            # 1. Check if user exists
            logger.info(f"1. Checking user with email: {TARGET_EMAIL}")
            
            user_query = select(User).where(User.email == TARGET_EMAIL)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found with email: {TARGET_EMAIL}")
                
                # Check if the target user ID exists at all
                user_by_id_query = select(User).where(User.id == UUID(TARGET_USER_ID))
                user_by_id_result = await db.execute(user_by_id_query)
                user_by_id = user_by_id_result.scalar_one_or_none()
                
                if user_by_id:
                    logger.info(f"   Found user by ID: {user_by_id.id} ({user_by_id.email})")
                    user = user_by_id
                else:
                    logger.error(f"   No user found with ID: {TARGET_USER_ID}")
                    return
            else:
                logger.info(f"   ✓ User found by email: {user.id} ({user.email})")
            
            # Check user details
            logger.info(f"   Active: {user.is_active}")
            logger.info(f"   Verified: {user.is_verified}")
            logger.info(f"   Role: {user.role}")
            logger.info(f"   Subscription status: {user.subscription_status}")
            
            # 2. Check memorials for this user
            logger.info(f"2. Checking memorials for user {user.id}")
            
            # Count all memorials
            count_all_query = select(func.count(Memorial.id)).where(Memorial.owner_id == user.id)
            count_all_result = await db.execute(count_all_query)
            total_memorials = count_all_result.scalar() or 0
            
            # Count active memorials  
            count_active_query = select(func.count(Memorial.id)).where(
                Memorial.owner_id == user.id,
                Memorial.is_deleted == False
            )
            count_active_result = await db.execute(count_active_query)
            active_memorials = count_active_result.scalar() or 0
            
            logger.info(f"   Total memorials: {total_memorials}")
            logger.info(f"   Active memorials: {active_memorials}")
            logger.info(f"   Deleted memorials: {total_memorials - active_memorials}")
            
            # 3. Get detailed memorial info
            logger.info("3. Fetching memorial details...")
            
            memorials_query = select(Memorial).where(Memorial.owner_id == user.id)
            memorials_result = await db.execute(memorials_query)
            memorials = memorials_result.scalars().all()
            
            for i, memorial in enumerate(memorials):
                logger.info(f"   Memorial {i+1}:")
                logger.info(f"     ID: {memorial.id}")
                logger.info(f"     Hebrew name: '{memorial.deceased_name_hebrew}'")
                logger.info(f"     English name: '{memorial.deceased_name_english}'")
                logger.info(f"     Parent name: '{memorial.parent_name_hebrew}'")
                logger.info(f"     Is deleted: {memorial.is_deleted}")
                logger.info(f"     Is public: {memorial.is_public}")
                logger.info(f"     Created: {memorial.created_at}")
                
                # Check required fields
                issues = []
                if not memorial.deceased_name_hebrew:
                    issues.append("missing deceased_name_hebrew")
                if not memorial.parent_name_hebrew:
                    issues.append("missing parent_name_hebrew")
                
                if issues:
                    logger.warning(f"     ⚠️ Issues: {', '.join(issues)}")
                else:
                    logger.info(f"     ✅ All required fields present")
            
            # 4. Test raw SQL query
            logger.info("4. Raw SQL check...")
            
            raw_query = text("""
                SELECT 
                    id,
                    deceased_name_hebrew,
                    deceased_name_english,
                    parent_name_hebrew,
                    is_deleted,
                    is_public,
                    created_at
                FROM memorials 
                WHERE owner_id = :user_id
                ORDER BY created_at DESC
            """)
            
            raw_result = await db.execute(raw_query, {"user_id": user.id})
            raw_memorials = raw_result.fetchall()
            
            logger.info(f"   Raw SQL returned {len(raw_memorials)} memorials")
            
            for i, row in enumerate(raw_memorials):
                logger.info(f"   Raw memorial {i+1}:")
                logger.info(f"     ID: {row.id}")
                logger.info(f"     Hebrew name: '{row.deceased_name_hebrew}'")
                logger.info(f"     English name: '{row.deceased_name_english}'")
                logger.info(f"     Parent name: '{row.parent_name_hebrew}'")
                logger.info(f"     Deleted: {row.is_deleted}")
                logger.info(f"     Public: {row.is_public}")
                logger.info(f"     Created: {row.created_at}")
            
            logger.info("Investigation complete!")
            
        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
    # Close database
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(investigate_memorial_issue())