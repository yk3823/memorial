#!/usr/bin/env python3
"""
Simple debug test to examine what's happening with the frontend API call.
"""

import asyncio
import json
import logging
import aiohttp
from aiohttp import ClientSession

# Setup logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target user credentials
EMAIL = "eduardkozhevnikov@basebuykey.com"
PASSWORD = "Keren@3823"
BASE_URL = "http://localhost:8000"


async def test_complete_flow():
    """Test the complete flow like the browser does."""
    
    logger.info("Testing complete flow...")
    
    async with ClientSession() as session:
        try:
            # 1. Login to get cookies
            logger.info("1. Logging in to get authentication...")
            
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
                
                # Get the access token and cookies
                access_token = login_result.get("access_token")
                logger.info(f"Access token: {access_token[:20] if access_token else 'None'}...")
                
                # Check cookies
                cookies = session.cookie_jar
                cookie_names = [cookie.key for cookie in cookies]
                logger.info(f"Cookies received: {cookie_names}")
            
            # 2. Call the memorial API with cookies (like browser does)
            logger.info("2. Calling memorial API with cookies...")
            
            async with session.get(f"{BASE_URL}/api/v1/memorials/my") as resp:
                logger.info(f"Memorial API status: {resp.status}")
                
                if resp.status == 200:
                    memorial_data = await resp.json()
                    logger.info(f"Memorial data received:")
                    logger.info(f"  Items count: {len(memorial_data.get('items', []))}")
                    logger.info(f"  Total: {memorial_data.get('total', 'N/A')}")
                    
                    if memorial_data.get('items'):
                        for i, item in enumerate(memorial_data['items']):
                            logger.info(f"  Memorial {i+1}:")
                            logger.info(f"    ID: {item.get('id')}")
                            logger.info(f"    Hebrew name: {item.get('deceased_name_hebrew')}")
                            logger.info(f"    Parent name: {item.get('parent_name_hebrew')}")
                    else:
                        logger.warning("  No memorial items in response!")
                        
                    # Log the exact JSON response
                    logger.info(f"Raw JSON response: {json.dumps(memorial_data, indent=2)}")
                else:
                    text = await resp.text()
                    logger.error(f"Memorial API failed: {resp.status} - {text}")
            
            # 3. Test the Hebrew memorial page to see if there are any server-side issues
            logger.info("3. Testing Hebrew memorial page load...")
            
            async with session.get(f"{BASE_URL}/he/my-memorials") as resp:
                if resp.status == 200:
                    logger.info("Hebrew memorial page loads successfully")
                else:
                    logger.error(f"Hebrew memorial page failed: {resp.status}")
                    text = await resp.text()
                    logger.error(f"Response: {text[:500]}...")
        
        except Exception as e:
            logger.error(f"Complete flow test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_complete_flow())