"""
Bulletproof Authentication System Test Suite
Tests all authentication scenarios to ensure no redirect loops occur.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import asyncpg
from datetime import datetime


class AuthenticationTester:
    """Comprehensive authentication testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[Dict] = []
        self.test_user = {
            "email": "test@memorial.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def run_all_tests(self) -> Dict:
        """Run the complete authentication test suite."""
        self.logger.info("Starting bulletproof authentication test suite...")
        
        start_time = time.time()
        
        # Test scenarios
        test_scenarios = [
            ("test_unauthenticated_access", "Test unauthenticated access to protected routes"),
            ("test_login_flow", "Test complete login flow with cookie management"),
            ("test_dashboard_access", "Test dashboard access after login"),
            ("test_redirect_loop_prevention", "Test prevention of redirect loops"),
            ("test_cookie_persistence", "Test cookie persistence across requests"),
            ("test_session_expiry", "Test session expiry handling"),
            ("test_invalid_token_handling", "Test invalid token cleanup"),
            ("test_concurrent_requests", "Test concurrent authentication requests"),
            ("test_error_scenarios", "Test error handling scenarios"),
            ("test_logout_flow", "Test logout and cleanup")
        ]
        
        for test_method, description in test_scenarios:
            self.logger.info(f"Running: {description}")
            try:
                result = await getattr(self, test_method)()
                result["description"] = description
                result["status"] = "passed" if result.get("success", False) else "failed"
            except Exception as e:
                result = {
                    "test": test_method,
                    "description": description,
                    "status": "error",
                    "error": str(e)
                }
                self.logger.error(f"Test {test_method} failed with error: {e}")
            
            self.test_results.append(result)
        
        # Generate summary report
        end_time = time.time()
        duration = end_time - start_time
        
        summary = {
            "test_suite": "Bulletproof Authentication Tests",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "total_tests": len(test_scenarios),
            "passed": sum(1 for r in self.test_results if r["status"] == "passed"),
            "failed": sum(1 for r in self.test_results if r["status"] == "failed"),
            "errors": sum(1 for r in self.test_results if r["status"] == "error"),
            "results": self.test_results
        }
        
        self.logger.info(f"Test suite completed in {duration:.2f}s")
        self.logger.info(f"Results: {summary['passed']} passed, {summary['failed']} failed, {summary['errors']} errors")
        
        return summary
    
    async def test_unauthenticated_access(self) -> Dict:
        """Test that unauthenticated users are properly redirected."""
        results = []
        
        protected_routes = [
            "/he/dashboard",
            "/he/memorials", 
            "/dashboard"
        ]
        
        async with aiohttp.ClientSession() as session:
            for route in protected_routes:
                async with session.get(f"{self.base_url}{route}", allow_redirects=False) as response:
                    results.append({
                        "route": route,
                        "status_code": response.status,
                        "location": response.headers.get("location"),
                        "redirected_to_login": "/login" in response.headers.get("location", "").lower()
                    })
        
        # All protected routes should redirect to login
        success = all(r["status_code"] == 302 and r["redirected_to_login"] for r in results)
        
        return {
            "test": "test_unauthenticated_access",
            "success": success,
            "results": results,
            "message": "All protected routes properly redirect unauthenticated users" if success else "Some routes failed to redirect"
        }
    
    async def test_login_flow(self) -> Dict:
        """Test the complete login flow with cookie management."""
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Access login page
            async with session.get(f"{self.base_url}/he/login") as response:
                login_page_ok = response.status == 200
            
            # Step 2: Submit login form
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"],
                "remember_me": True
            }
            
            async with session.post(f"{self.base_url}/he/login", data=login_data, allow_redirects=False) as response:
                login_redirect = response.status == 302
                redirected_to_dashboard = "/he/dashboard" in response.headers.get("location", "")
                has_cookies = "access_token" in response.cookies
            
            # Step 3: Follow redirect to dashboard
            if login_redirect and redirected_to_dashboard:
                async with session.get(f"{self.base_url}/he/dashboard") as response:
                    dashboard_accessible = response.status == 200
                    # Check if access_token cookie exists
                    cookies_sent = any(cookie.key == "access_token" for cookie in session.cookie_jar)
            else:
                dashboard_accessible = False
                cookies_sent = False
        
        success = all([login_page_ok, login_redirect, redirected_to_dashboard, has_cookies, dashboard_accessible, cookies_sent])
        
        return {
            "test": "test_login_flow",
            "success": success,
            "results": {
                "login_page_ok": login_page_ok,
                "login_redirect": login_redirect,
                "redirected_to_dashboard": redirected_to_dashboard,
                "has_cookies": has_cookies,
                "dashboard_accessible": dashboard_accessible,
                "cookies_sent": cookies_sent
            },
            "message": "Complete login flow successful" if success else "Login flow has issues"
        }
    
    async def test_dashboard_access(self) -> Dict:
        """Test dashboard access consistency after login."""
        results = []
        
        # Perform login and test dashboard access multiple times
        for attempt in range(5):
            async with aiohttp.ClientSession() as session:
                # Login
                login_data = {
                    "email": self.test_user["email"],
                    "password": self.test_user["password"]
                }
                
                async with session.post(f"{self.base_url}/he/login", data=login_data, allow_redirects=False) as response:
                    login_ok = response.status == 302
                
                # Access dashboard immediately after login
                if login_ok:
                    async with session.get(f"{self.base_url}/he/dashboard") as response:
                        dashboard_ok = response.status == 200
                        no_redirect_loop = "/he/login" not in str(response.url)
                else:
                    dashboard_ok = False
                    no_redirect_loop = False
                
                results.append({
                    "attempt": attempt + 1,
                    "login_ok": login_ok,
                    "dashboard_ok": dashboard_ok,
                    "no_redirect_loop": no_redirect_loop
                })
        
        success = all(r["login_ok"] and r["dashboard_ok"] and r["no_redirect_loop"] for r in results)
        
        return {
            "test": "test_dashboard_access",
            "success": success,
            "results": results,
            "message": "Dashboard consistently accessible after login" if success else "Dashboard access inconsistent"
        }
    
    async def test_redirect_loop_prevention(self) -> Dict:
        """Test that redirect loops are prevented."""
        
        # Test the exact scenario that was causing problems
        async with aiohttp.ClientSession() as session:
            # Login first
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            async with session.post(f"{self.base_url}/he/login", data=login_data, allow_redirects=True) as response:
                final_url = str(response.url)
                redirect_count = len(response.history)
                no_loops = redirect_count < 10 and "/he/dashboard" in final_url
        
        return {
            "test": "test_redirect_loop_prevention", 
            "success": no_loops,
            "results": {
                "final_url": final_url,
                "redirect_count": redirect_count,
                "ended_at_dashboard": "/he/dashboard" in final_url
            },
            "message": "No redirect loops detected" if no_loops else "Redirect loop detected"
        }
    
    async def test_cookie_persistence(self) -> Dict:
        """Test that cookies persist across requests."""
        
        async with aiohttp.ClientSession() as session:
            # Login to get cookies
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"],
                "remember_me": True
            }
            
            await session.post(f"{self.base_url}/he/login", data=login_data)
            cookies_after_login = {cookie.key: cookie.value for cookie in session.cookie_jar if not cookie.key.startswith('_')}
            
            # Make multiple requests to ensure cookies persist
            persistent_requests = []
            for i in range(3):
                async with session.get(f"{self.base_url}/he/dashboard") as response:
                    persistent_requests.append({
                        "request": i + 1,
                        "status": response.status,
                        "has_cookies": bool(session.cookie_jar)
                    })
                
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        success = all(r["status"] == 200 and r["has_cookies"] for r in persistent_requests)
        
        return {
            "test": "test_cookie_persistence",
            "success": success,
            "results": {
                "initial_cookies": list(cookies_after_login.keys()),
                "persistent_requests": persistent_requests
            },
            "message": "Cookies persist across requests" if success else "Cookie persistence issues"
        }
    
    async def test_session_expiry(self) -> Dict:
        """Test session expiry handling (mock test)."""
        # This would test with expired tokens in a real scenario
        # For now, we'll test invalid token handling
        
        cookie_jar = aiohttp.CookieJar()
        # Add an invalid/expired token
        cookie_jar.update_cookies({"access_token": "invalid.token.here"})
        
        async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
            async with session.get(f"{self.base_url}/he/dashboard", allow_redirects=False) as response:
                redirected_to_login = response.status == 302 and "/he/login" in response.headers.get("location", "")
        
        return {
            "test": "test_session_expiry",
            "success": redirected_to_login,
            "results": {
                "status_code": response.status,
                "location": response.headers.get("location"),
                "redirected_to_login": redirected_to_login
            },
            "message": "Invalid tokens properly handled" if redirected_to_login else "Invalid token handling failed"
        }
    
    async def test_invalid_token_handling(self) -> Dict:
        """Test that invalid tokens are properly cleaned up."""
        
        # Test with various invalid token scenarios
        test_scenarios = [
            ("malformed_token", "invalid.malformed.token"),
            ("empty_token", ""),
            ("short_token", "abc"),
            ("wrong_format", "not-a-jwt-token")
        ]
        
        results = []
        
        for scenario_name, token_value in test_scenarios:
            cookie_jar = aiohttp.CookieJar()
            if token_value:  # Only set cookie if token_value is not empty
                cookie_jar.update_cookies({"access_token": token_value})
            
            async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
                async with session.get(f"{self.base_url}/he/dashboard", allow_redirects=False) as response:
                    properly_handled = response.status == 302 and "/he/login" in response.headers.get("location", "")
                    
                    results.append({
                        "scenario": scenario_name,
                        "token": token_value[:20] + "..." if len(token_value) > 20 else token_value,
                        "properly_handled": properly_handled
                    })
        
        success = all(r["properly_handled"] for r in results)
        
        return {
            "test": "test_invalid_token_handling",
            "success": success,
            "results": results,
            "message": "Invalid tokens properly handled" if success else "Some invalid tokens not handled correctly"
        }
    
    async def test_concurrent_requests(self) -> Dict:
        """Test authentication under concurrent load."""
        
        async def make_auth_request(session_id: int):
            async with aiohttp.ClientSession() as session:
                # Login
                login_data = {
                    "email": self.test_user["email"],
                    "password": self.test_user["password"]
                }
                
                login_start = time.time()
                async with session.post(f"{self.base_url}/he/login", data=login_data, allow_redirects=False) as response:
                    login_time = time.time() - login_start
                    login_ok = response.status == 302
                
                # Access dashboard
                if login_ok:
                    dashboard_start = time.time()
                    async with session.get(f"{self.base_url}/he/dashboard") as response:
                        dashboard_time = time.time() - dashboard_start
                        dashboard_ok = response.status == 200
                else:
                    dashboard_time = 0
                    dashboard_ok = False
                
                return {
                    "session_id": session_id,
                    "login_ok": login_ok,
                    "dashboard_ok": dashboard_ok,
                    "login_time": round(login_time, 3),
                    "dashboard_time": round(dashboard_time, 3)
                }
        
        # Run 10 concurrent authentication flows
        concurrent_count = 10
        tasks = [make_auth_request(i) for i in range(concurrent_count)]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r["login_ok"] and r["dashboard_ok"])
        success = success_count == concurrent_count
        
        return {
            "test": "test_concurrent_requests",
            "success": success,
            "results": {
                "concurrent_requests": concurrent_count,
                "successful": success_count,
                "failed": concurrent_count - success_count,
                "average_login_time": round(sum(r["login_time"] for r in results) / len(results), 3),
                "average_dashboard_time": round(sum(r["dashboard_time"] for r in results) / len(results), 3),
                "details": results
            },
            "message": f"All {concurrent_count} concurrent requests successful" if success else f"Only {success_count}/{concurrent_count} requests successful"
        }
    
    async def test_error_scenarios(self) -> Dict:
        """Test various error scenarios."""
        
        error_scenarios = [
            ("invalid_credentials", {"email": "wrong@email.com", "password": "wrongpass"}),
            ("missing_password", {"email": self.test_user["email"], "password": ""}),
            ("missing_email", {"email": "", "password": self.test_user["password"]}),
            ("malformed_email", {"email": "not-an-email", "password": self.test_user["password"]})
        ]
        
        results = []
        
        for scenario_name, login_data in error_scenarios:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/he/login", data=login_data, allow_redirects=False) as response:
                    redirected_to_login = response.status == 302 and "/he/login" in response.headers.get("location", "")
                    
                    results.append({
                        "scenario": scenario_name,
                        "handled_properly": redirected_to_login,
                        "status_code": response.status,
                        "location": response.headers.get("location")
                    })
        
        success = all(r["handled_properly"] for r in results)
        
        return {
            "test": "test_error_scenarios",
            "success": success,
            "results": results,
            "message": "All error scenarios handled properly" if success else "Some error scenarios not handled correctly"
        }
    
    async def test_logout_flow(self) -> Dict:
        """Test logout and cleanup."""
        
        async with aiohttp.ClientSession() as session:
            # Login first
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            await session.post(f"{self.base_url}/he/login", data=login_data)
            cookies_after_login = bool(session.cookie_jar)
            
            # Access dashboard to confirm login
            async with session.get(f"{self.base_url}/he/dashboard") as response:
                dashboard_accessible_before = response.status == 200
            
            # Logout (simulate by clearing cookies manually since we don't have a logout endpoint in web_routes)
            session.cookie_jar.clear()
            
            # Try to access dashboard after logout
            async with session.get(f"{self.base_url}/he/dashboard", allow_redirects=False) as response:
                redirected_after_logout = response.status == 302 and "/he/login" in response.headers.get("location", "")
        
        success = cookies_after_login and dashboard_accessible_before and redirected_after_logout
        
        return {
            "test": "test_logout_flow",
            "success": success,
            "results": {
                "cookies_after_login": cookies_after_login,
                "dashboard_accessible_before": dashboard_accessible_before,
                "redirected_after_logout": redirected_after_logout
            },
            "message": "Logout flow working correctly" if success else "Logout flow has issues"
        }


