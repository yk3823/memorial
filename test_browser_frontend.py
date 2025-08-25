#!/usr/bin/env python3
"""
Test the frontend by examining the browser behavior.
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target user credentials
EMAIL = "eduardkozhevnikov@basebuykey.com"
PASSWORD = "Keren@3823"
BASE_URL = "http://localhost:8000"


async def test_frontend_memorial_page():
    """Test the frontend memorial page behavior."""
    
    logger.info("Starting browser test...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)  # Visible for debugging
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen to console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        # Listen to network requests
        network_logs = []
        page.on("request", lambda req: network_logs.append(f"➤ {req.method} {req.url}"))
        page.on("response", lambda res: network_logs.append(f"◀ {res.status} {res.url}"))
        
        try:
            # 1. Go to login page
            logger.info("1. Navigating to login page...")
            await page.goto(f"{BASE_URL}/he/login")
            
            # 2. Login
            logger.info("2. Logging in...")
            await page.fill('input[name="email"]', EMAIL)
            await page.fill('input[name="password"]', PASSWORD)
            await page.click('button[type="submit"]')
            
            # Wait for redirect
            await page.wait_for_url(f"{BASE_URL}/he/dashboard*")
            logger.info("   Login successful!")
            
            # 3. Navigate to memorials page
            logger.info("3. Navigating to my memorials page...")
            await page.goto(f"{BASE_URL}/he/my-memorials")
            
            # 4. Wait for page to load
            await page.wait_for_timeout(3000)  # Wait 3 seconds for JS to execute
            
            # 5. Check what happened
            logger.info("4. Checking page content...")
            
            # Check if loading state is visible
            loading_visible = await page.is_visible('#loadingState')
            empty_visible = await page.is_visible('#emptyState')
            memorials_list = await page.locator('#memorialsList').inner_html()
            
            logger.info(f"   Loading state visible: {loading_visible}")
            logger.info(f"   Empty state visible: {empty_visible}")
            logger.info(f"   Memorials list HTML: {memorials_list[:200]}...")
            
            # 6. Check console logs for errors
            logger.info("5. Console logs:")
            for log in console_logs[-10:]:  # Last 10 logs
                logger.info(f"   {log}")
            
            # 7. Check network requests
            logger.info("6. Recent network requests:")
            for log in network_logs[-5:]:  # Last 5 requests
                logger.info(f"   {log}")
                
            # 8. Check if HebrewMemorialApp is defined
            hebrew_app_defined = await page.evaluate("typeof HebrewMemorialApp !== 'undefined'")
            logger.info(f"   HebrewMemorialApp defined: {hebrew_app_defined}")
            
            if hebrew_app_defined:
                # Try to manually call the API
                logger.info("7. Testing API call manually...")
                try:
                    result = await page.evaluate("""
                        async () => {
                            try {
                                console.log('Calling HebrewMemorialApp.apiCall...');
                                const response = await HebrewMemorialApp.apiCall('/memorials/my');
                                console.log('API response:', response);
                                return { success: true, data: response };
                            } catch (error) {
                                console.error('API call failed:', error);
                                return { success: false, error: error.message };
                            }
                        }
                    """)
                    
                    if result['success']:
                        logger.info(f"   Manual API call successful: {len(result['data'].get('items', []))} items")
                    else:
                        logger.error(f"   Manual API call failed: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"   Failed to execute manual API call: {e}")
            
            # 9. Take screenshot for debugging
            await page.screenshot(path="memorial_page_debug.png")
            logger.info("   Screenshot saved as memorial_page_debug.png")
            
        except Exception as e:
            logger.error(f"Browser test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_frontend_memorial_page())