#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script for Memorial Website
Tests all endpoints systematically and reports results.
"""
import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.test_user = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        self.results = {
            "passed": [],
            "failed": [],
            "total_tests": 0
        }
    
    def log_result(self, endpoint: str, method: str, status: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": "✅ PASS" if status else "❌ FAIL",
            "details": details,
            "response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        if status:
            self.results["passed"].append(result)
        else:
            self.results["failed"].append(result)
        self.results["total_tests"] += 1
        
        print(f"{result['status']} {method} {endpoint} ({result['response_time']}) - {details}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, requests.Response, str]:
        """Make HTTP request and return success status, response, and details"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            # Add auth header if we have a token
            if self.access_token and 'headers' not in kwargs:
                kwargs['headers'] = {}
            if self.access_token and 'headers' in kwargs:
                kwargs['headers']['Authorization'] = f"Bearer {self.access_token}"
            
            response = self.session.request(method, url, **kwargs)
            response_time = time.time() - start_time
            
            # Consider 2xx and 3xx as success for most cases
            success = response.status_code < 400
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', response.text[:100])}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_result(endpoint, method, success, details, response_time)
            return success, response, details
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            details = f"Request failed: {str(e)}"
            self.log_result(endpoint, method, False, details, response_time)
            return False, None, details
    
    def test_system_endpoints(self):
        """Test system health and info endpoints"""
        print("\n=== TESTING SYSTEM ENDPOINTS ===")
        
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/api/"),
            ("GET", "/api/health"),
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/info")
        ]
        
        for method, endpoint in endpoints:
            self.make_request(method, endpoint)
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== TESTING AUTHENTICATION ENDPOINTS ===")
        
        # Test user registration
        register_data = {
            **self.test_user,
            "confirm_password": self.test_user["password"]
        }
        success, response, _ = self.make_request("POST", "/api/v1/auth/register", 
                                                json=register_data)
        
        if success and response:
            print("✅ User registration successful")
        else:
            print("❌ User registration failed - will try to login with existing user")
        
        # Test user login
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"],
            "remember_me": False
        }
        
        success, response, _ = self.make_request("POST", "/api/v1/auth/login",
                                               json=login_data)
        
        if success and response:
            try:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                print(f"✅ Login successful, got access token: {self.access_token[:20]}...")
            except:
                print("❌ Login response format issue")
        
        # Test authenticated endpoints
        if self.access_token:
            # Test get current user info
            self.make_request("GET", "/api/v1/auth/me")
            
            # Test change password
            change_password_data = {
                "current_password": self.test_user["password"],
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            }
            self.make_request("POST", "/api/v1/auth/change-password", 
                            json=change_password_data)
            
            # Test update profile
            profile_data = {
                "first_name": "Updated",
                "last_name": "Test User",
                "phone_number": "+1987654321"
            }
            self.make_request("PUT", "/api/v1/auth/profile", json=profile_data)
            
            # Test token refresh
            if self.refresh_token:
                refresh_data = {"refresh_token": self.refresh_token}
                self.make_request("POST", "/api/v1/auth/refresh", json=refresh_data)
        
        # Test endpoints that don't require existing auth
        # Test forgot password
        forgot_data = {"email": self.test_user["email"]}
        self.make_request("POST", "/api/v1/auth/forgot-password", json=forgot_data)
        
        # Test resend verification
        resend_data = {"email": self.test_user["email"]}
        self.make_request("POST", "/api/v1/auth/resend-verification", json=resend_data)
        
        # Test email verification (will fail without valid token, but we test the endpoint)
        self.make_request("GET", "/api/v1/auth/verify-email?token=invalid_token")
        
        # Test password reset (will fail without valid token, but we test the endpoint)
        reset_data = {
            "token": "invalid_token",
            "new_password": "ResetPassword123!",
            "confirm_password": "ResetPassword123!"
        }
        self.make_request("POST", "/api/v1/auth/reset-password", json=reset_data)
        
        # Test logout (should be last)
        if self.access_token:
            self.make_request("POST", "/api/v1/auth/logout")
    
    def test_memorial_endpoints(self):
        """Test memorial endpoints"""
        print("\n=== TESTING MEMORIAL ENDPOINTS ===")
        
        # Get a fresh authentication token for memorial testing
        print("Getting fresh authentication for memorial tests...")
        login_data = {
            "email": self.test_user["email"],
            "password": "NewPassword123!",  # Use new password from change password test
            "remember_me": False
        }
        
        success, response, _ = self.make_request("POST", "/api/v1/auth/login",
                                               json=login_data)
        
        if not success or not response:
            print("❌ Failed to authenticate for memorial testing - trying original password")
            login_data["password"] = self.test_user["password"]
            success, response, _ = self.make_request("POST", "/api/v1/auth/login",
                                                   json=login_data)
            
        if success and response:
            try:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                print("✅ Memorial testing authentication successful")
            except:
                print("❌ Failed to parse login response")
                return
        else:
            print("❌ No access token available - skipping memorial endpoint tests")
            return
        
        memorial_data = {
            "deceased_name_hebrew": "שלום עליכם",
            "deceased_name_english": "Peace Be Upon You",
            "birth_date_gregorian": "1950-01-01",
            "death_date_gregorian": "2020-01-01",
            "biography": "This is a test memorial biography for API testing purposes.",
            "is_public": True
        }
        
        # Test create memorial
        success, response, _ = self.make_request("POST", "/api/v1/memorials", 
                                               json=memorial_data)
        
        memorial_id = None
        memorial_slug = None
        if success and response:
            try:
                memorial = response.json()
                memorial_id = memorial.get("id")
                memorial_slug = memorial.get("slug")
                print(f"✅ Memorial created with ID: {memorial_id}")
            except:
                print("❌ Memorial creation response format issue")
        
        # Test list user memorials
        self.make_request("GET", "/api/v1/memorials")
        
        # Test memorial search
        search_data = {"query": "test"}
        self.make_request("POST", "/api/v1/memorials/search", json=search_data)
        
        # Test endpoints that require memorial ID
        if memorial_id:
            # Test get memorial details
            self.make_request("GET", f"/api/v1/memorials/{memorial_id}")
            
            # Test update memorial
            update_data = {
                "biography": "Updated test memorial biography."
            }
            self.make_request("PUT", f"/api/v1/memorials/{memorial_id}", 
                            json=update_data)
            
            # Test memorial statistics
            self.make_request("GET", f"/api/v1/memorials/{memorial_id}/stats")
            
            # Test update memorial slug
            new_slug_data = {"new_slug": f"updated-test-memorial-{int(time.time())}"}
            self.make_request("PUT", f"/api/v1/memorials/{memorial_id}/slug", 
                            json=new_slug_data)
        
        # Test public memorial access (if we have a slug)
        if memorial_slug:
            self.make_request("GET", f"/api/v1/memorials/{memorial_slug}/public")
        else:
            # Try with a test slug that should return 404
            self.make_request("GET", "/api/v1/memorials/non-existent-memorial/public")
        
        # Test delete memorial (should be last)
        if memorial_id:
            self.make_request("DELETE", f"/api/v1/memorials/{memorial_id}")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("                    API ENDPOINT TEST RESULTS")
        print("="*80)
        
        total = self.results["total_tests"]
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        
        print(f"\nSUMMARY:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ✅")
        print(f"  Failed: {failed} ❌")
        print(f"  Success Rate: {(passed/total*100):.1f}%")
        
        if self.results["passed"]:
            print(f"\n✅ WORKING ENDPOINTS ({len(self.results['passed'])}):")
            for result in self.results["passed"]:
                print(f"  ✅ {result['method']} {result['endpoint']} - {result['details']}")
        
        if self.results["failed"]:
            print(f"\n❌ FAILING ENDPOINTS ({len(self.results['failed'])}):")
            for result in self.results["failed"]:
                print(f"  ❌ {result['method']} {result['endpoint']} - {result['details']}")
        
        # Print JWT tokens if available
        if self.access_token:
            print(f"\n🔑 JWT ACCESS TOKEN (for further testing):")
            print(f"  {self.access_token}")
        
        if self.refresh_token:
            print(f"\n🔄 JWT REFRESH TOKEN:")
            print(f"  {self.refresh_token}")
        
        print("\n" + "="*80)
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("Starting comprehensive API endpoint testing...")
        print(f"Base URL: {self.base_url}")
        print(f"Test User Email: {self.test_user['email']}")
        
        start_time = time.time()
        
        # Run tests in order
        self.test_system_endpoints()
        self.test_auth_endpoints()
        self.test_memorial_endpoints()
        
        total_time = time.time() - start_time
        print(f"\nTotal testing time: {total_time:.2f} seconds")
        
        # Print summary
        self.print_summary()


def main():
    """Main function to run API tests"""
    tester = APITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()