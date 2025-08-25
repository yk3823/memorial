#!/usr/bin/env python3
"""
Debug script to investigate the memorial listing issue.
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_database
from app.models.user import User
from app.models.memorial import Memorial
from app.services.memorial import MemorialService, get_memorial_service
from app.schemas.memorial_simple import MemorialResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target user credentials
TARGET_EMAIL = "eduardkozhevnikov@basebuykey.com"
TARGET_USER_ID = "4f4c1d3d-0d80-4264-b918-4e9cf9ddff1d"


async def debug_memorial_issue():
    """Debug the memorial listing issue for the specific user."""
    
    logger.info("Starting memorial debug investigation...")
    
    # Get database connection
    async for db in get_database():
        try:
            # 1. Check if user exists and verify details
            logger.info(f"1. Checking user existence for email: {TARGET_EMAIL}")
            
            user_query = select(User).where(User.email == TARGET_EMAIL)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found with email: {TARGET_EMAIL}")
                return
            
            logger.info(f"   ✓ User found: {user.id} ({user.email})")
            logger.info(f"   ✓ User active: {user.is_active}")
            logger.info(f"   ✓ User verified: {user.is_verified}")
            logger.info(f"   ✓ User role: {user.role}")
            
            # Check if user ID matches expected
            if str(user.id) != TARGET_USER_ID:
                logger.warning(f"   ! User ID mismatch: expected {TARGET_USER_ID}, got {user.id}")
            
            # 2. Check raw memorial count in database
            logger.info(f"2. Checking raw memorial count for user {user.id}")
            
            count_query = select(func.count(Memorial.id)).where(Memorial.owner_id == user.id)
            count_result = await db.execute(count_query)
            total_memorials = count_result.scalar() or 0
            
            logger.info(f"   ✓ Total memorials for user: {total_memorials}")
            
            # Count by deletion status
            active_count_query = select(func.count(Memorial.id)).where(
                Memorial.owner_id == user.id,
                Memorial.is_deleted == False
            )
            active_count_result = await db.execute(active_count_query)
            active_memorials = active_count_result.scalar() or 0
            
            deleted_count_query = select(func.count(Memorial.id)).where(
                Memorial.owner_id == user.id,
                Memorial.is_deleted == True
            )
            deleted_count_result = await db.execute(deleted_count_query)
            deleted_memorials = deleted_count_result.scalar() or 0
            
            logger.info(f"   ✓ Active memorials: {active_memorials}")
            logger.info(f"   ✓ Deleted memorials: {deleted_memorials}")
            
            # 3. Get detailed memorial information
            logger.info("3. Fetching detailed memorial information...")
            
            memorials_query = select(Memorial).where(Memorial.owner_id == user.id)
            memorials_result = await db.execute(memorials_query)
            memorials = memorials_result.scalars().all()
            
            for i, memorial in enumerate(memorials):
                logger.info(f"   Memorial {i+1}:")
                logger.info(f"     ID: {memorial.id}")
                logger.info(f"     Hebrew name: {memorial.deceased_name_hebrew}")
                logger.info(f"     English name: {memorial.deceased_name_english}")
                logger.info(f"     Parent name Hebrew: {memorial.parent_name_hebrew}")
                logger.info(f"     Is deleted: {memorial.is_deleted}")
                logger.info(f"     Is public: {memorial.is_public}")
                logger.info(f"     Is locked: {memorial.is_locked}")
                logger.info(f"     Created at: {memorial.created_at}")
                logger.info(f"     Updated at: {memorial.updated_at}")
                
                # Check for missing required fields
                missing_fields = []
                if not memorial.deceased_name_hebrew:
                    missing_fields.append("deceased_name_hebrew")
                if not memorial.parent_name_hebrew:
                    missing_fields.append("parent_name_hebrew")
                
                if missing_fields:
                    logger.warning(f"     ! Missing required fields: {', '.join(missing_fields)}")
                else:
                    logger.info(f"     ✓ All required fields present")
            
            # 4. Test memorial service directly
            logger.info("4. Testing memorial service...")
            
            memorial_service = get_memorial_service()
            
            try:
                result = await memorial_service.get_user_memorials(
                    db=db,
                    user_id=user.id,
                    skip=0,
                    limit=20,
                    include_photos=False
                )
                
                logger.info(f"   ✓ Memorial service returned {len(result.items)} memorials")
                logger.info(f"   ✓ Total count from service: {result.total}")
                
                if result.items:
                    logger.info("   Memorial service responses:")
                    for i, memorial_response in enumerate(result.items):
                        logger.info(f"     Memorial {i+1}: {memorial_response.id}")
                        logger.info(f"       Hebrew name: {memorial_response.deceased_name_hebrew}")
                        logger.info(f"       Parent name: {memorial_response.parent_name_hebrew}")
                
            except Exception as e:
                logger.error(f"   ✗ Memorial service failed: {e}")
                logger.exception("   Full error:")
            
            # 5. Test MemorialResponse schema conversion manually
            logger.info("5. Testing MemorialResponse conversion...")
            
            for i, memorial in enumerate(memorials):
                try:
                    memorial_data = {
                        'id': memorial.id,
                        'owner_id': memorial.owner_id,
                        'deceased_name_hebrew': memorial.deceased_name_hebrew,
                        'deceased_name_english': memorial.deceased_name_english,
                        'parent_name_hebrew': memorial.parent_name_hebrew,
                        'spouse_name': memorial.spouse_name,
                        'children_names': memorial.children_names,
                        'parents_names': memorial.parents_names,
                        'family_names': memorial.family_names,
                        'birth_date_gregorian': memorial.birth_date_gregorian,
                        'death_date_gregorian': memorial.death_date_gregorian,
                        'birth_date_hebrew': memorial.birth_date_hebrew,
                        'death_date_hebrew': memorial.death_date_hebrew,
                        'yahrzeit_date_hebrew': memorial.yahrzeit_date_hebrew,
                        'next_yahrzeit_gregorian': memorial.next_yahrzeit_gregorian,
                        'biography': memorial.biography,
                        'memorial_song_url': memorial.memorial_song_url,
                        'is_public': memorial.is_public,
                        'is_locked': memorial.is_locked,
                        'enable_comments': memorial.enable_comments,
                        'location': memorial.location,
                        'location_lat': memorial.location_lat,
                        'location_lng': memorial.location_lng,
                        'whatsapp_phones': memorial.whatsapp_phones,
                        'notification_emails': memorial.notification_emails,
                        'unique_slug': memorial.unique_slug,
                        'page_views': memorial.page_views,
                        'created_at': memorial.created_at,
                        'updated_at': memorial.updated_at,
                        # Computed fields
                        'display_name': memorial.display_name,
                        'age_at_death': memorial.age_at_death,
                        'public_url': memorial.public_url,
                        'years_since_death': memorial.years_since_death,
                        'photo_count': 0,
                        'contact_count': 0,
                        'primary_photo': None,
                        'yahrzeit_first_year_custom': memorial.yahrzeit_first_year_custom or 3,
                    }
                    
                    memorial_response = MemorialResponse(**memorial_data)
                    logger.info(f"   ✓ Memorial {i+1} converted successfully")
                    
                except Exception as e:
                    logger.error(f"   ✗ Memorial {i+1} conversion failed: {e}")
                    logger.exception("   Conversion error details:")
            
            # 6. Raw SQL check
            logger.info("6. Raw SQL check...")
            
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
            
            logger.info(f"   ✓ Raw SQL found {len(raw_memorials)} memorials")
            
            for i, row in enumerate(raw_memorials):
                logger.info(f"   Raw Memorial {i+1}:")
                logger.info(f"     ID: {row.id}")
                logger.info(f"     Hebrew name: {row.deceased_name_hebrew}")
                logger.info(f"     English name: {row.deceased_name_english}")
                logger.info(f"     Parent name: {row.parent_name_hebrew}")
                logger.info(f"     Is deleted: {row.is_deleted}")
                logger.info(f"     Is public: {row.is_public}")
                logger.info(f"     Created: {row.created_at}")
        
        except Exception as e:
            logger.error(f"Database investigation failed: {e}")
            logger.exception("Full error details:")
            
        # Break after first iteration since get_database is a generator
        break


if __name__ == "__main__":
    asyncio.run(debug_memorial_issue())