#!/usr/bin/env python3
"""
Comprehensive Hebrew Login Flow Test Script
==========================================

Tests the complete Hebrew login flow to verify the fix works properly:
1. Hebrew login form access and rendering
2. Login API call with provided credentials 
3. Cookie setting by server
4. Redirect functionality
5. Authentication state persistence
6. Hebrew navigation display

Usage:
    python test_hebrew_login_flow.py
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HebrewLoginFlowTester:
    """Comprehensive tester for Hebrew login flow"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.cookies = {}
        
        # Test credentials
        self.test_email = "kolesnikovilj@extraku.net"
        self.test_password = "J0seph123!"
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str, data: Optional[Dict] = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} | {test_name}: {details}")
        
        if data:
            logger.debug(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    async def test_hebrew_login_page_access(self) -> bool:
        """Test 1: Access Hebrew login page"""
        try:
            url = f"{self.base_url}/he/login"
            
            async with self.session.get(url) as response:
                content = await response.text()
                
                # Check response status
                if response.status != 200:
                    self.log_result(
                        "Hebrew Login Page Access",
                        False,
                        f"HTTP {response.status} - Expected 200",
                        {"status": response.status, "url": url}
                    )
                    return False
                
                # Check Hebrew content
                hebrew_indicators = [
                    "כניסה לחשבון",  # Login to account
                    "כתובת דוא\"ל",  # Email address
                    "סיסמה",  # Password
                    "זכור אותי",  # Remember me
                    "dir=\"rtl\"",  # RTL direction
                    "lang=\"he\""   # Hebrew language
                ]
                
                found_indicators = []
                for indicator in hebrew_indicators:
                    if indicator in content:
                        found_indicators.append(indicator)
                
                success = len(found_indicators) >= 5
                self.log_result(
                    "Hebrew Login Page Access",
                    success,
                    f"Found {len(found_indicators)}/6 Hebrew indicators",
                    {
                        "found_indicators": found_indicators,
                        "content_length": len(content),
                        "has_rtl": "dir=\"rtl\"" in content,
                        "has_hebrew_lang": "lang=\"he\"" in content
                    }
                )
                return success
                
        except Exception as e:
            self.log_result(
                "Hebrew Login Page Access",
                False,
                f"Exception: {str(e)}",
                {"exception": type(e).__name__}
            )
            return False
    
    async def test_login_api_call(self) -> Tuple[bool, Optional[Dict]]:
        """Test 2: Login API call with credentials"""
        try:
            url = f"{self.base_url}/api/v1/auth/login"
            
            login_data = {
                "email": self.test_email,
                "password": self.test_password,
                "remember_me": True
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with self.session.post(url, json=login_data, headers=headers) as response:
                response_data = await response.json()
                
                # Store cookies for next tests
                if hasattr(response, 'cookies') and response.cookies:
                    for cookie in response.cookies:
                        if hasattr(cookie, 'key') and hasattr(cookie, 'value'):
                            self.cookies[cookie.key] = cookie.value
                        elif hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                            self.cookies[cookie.name] = cookie.value
                
                success = (
                    response.status == 200 and
                    response_data.get("success") is True and
                    "access_token" in response_data and
                    "refresh_token" in response_data and
                    "user" in response_data
                )
                
                details = f"Status: {response.status}, Success: {response_data.get('success')}"
                if not success:
                    details += f", Message: {response_data.get('message', 'No message')}"
                
                self.log_result(
                    "Login API Call",
                    success,
                    details,
                    {
                        "status": response.status,
                        "response_data": response_data,
                        "cookies_received": len(self.cookies),
                        "cookie_names": list(self.cookies.keys())
                    }
                )
                
                return success, response_data if success else None
                
        except Exception as e:
            self.log_result(
                "Login API Call",
                False,
                f"Exception: {str(e)}",
                {"exception": type(e).__name__}
            )
            return False, None
    
    async def test_cookie_setting(self) -> bool:
        """Test 3: Verify HTTP cookies are set correctly"""
        try:
            # Check if access_token cookie was set
            has_access_token = "access_token" in self.cookies
            
            if not has_access_token:
                self.log_result(
                    "Cookie Setting",
                    False,
                    "No access_token cookie found",
                    {"available_cookies": list(self.cookies.keys())}
                )
                return False
            
            # Verify cookie properties by making a request to see response headers
            url = f"{self.base_url}/he/login"  # Safe endpoint to check cookies
            async with self.session.get(url) as response:
                set_cookie_headers = response.headers.getall('Set-Cookie', [])
                
                # Look for access_token in Set-Cookie headers from previous login
                cookie_properties = {}
                for cookie_header in set_cookie_headers:
                    if 'access_token=' in cookie_header:
                        cookie_properties['found_in_headers'] = True
                        if 'HttpOnly' not in cookie_header.lower():
                            cookie_properties['allows_js_access'] = True
                        if 'SameSite=Lax' in cookie_header:
                            cookie_properties['samesite_lax'] = True
                
                self.log_result(
                    "Cookie Setting",
                    True,
                    f"Access token cookie set successfully",
                    {
                        "access_token_length": len(self.cookies.get("access_token", "")),
                        "total_cookies": len(self.cookies),
                        "cookie_properties": cookie_properties
                    }
                )
                return True
                
        except Exception as e:
            self.log_result(
                "Cookie Setting",
                False,
                f"Exception: {str(e)}",
                {"exception": type(e).__name__}
            )
            return False
    
    async def test_protected_route_access(self) -> bool:
        """Test 4: Access protected Hebrew route with cookies"""
        try:
            url = f"{self.base_url}/he/memorials"
            
            # Include cookies in request
            cookie_header = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers = {
                "Cookie": cookie_header
            } if cookie_header else {}
            
            async with self.session.get(url, headers=headers) as response:
                content = await response.text()
                
                # Check if we got the memorials page (not redirected to login)
                success = (
                    response.status == 200 and
                    "התחבר" not in content and  # "Login" shouldn't appear if logged in
                    ("ההנצחות שלי" in content or "memorials" in content.lower())
                )
                
                # Also check if redirected to login
                redirected_to_login = "/he/login" in str(response.url) or "כניסה לחשבון" in content
                
                if redirected_to_login:
                    success = False
                
                details = f"Status: {response.status}"
                if redirected_to_login:
                    details += " - Redirected to login page"
                elif success:
                    details += " - Successfully accessed protected route"
                
                self.log_result(
                    "Protected Route Access",
                    success,
                    details,
                    {
                        "status": response.status,
                        "url": str(response.url),
                        "content_length": len(content),
                        "has_login_form": "כניסה לחשבון" in content,
                        "has_memorials": "ההנצחות שלי" in content
                    }
                )
                return success
                
        except Exception as e:
            self.log_result(
                "Protected Route Access",
                False,
                f"Exception: {str(e)}",
                {"exception": type(e).__name__}
            )
            return False
    
    async def test_hebrew_navigation_authenticated(self) -> bool:
        """Test 5: Verify Hebrew navigation shows user as authenticated"""
        try:
            url = f"{self.base_url}/he"
            
            # Include cookies in request
            cookie_header = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers = {
                "Cookie": cookie_header
            } if cookie_header else {}
            
            async with self.session.get(url, headers=headers) as response:
                content = await response.text()
                
                # Check for authenticated navigation elements
                authenticated_indicators = [
                    "ההנצחות שלי",  # My memorials
                    "פרופיל אישי",   # Personal profile
                    "התנתק",        # Logout
                    "dropdown-toggle"  # User dropdown menu
                ]
                
                # Check for login/register links (shouldn't be there if authenticated)
                unauthenticated_indicators = [
                    'href="/he/login"',
                    'href="/he/register"',
                    "התחבר",  # Login
                    "הרשם"   # Register
                ]
                
                found_auth = [ind for ind in authenticated_indicators if ind in content]
                found_unauth = [ind for ind in unauthenticated_indicators if ind in content]
                
                success = len(found_auth) >= 2 and len(found_unauth) == 0
                
                details = f"Auth indicators: {len(found_auth)}/4, Unauth indicators: {len(found_unauth)}"
                
                self.log_result(
                    "Hebrew Navigation Authentication",
                    success,
                    details,
                    {
                        "status": response.status,
                        "authenticated_elements": found_auth,
                        "unauthenticated_elements": found_unauth,
                        "has_user_dropdown": "dropdown-toggle" in content
                    }
                )
                return success
                
        except Exception as e:
            self.log_result(
                "Hebrew Navigation Authentication",
                False,
                f"Exception: {str(e)}",
                {"exception": type(e).__name__}
            )
            return False
    
    async def test_login_redirect_flow(self) -> bool:
        """Test 6: Test the complete login and redirect flow"""
        try:
            # Simulate the full flow: login form -> API call -> redirect
            login_url = f"{self.base_url}/he/login"
            api_url = f"{self.base_url}/api/v1/auth/login"
            
            # First, get the login form
            async with self.session.get(login_url) as response:
                if response.status != 200:
                    self.log_result(
                        "Login Redirect Flow",
                        False,
                        f"Could not access login form: HTTP {response.status}",
                        {"step": "form_access", "status": response.status}
                    )
                    return False
            
            # Perform login API call
            login_data = {
                "email": self.test_email,
                "password": self.test_password,
                "remember_me": True
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with self.session.post(api_url, json=login_data, headers=headers) as response:
                if response.status != 200:
                    response_data = await response.json()
                    self.log_result(
                        "Login Redirect Flow",
                        False,
                        f"Login API failed: HTTP {response.status}",
                        {
                            "step": "api_login",
                            "status": response.status,
                            "response": response_data
                        }
                    )
                    return False
                
                # Update cookies
                if hasattr(response, 'cookies') and response.cookies:
                    for cookie in response.cookies:
                        if hasattr(cookie, 'key') and hasattr(cookie, 'value'):
                            self.cookies[cookie.key] = cookie.value
                        elif hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                            self.cookies[cookie.name] = cookie.value
            
            # Now test redirect to memorials (simulating JavaScript redirect)
            memorials_url = f"{self.base_url}/he/memorials"
            cookie_header = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers = {"Cookie": cookie_header} if cookie_header else {}
            
            async with self.session.get(memorials_url, headers=headers) as response:
                content = await response.text()
                
                success = (
                    response.status == 200 and
                    "כניסה לחשבון" not in content  # Not on login page
                )
                
                self.log_result(
                    "Login Redirect Flow",
                    success,
                    f"Complete flow status: {response.status}",
                    {
                        "final_status": response.status,
                        "final_url": str(response.url),
                        "has_login_form": "כניסה לחשבון" in content,
                        "cookies_count": len(self.cookies)
                    }
                )
                return success
                
        except Exception as e:
            self.log_result(
                "Login Redirect Flow",
                False,
                f"Exception: {str(e)}",
                {"exception": type(e).__name__}
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("Starting Hebrew Login Flow Test Suite")
        logger.info("=" * 50)
        
        # Test 1: Hebrew login page access
        test1_success = await self.test_hebrew_login_page_access()
        
        # Test 2: Login API call
        test2_success, login_data = await self.test_login_api_call()
        
        # Test 3: Cookie setting (depends on test 2)
        test3_success = await self.test_cookie_setting() if test2_success else False
        
        # Test 4: Protected route access (depends on test 2 & 3)
        test4_success = await self.test_protected_route_access() if test2_success else False
        
        # Test 5: Hebrew navigation authentication (depends on test 2 & 3)
        test5_success = await self.test_hebrew_navigation_authenticated() if test2_success else False
        
        # Test 6: Complete redirect flow
        test6_success = await self.test_login_redirect_flow()
        
        # Calculate overall results
        tests_run = 6
        tests_passed = sum([test1_success, test2_success, test3_success, 
                           test4_success, test5_success, test6_success])
        
        overall_success = tests_passed == tests_run
        
        summary = {
            "overall_success": overall_success,
            "tests_passed": tests_passed,
            "tests_run": tests_run,
            "success_rate": f"{tests_passed}/{tests_run} ({tests_passed/tests_run*100:.1f}%)",
            "test_results": self.test_results,
            "login_data": login_data,
            "cookies": self.cookies
        }
        
        logger.info("=" * 50)
        logger.info(f"TEST SUITE COMPLETE: {tests_passed}/{tests_run} tests passed")
        
        if overall_success:
            logger.info("✅ ALL TESTS PASSED - Hebrew login flow is working correctly!")
        else:
            logger.error("❌ SOME TESTS FAILED - Hebrew login flow needs attention")
        
        return summary

async def main():
    """Main test runner"""
    try:
        async with HebrewLoginFlowTester() as tester:
            results = await tester.run_all_tests()
            
            # Write detailed results to file
            with open('hebrew_login_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\nDetailed test results saved to: hebrew_login_test_results.json")
            print(f"Overall Result: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
            print(f"Success Rate: {results['success_rate']}")
            
            return 0 if results['overall_success'] else 1
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)