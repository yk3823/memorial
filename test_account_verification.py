#!/usr/bin/env python3
"""
Comprehensive test to verify the new user account (shaktee@maxseeding.vn) is working properly.

Tests:
1. Hebrew login form accessibility at http://localhost:8000/he/login
2. Login API call with JWT tokens
3. Authentication cookies setting
4. Access to protected Hebrew routes
5. Hebrew navigation authentication status
6. Authentication persistence across page reloads
"""

import requests
import json
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

class AccountVerificationTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_email = "shaktee@maxseeding.vn"
        self.test_password = "Keren@3823"
        self.results = {}
        self.access_token = None
        self.refresh_token = None
        
    def log_result(self, test_name, passed, details, error=None):
        """Log test result"""
        self.results[test_name] = {
            "passed": passed,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {details}")
        if error:
            print(f"       Error: {error}")

    def test_1_hebrew_login_form_accessibility(self):
        """Test 1: Hebrew login form at http://localhost:8000/he/login is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/he/login")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for Hebrew login form elements
                email_field = soup.find('input', {'type': 'email'}) or soup.find('input', {'name': 'email'})
                password_field = soup.find('input', {'type': 'password'}) or soup.find('input', {'name': 'password'})
                form = soup.find('form')
                
                if email_field and password_field and form:
                    # Check for Hebrew RTL elements or Hebrew text
                    has_hebrew_elements = (
                        soup.find(attrs={"dir": "rtl"}) or 
                        soup.find(class_=re.compile(r'hebrew|rtl', re.I)) or
                        'hebrew_rtl.css' in response.text or
                        'rtl' in response.text.lower()
                    )
                    
                    self.log_result(
                        "Hebrew Login Form Accessibility",
                        True,
                        f"Hebrew login form accessible at /he/login. Form elements found: email={bool(email_field)}, password={bool(password_field)}, Hebrew elements={has_hebrew_elements}"
                    )
                    return True
                else:
                    self.log_result(
                        "Hebrew Login Form Accessibility",
                        False,
                        f"Login form elements missing. Email field: {bool(email_field)}, Password field: {bool(password_field)}, Form: {bool(form)}"
                    )
                    return False
            else:
                self.log_result(
                    "Hebrew Login Form Accessibility",
                    False,
                    f"Hebrew login page returned status {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Hebrew Login Form Accessibility", False, "Failed to access Hebrew login form", e)
            return False

    def test_2_login_api_success_and_tokens(self):
        """Test 2 & 3: Login API call succeeds and returns JWT tokens"""
        try:
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required token fields
                has_access_token = 'access_token' in data and data['access_token']
                has_refresh_token = 'refresh_token' in data and data['refresh_token']
                has_token_type = 'token_type' in data and data['token_type'] == 'bearer'
                
                if has_access_token and has_refresh_token and has_token_type:
                    self.access_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    
                    self.log_result(
                        "Login API Success and JWT Tokens",
                        True,
                        f"Login successful. Tokens received: access_token={len(self.access_token)} chars, refresh_token={len(self.refresh_token)} chars, token_type={data['token_type']}"
                    )
                    return True
                else:
                    self.log_result(
                        "Login API Success and JWT Tokens",
                        False,
                        f"Missing token fields. access_token: {has_access_token}, refresh_token: {has_refresh_token}, token_type: {has_token_type}"
                    )
                    return False
            else:
                self.log_result(
                    "Login API Success and JWT Tokens",
                    False,
                    f"Login API returned status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Login API Success and JWT Tokens", False, "Login API call failed", e)
            return False

    def test_3_authentication_cookies(self):
        """Test 4: Server sets proper authentication cookies"""
        try:
            # Check cookies from the session after login
            cookies_dict = dict(self.session.cookies)
            
            # Look for authentication-related cookies
            auth_cookies = {}
            for name, value in cookies_dict.items():
                if any(keyword in name.lower() for keyword in ['auth', 'token', 'session', 'access', 'refresh']):
                    auth_cookies[name] = value
            
            if auth_cookies:
                cookie_details = ", ".join([f"{k}={v[:20]}..." if len(v) > 20 else f"{k}={v}" for k, v in auth_cookies.items()])
                self.log_result(
                    "Authentication Cookies",
                    True,
                    f"Authentication cookies set: {cookie_details}"
                )
                return True
            else:
                # Check if we have any cookies at all
                if cookies_dict:
                    cookie_list = ", ".join(cookies_dict.keys())
                    self.log_result(
                        "Authentication Cookies",
                        False,
                        f"No authentication cookies found. Available cookies: {cookie_list}"
                    )
                else:
                    self.log_result(
                        "Authentication Cookies",
                        False,
                        "No cookies set by server"
                    )
                return False
                
        except Exception as e:
            self.log_result("Authentication Cookies", False, "Failed to check authentication cookies", e)
            return False

    def test_4_protected_hebrew_routes_access(self):
        """Test 5: User can access protected Hebrew routes after login"""
        try:
            # Try to access Hebrew dashboard (protected route)
            headers = {}
            if self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'
            
            response = self.session.get(f"{self.base_url}/he/dashboard", headers=headers)
            
            if response.status_code == 200:
                # Check if we got the dashboard content (not a login redirect)
                content = response.text.lower()
                is_dashboard = any(keyword in content for keyword in ['dashboard', 'דשבורד', 'לוח בקרה', 'ראשי'])
                is_login_redirect = 'login' in content and ('form' in content or 'כניסה' in content)
                
                if is_dashboard and not is_login_redirect:
                    self.log_result(
                        "Protected Hebrew Routes Access",
                        True,
                        "Successfully accessed Hebrew dashboard with authentication"
                    )
                    return True
                else:
                    self.log_result(
                        "Protected Hebrew Routes Access",
                        False,
                        f"Dashboard access unclear. Is dashboard: {is_dashboard}, Is login redirect: {is_login_redirect}"
                    )
                    return False
            elif response.status_code == 302 or response.status_code == 307:
                # Check if redirected to login
                location = response.headers.get('Location', '')
                if 'login' in location:
                    self.log_result(
                        "Protected Hebrew Routes Access",
                        False,
                        f"Redirected to login page: {location}"
                    )
                else:
                    self.log_result(
                        "Protected Hebrew Routes Access",
                        False,
                        f"Unexpected redirect to: {location}"
                    )
                return False
            else:
                self.log_result(
                    "Protected Hebrew Routes Access",
                    False,
                    f"Hebrew dashboard returned status {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Protected Hebrew Routes Access", False, "Failed to access protected Hebrew routes", e)
            return False

    def test_5_hebrew_navigation_authentication_status(self):
        """Test 6: Hebrew navigation shows user as authenticated"""
        try:
            # Get Hebrew dashboard and check navigation for authentication indicators
            headers = {}
            if self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'
                
            response = self.session.get(f"{self.base_url}/he/dashboard", headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for authentication indicators in navigation
                auth_indicators = []
                
                # Check for logout links/buttons
                logout_elements = soup.find_all(['a', 'button'], string=re.compile(r'יציאה|logout|sign out', re.I))
                if logout_elements:
                    auth_indicators.append("logout_link")
                
                # Check for user name or profile indicators
                user_elements = soup.find_all(['span', 'div', 'a'], string=re.compile(r'שלום|hello|welcome|profile|פרופיל', re.I))
                if user_elements:
                    auth_indicators.append("user_greeting")
                
                # Check for authenticated navigation items (dashboard, profile, etc.)
                nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu', re.I))
                auth_nav_found = False
                for nav in nav_elements:
                    nav_text = nav.get_text().lower()
                    if any(keyword in nav_text for keyword in ['dashboard', 'profile', 'דשבורד', 'פרופיל']):
                        auth_nav_found = True
                        break
                
                if auth_nav_found:
                    auth_indicators.append("authenticated_navigation")
                
                if auth_indicators:
                    self.log_result(
                        "Hebrew Navigation Authentication Status",
                        True,
                        f"Navigation shows user as authenticated. Indicators: {', '.join(auth_indicators)}"
                    )
                    return True
                else:
                    self.log_result(
                        "Hebrew Navigation Authentication Status",
                        False,
                        "No authentication indicators found in Hebrew navigation"
                    )
                    return False
            else:
                self.log_result(
                    "Hebrew Navigation Authentication Status",
                    False,
                    f"Could not access Hebrew dashboard to check navigation (status {response.status_code})"
                )
                return False
                
        except Exception as e:
            self.log_result("Hebrew Navigation Authentication Status", False, "Failed to check Hebrew navigation authentication status", e)
            return False

    def test_6_authentication_persistence(self):
        """Test 7: Authentication persists across page reloads"""
        try:
            # First, verify we're authenticated
            headers = {}
            if self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'
                
            # Test /api/v1/auth/me endpoint
            response1 = self.session.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            
            if response1.status_code != 200:
                self.log_result(
                    "Authentication Persistence",
                    False,
                    f"Initial auth check failed with status {response1.status_code}"
                )
                return False
            
            user_data1 = response1.json()
            
            # Wait a moment and test again (simulating page reload)
            time.sleep(1)
            
            response2 = self.session.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            
            if response2.status_code == 200:
                user_data2 = response2.json()
                
                # Compare user data to ensure it's the same user
                if (user_data1.get('email') == user_data2.get('email') and 
                    user_data1.get('id') == user_data2.get('id')):
                    
                    self.log_result(
                        "Authentication Persistence",
                        True,
                        f"Authentication persisted across requests. User: {user_data1.get('email')}, ID: {user_data1.get('id')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Authentication Persistence",
                        False,
                        "User data inconsistent between requests"
                    )
                    return False
            else:
                self.log_result(
                    "Authentication Persistence",
                    False,
                    f"Second auth check failed with status {response2.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Authentication Persistence", False, "Failed to test authentication persistence", e)
            return False

    def run_all_tests(self):
        """Run all tests and return overall result"""
        print(f"\n{'='*60}")
        print("COMPREHENSIVE ACCOUNT VERIFICATION TEST")
        print(f"Testing account: {self.test_email}")
        print(f"Base URL: {self.base_url}")
        print(f"{'='*60}\n")
        
        tests = [
            self.test_1_hebrew_login_form_accessibility,
            self.test_2_login_api_success_and_tokens,
            self.test_3_authentication_cookies,
            self.test_4_protected_hebrew_routes_access,
            self.test_5_hebrew_navigation_authentication_status,
            self.test_6_authentication_persistence
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
        
        # Generate summary
        print(f"{'='*60}")
        print(f"TEST SUMMARY: {passed_tests}/{total_tests} TESTS PASSED")
        print(f"{'='*60}")
        
        for test_name, result in self.results.items():
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {test_name}")
            if not result["passed"] and result["error"]:
                print(f"       Error: {result['error']}")
        
        overall_success = passed_tests == total_tests
        print(f"\nOVERALL RESULT: {'SUCCESS' if overall_success else 'FAILURE'}")
        
        if overall_success:
            print("\n✓ The account is READY for manual testing in the browser!")
            print(f"✓ User can login at: {self.base_url}/he/login")
            print(f"✓ Credentials: {self.test_email} / {self.test_password}")
        else:
            print(f"\n✗ The account has {total_tests - passed_tests} failing test(s)")
            print("✗ Manual testing may encounter issues")
        
        # Save results to file
        results_file = "account_verification_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "overall_success": overall_success,
                    "test_account": self.test_email,
                    "base_url": self.base_url,
                    "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "detailed_results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return overall_success

if __name__ == "__main__":
    tester = AccountVerificationTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)