async def main():
    """Run the authentication test suite."""
    tester = AuthenticationTester()
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{tester.base_url}/health") as response:
                if response.status != 200:
                    print("ERROR: Memorial website server is not running or not healthy")
                    print("Please start the server with: uvicorn app.main:app --reload")
                    return
    except Exception as e:
        print(f"ERROR: Cannot connect to server at {tester.base_url}")
        print("Please ensure the server is running: uvicorn app.main:app --reload")
        return
    
    # Run tests
    results = await tester.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bulletproof_auth_test_results_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("BULLETPROOF AUTHENTICATION TEST RESULTS")
    print("="*60)
    print(f"Duration: {results['duration_seconds']}s")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Errors: {results['errors']}")
    print(f"Success Rate: {results['passed']/results['total_tests']*100:.1f}%")
    print(f"\nDetailed results saved to: {filename}")
    
    if results['failed'] > 0 or results['errors'] > 0:
        print("\nFAILED TESTS:")
        for result in results['results']:
            if result['status'] != 'passed':
                print(f"  - {result['test']}: {result.get('message', result.get('error', 'Unknown error'))}")
    else:
        print("\n🎉 ALL TESTS PASSED! Bulletproof authentication is working correctly.")


if __name__ == "__main__":
    asyncio.run(main())