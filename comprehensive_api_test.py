#!/usr/bin/env python3
"""
COMPREHENSIVE API ENDPOINT TEST SUITE FOR MEMORIAL WEBSITE
===========================================================

This script tests ALL API endpoints systematically:
1. System Health Checks
2. Authentication Endpoints (with both unverified and verified users)
3. Memorial CRUD Operations (with verified user)
4. Error Handling and Edge Cases

Test Results are categorized and analyzed for API health assessment.
"""
import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys


class ComprehensiveAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Test users
        self.unverified_user = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        self.verified_user = {
            "email": "verified_test@example.com",
            "password": "TestPassword123!"
        }
        
        # Test tracking
        self.results = {
            "system_endpoints": [],
            "auth_endpoints": [],
            "memorial_endpoints": [],
            "error_tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "start_time": datetime.now(),
                "end_time": None
            }
        }
        
        self.tokens = {
            "unverified_access": None,
            "unverified_refresh": None,
            "verified_access": None,
            "verified_refresh": None
        }
    
    def log_test(self, category: str, endpoint: str, method: str, status_code: int, 
                success: bool, details: str = "", response_time: float = 0):
        """Log a test result."""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        self.results[category].append(result)
        self.results["summary"]["total_tests"] += 1
        
        if success:
            self.results["summary"]["passed"] += 1
            print(f"✅ {method} {endpoint} ({result['response_time']}) - {details}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {method} {endpoint} ({result['response_time']}) - {details}")
    
    def make_request(self, method: str, endpoint: str, auth_token: str = None, **kwargs) -> Tuple[bool, requests.Response, str]:
        """Make HTTP request with optional authentication."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            # Add auth header if token provided
            if auth_token:
                if 'headers' not in kwargs:
                    kwargs['headers'] = {}
                kwargs['headers']['Authorization'] = f"Bearer {auth_token}"
            
            response = self.session.request(method, url, **kwargs)
            response_time = time.time() - start_time
            
            # Determine success based on expected behavior
            success = response.status_code < 400
            details = f"Status: {response.status_code}"
            
            # Add response details for failures
            if not success:
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        details += f" - {error_data['detail']}"
                    elif 'message' in error_data:
                        details += f" - {error_data['message']}"
                    else:
                        details += f" - {str(error_data)[:100]}"
                except:
                    details += f" - {response.text[:100]}"
            
            return success, response, details, response_time
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            details = f"Connection failed: {str(e)}"
            return False, None, details, response_time
    
    def test_system_endpoints(self):
        """Test system health and info endpoints."""
        print("\n" + "="*60)
        print("TESTING SYSTEM ENDPOINTS")
        print("="*60)
        
        endpoints = [
            ("GET", "/", "Main page"),
            ("GET", "/health", "Health check"),
            ("GET", "/api/", "API root"),
            ("GET", "/api/health", "API health check"),
            ("GET", "/api/v1/health", "API v1 health check"),
            ("GET", "/api/v1/info", "API v1 info")
        ]
        
        for method, endpoint, description in endpoints:
            success, response, details, response_time = self.make_request(method, endpoint)
            self.log_test("system_endpoints", endpoint, method, 
                         response.status_code if response else 0,
                         success, details, response_time)
    
    def test_auth_endpoints(self):
        """Test authentication endpoints with both user types."""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATION ENDPOINTS")
        print("="*60)
        
        # Test with unverified user
        print("\n--- Testing with Unverified User ---")
        self._test_auth_flow("unverified", self.unverified_user, register_first=True)
        
        # Test with verified user  
        print("\n--- Testing with Verified User ---")
        self._test_auth_flow("verified", self.verified_user, register_first=False)
    
    def _test_auth_flow(self, user_type: str, user_data: dict, register_first: bool):
        """Test complete authentication flow for a user type."""
        
        if register_first:
            # User registration
            register_data = {**user_data, "confirm_password": user_data["password"]}
            success, response, details, response_time = self.make_request(
                "POST", "/api/v1/auth/register", json=register_data)
            self.log_test("auth_endpoints", "/api/v1/auth/register", "POST",
                         response.status_code if response else 0,
                         success, details, response_time)
        
        # User login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": False
        }
        success, response, details, response_time = self.make_request(
            "POST", "/api/v1/auth/login", json=login_data)
        self.log_test("auth_endpoints", "/api/v1/auth/login", "POST",
                     response.status_code if response else 0,
                     success, f"{user_type.title()} login - {details}", response_time)
        
        # Store tokens
        if success and response:
            try:
                token_data = response.json()
                self.tokens[f"{user_type}_access"] = token_data.get("access_token")
                self.tokens[f"{user_type}_refresh"] = token_data.get("refresh_token")
            except:
                pass
        
        # Test authenticated endpoints if we have a token
        access_token = self.tokens[f"{user_type}_access"]
        if access_token:
            # Get current user info
            success, response, details, response_time = self.make_request(
                "GET", "/api/v1/auth/me", auth_token=access_token)
            self.log_test("auth_endpoints", "/api/v1/auth/me", "GET",
                         response.status_code if response else 0,
                         success, f"{user_type.title()} user info - {details}", response_time)
            
            # Update profile
            profile_data = {
                "first_name": f"Updated{user_type.title()}",
                "last_name": "TestUser"
            }
            success, response, details, response_time = self.make_request(
                "PUT", "/api/v1/auth/profile", json=profile_data, auth_token=access_token)
            self.log_test("auth_endpoints", "/api/v1/auth/profile", "PUT",
                         response.status_code if response else 0,
                         success, f"{user_type.title()} profile update - {details}", response_time)
            
            # Test token refresh
            refresh_token = self.tokens[f"{user_type}_refresh"]
            if refresh_token:
                refresh_data = {"refresh_token": refresh_token}
                success, response, details, response_time = self.make_request(
                    "POST", "/api/v1/auth/refresh", json=refresh_data)
                self.log_test("auth_endpoints", "/api/v1/auth/refresh", "POST",
                             response.status_code if response else 0,
                             success, f"{user_type.title()} token refresh - {details}", response_time)
        
        # Test password-related endpoints (these work without verification)
        forgot_data = {"email": user_data["email"]}
        success, response, details, response_time = self.make_request(
            "POST", "/api/v1/auth/forgot-password", json=forgot_data)
        self.log_test("auth_endpoints", "/api/v1/auth/forgot-password", "POST",
                     response.status_code if response else 0,
                     success, f"{user_type.title()} forgot password - {details}", response_time)
        
        # Logout (if we have a token)
        if access_token:
            success, response, details, response_time = self.make_request(
                "POST", "/api/v1/auth/logout", auth_token=access_token)
            self.log_test("auth_endpoints", "/api/v1/auth/logout", "POST",
                         response.status_code if response else 0,
                         success, f"{user_type.title()} logout - {details}", response_time)
    
    def test_memorial_endpoints(self):
        """Test memorial CRUD operations."""
        print("\n" + "="*60)
        print("TESTING MEMORIAL ENDPOINTS")
        print("="*60)
        
        # Get fresh verified user token
        login_data = {
            "email": self.verified_user["email"],
            "password": self.verified_user["password"],
            "remember_me": False
        }
        success, response, _, _ = self.make_request("POST", "/api/v1/auth/login", json=login_data)
        
        if not success or not response:
            print("❌ Could not authenticate verified user for memorial testing")
            return
        
        try:
            token_data = response.json()
            access_token = token_data.get("access_token")
        except:
            print("❌ Could not parse login response for memorial testing")
            return
        
        print("✅ Authenticated as verified user for memorial testing")
        
        # Memorial test data
        memorial_data = {
            "deceased_name_hebrew": "שלום עליכם",
            "deceased_name_english": "Shalom Aleichem",
            "birth_date_gregorian": "1950-01-01",
            "death_date_gregorian": "2020-01-01",
            "biography": "Test memorial biography for comprehensive API testing.",
            "is_public": True
        }
        
        # Create memorial
        success, response, details, response_time = self.make_request(
            "POST", "/api/v1/memorials", json=memorial_data, auth_token=access_token)
        self.log_test("memorial_endpoints", "/api/v1/memorials", "POST",
                     response.status_code if response else 0,
                     success, details, response_time)
        
        memorial_id = None
        memorial_slug = None
        if success and response:
            try:
                memorial_response = response.json()
                if "memorial" in memorial_response:
                    memorial_id = memorial_response["memorial"].get("id")
                    memorial_slug = memorial_response["memorial"].get("unique_slug")
            except:
                pass
        
        # List user memorials
        success, response, details, response_time = self.make_request(
            "GET", "/api/v1/memorials", auth_token=access_token)
        self.log_test("memorial_endpoints", "/api/v1/memorials", "GET",
                     response.status_code if response else 0,
                     success, details, response_time)
        
        # Search memorials
        search_data = {"query": "test"}
        success, response, details, response_time = self.make_request(
            "POST", "/api/v1/memorials/search", json=search_data, auth_token=access_token)
        self.log_test("memorial_endpoints", "/api/v1/memorials/search", "POST",
                     response.status_code if response else 0,
                     success, details, response_time)
        
        # Test memorial-specific endpoints if we have an ID
        if memorial_id:
            # Get memorial details
            success, response, details, response_time = self.make_request(
                "GET", f"/api/v1/memorials/{memorial_id}", auth_token=access_token)
            self.log_test("memorial_endpoints", f"/api/v1/memorials/{memorial_id}", "GET",
                         response.status_code if response else 0,
                         success, details, response_time)
            
            # Update memorial
            update_data = {"biography": "Updated test memorial biography."}
            success, response, details, response_time = self.make_request(
                "PUT", f"/api/v1/memorials/{memorial_id}", json=update_data, auth_token=access_token)
            self.log_test("memorial_endpoints", f"/api/v1/memorials/{memorial_id}", "PUT",
                         response.status_code if response else 0,
                         success, details, response_time)
            
            # Get memorial statistics
            success, response, details, response_time = self.make_request(
                "GET", f"/api/v1/memorials/{memorial_id}/stats", auth_token=access_token)
            self.log_test("memorial_endpoints", f"/api/v1/memorials/{memorial_id}/stats", "GET",
                         response.status_code if response else 0,
                         success, details, response_time)
            
            # Update memorial slug
            new_slug_data = {"new_slug": f"comprehensive-test-{int(time.time())}"}
            success, response, details, response_time = self.make_request(
                "PUT", f"/api/v1/memorials/{memorial_id}/slug", json=new_slug_data, auth_token=access_token)
            self.log_test("memorial_endpoints", f"/api/v1/memorials/{memorial_id}/slug", "PUT",
                         response.status_code if response else 0,
                         success, details, response_time)
            
            # Delete memorial (cleanup)
            success, response, details, response_time = self.make_request(
                "DELETE", f"/api/v1/memorials/{memorial_id}", auth_token=access_token)
            self.log_test("memorial_endpoints", f"/api/v1/memorials/{memorial_id}", "DELETE",
                         response.status_code if response else 0,
                         success, details, response_time)
        
        # Test public memorial access
        success, response, details, response_time = self.make_request(
            "GET", "/api/v1/memorials/non-existent-slug/public")
        # For this test, 404 is the expected behavior, so adjust success criteria
        expected_success = response and response.status_code == 404
        self.log_test("memorial_endpoints", "/api/v1/memorials/{slug}/public", "GET",
                     response.status_code if response else 0,
                     expected_success, "Expected 404 for non-existent memorial", response_time)
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING & EDGE CASES")
        print("="*60)
        
        # Test invalid endpoints
        success, response, details, response_time = self.make_request("GET", "/api/v1/invalid")
        expected_success = response and response.status_code == 404
        self.log_test("error_tests", "/api/v1/invalid", "GET",
                     response.status_code if response else 0,
                     expected_success, "Expected 404 for invalid endpoint", response_time)
        
        # Test unauthorized access to protected endpoints
        success, response, details, response_time = self.make_request("GET", "/api/v1/auth/me")
        expected_success = response and response.status_code == 401
        self.log_test("error_tests", "/api/v1/auth/me", "GET",
                     response.status_code if response else 0,
                     expected_success, "Expected 401 without auth token", response_time)
        
        # Test invalid login
        invalid_login = {"email": "invalid@example.com", "password": "wrongpass"}
        success, response, details, response_time = self.make_request(
            "POST", "/api/v1/auth/login", json=invalid_login)
        expected_success = response and response.status_code in [400, 401, 404]
        self.log_test("error_tests", "/api/v1/auth/login", "POST",
                     response.status_code if response else 0,
                     expected_success, "Expected error for invalid login", response_time)
    
    def generate_report(self):
        """Generate comprehensive test report."""
        self.results["summary"]["end_time"] = datetime.now()
        duration = self.results["summary"]["end_time"] - self.results["summary"]["start_time"]
        
        print("\n" + "="*80)
        print("             COMPREHENSIVE API TEST REPORT")
        print("="*80)
        
        # Summary statistics
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        
        print(f"\nEXECUTION SUMMARY:")
        print(f"  Test Duration: {duration.total_seconds():.2f} seconds")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ✅")
        print(f"  Failed: {failed} ❌")
        print(f"  Success Rate: {(passed/total*100):.1f}%")
        
        # Detailed results by category
        categories = [
            ("SYSTEM ENDPOINTS", "system_endpoints"),
            ("AUTHENTICATION ENDPOINTS", "auth_endpoints"),
            ("MEMORIAL ENDPOINTS", "memorial_endpoints"), 
            ("ERROR HANDLING TESTS", "error_tests")
        ]
        
        for category_name, category_key in categories:
            results = self.results[category_key]
            if not results:
                continue
                
            passed_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            print(f"\n{category_name} ({passed_count}/{total_count} passed):")
            print("-" * 60)
            
            for result in results:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {result['method']} {result['endpoint']} "
                      f"({result['response_time']}) - {result['details']}")
        
        # Failing endpoints summary
        failed_tests = []
        for category_key in ["system_endpoints", "auth_endpoints", "memorial_endpoints", "error_tests"]:
            failed_tests.extend([r for r in self.results[category_key] if not r["success"]])
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS SUMMARY ({len(failed_tests)} failures):")
            print("-" * 60)
            for test in failed_tests:
                print(f"  ❌ {test['method']} {test['endpoint']} - {test['details']}")
        
        # Working endpoints summary
        working_tests = []
        for category_key in ["system_endpoints", "auth_endpoints", "memorial_endpoints", "error_tests"]:
            working_tests.extend([r for r in self.results[category_key] if r["success"]])
        
        print(f"\n✅ WORKING ENDPOINTS SUMMARY ({len(working_tests)} endpoints):")
        print("-" * 60)
        for test in working_tests[:15]:  # Show first 15 to keep output manageable
            print(f"  ✅ {test['method']} {test['endpoint']}")
        if len(working_tests) > 15:
            print(f"  ... and {len(working_tests) - 15} more working endpoints")
        
        # JWT tokens for manual testing
        if any(self.tokens.values()):
            print(f"\n🔑 AUTHENTICATION TOKENS:")
            print("-" * 60)
            for token_type, token in self.tokens.items():
                if token:
                    print(f"  {token_type.upper()}: {token[:50]}...")
        
        print("\n" + "="*80)
        
        # Overall health assessment
        if passed / total >= 0.9:
            print("🟢 API HEALTH: EXCELLENT (≥90% success rate)")
        elif passed / total >= 0.8:
            print("🟡 API HEALTH: GOOD (80-89% success rate)")
        elif passed / total >= 0.7:
            print("🟠 API HEALTH: FAIR (70-79% success rate)")
        else:
            print("🔴 API HEALTH: POOR (<70% success rate)")
        
        print("="*80)
        
        return passed / total
    
    def run_all_tests(self):
        """Execute all test suites."""
        print("🚀 Starting Comprehensive API Testing Suite...")
        print(f"🎯 Target URL: {self.base_url}")
        print(f"⏰ Started at: {self.results['summary']['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.test_system_endpoints()
        self.test_auth_endpoints()
        self.test_memorial_endpoints()
        self.test_error_handling()
        
        return self.generate_report()


def main():
    """Main test execution."""
    tester = ComprehensiveAPITester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 0.8 else 1)


if __name__ == "__main__":
    main()