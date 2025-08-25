#!/usr/bin/env python3
"""
Test the memorial service to identify the conversion issue.
"""

import asyncio
import logging
from uuid import UUID

from app.core.config import get_settings
from app.core.database import create_database_engine, create_session_factory
from app.services.memorial import get_memorial_service
from app.schemas.memorial_simple import MemorialResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target user 
TARGET_USER_ID = "4f4c1d3d-0d80-4264-b918-4e9cf9ddff1d"


async def test_memorial_service():
    """Test the memorial service conversion."""
    
    logger.info("Testing memorial service...")
    
    # Initialize database
    settings = get_settings()
    engine = create_database_engine(settings.DATABASE_URL)
    session_factory = create_session_factory(engine)
    
    async with session_factory() as db:
        try:
            user_id = UUID(TARGET_USER_ID)
            memorial_service = get_memorial_service()
            
            logger.info(f"Calling memorial service for user {user_id}")
            
            result = await memorial_service.get_user_memorials(
                db=db,
                user_id=user_id,
                skip=0,
                limit=20,
                include_photos=False
            )
            
            logger.info(f"Memorial service returned:")
            logger.info(f"  Items count: {len(result.items)}")
            logger.info(f"  Total: {result.total}")
            logger.info(f"  Skip: {result.skip}")
            logger.info(f"  Limit: {result.limit}")
            logger.info(f"  Has next: {result.has_next}")
            logger.info(f"  Has previous: {result.has_previous}")
            
            if result.items:
                logger.info("Memorial items:")
                for i, memorial in enumerate(result.items):
                    logger.info(f"  Memorial {i+1}:")
                    logger.info(f"    ID: {memorial.id}")
                    logger.info(f"    Hebrew name: {memorial.deceased_name_hebrew}")
                    logger.info(f"    Parent name: {memorial.parent_name_hebrew}")
                    logger.info(f"    Owner ID: {memorial.owner_id}")
            else:
                logger.warning("No memorial items returned!")
            
        except Exception as e:
            logger.error(f"Memorial service test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_memorial_service())