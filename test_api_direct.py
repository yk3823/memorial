#!/usr/bin/env python3
"""
Test the memorial API endpoint directly using HTTP client.
"""

import asyncio
import json
import logging
import aiohttp
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target user credentials
EMAIL = "eduardkozhevnikov@basebuykey.com"
PASSWORD = "Keren@3823"
BASE_URL = "http://localhost:8000"


async def test_memorial_api():
    """Test the memorial API directly."""
    
    logger.info("Testing memorial API endpoint directly...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Login first
            logger.info("1. Logging in...")
            
            login_data = {
                "email": EMAIL,
                "password": PASSWORD,
                "remember_me": False
            }
            
            async with session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data) as resp:
                if resp.status != 200:
                    logger.error(f"Login failed with status {resp.status}")
                    text = await resp.text()
                    logger.error(f"Response: {text}")
                    return
                
                login_result = await resp.json()
                logger.info(f"Login successful: {login_result.get('success', False)}")
                
                access_token = login_result.get("access_token")
                if not access_token:
                    logger.error("No access token in login response")
                    return
                
                logger.info(f"Access token: {access_token[:20]}...")
            
            # 2. Call the memorial listing API
            logger.info("2. Calling memorial listing API...")
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with session.get(f"{BASE_URL}/api/v1/memorials/my", headers=headers) as resp:
                logger.info(f"Memorial API response status: {resp.status}")
                
                response_text = await resp.text()
                logger.info(f"Response text: {response_text}")
                
                if resp.status == 200:
                    try:
                        memorial_data = json.loads(response_text)
                        logger.info(f"Memorial data:")
                        logger.info(f"  Items count: {len(memorial_data.get('items', []))}")
                        logger.info(f"  Total: {memorial_data.get('total', 'N/A')}")
                        
                        items = memorial_data.get('items', [])
                        if items:
                            logger.info("  Memorial items:")
                            for i, item in enumerate(items):
                                logger.info(f"    Memorial {i+1}:")
                                logger.info(f"      ID: {item.get('id')}")
                                logger.info(f"      Hebrew name: {item.get('deceased_name_hebrew')}")
                                logger.info(f"      Parent name: {item.get('parent_name_hebrew')}")
                        else:
                            logger.warning("  No memorial items found!")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                else:
                    logger.error(f"Memorial API call failed with status {resp.status}")
        
        except Exception as e:
            logger.error(f"API test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_memorial_api())