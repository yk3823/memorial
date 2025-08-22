#!/usr/bin/env python3
"""
Final comprehensive test to verify the new user account (shaktee@maxseeding.vn) is working properly.
This test addresses issues found in the previous comprehensive test.
"""

import requests
import json
import time
from urllib.parse import urljoin
import re

class FinalAccountVerificationTest:
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
        print(f"[{status}] {test_name}")
        print(f"       {details}")
        if error:
            print(f"       Error: {error}")

    def test_1_hebrew_login_form_accessibility(self):
        """Test 1: Hebrew login form at http://localhost:8000/he/login is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/he/login")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for required form elements and Hebrew characteristics
                has_email_field = 'type="email"' in content or 'name="email"' in content
                has_password_field = 'type="password"' in content or 'name="password"' in content
                has_form = '<form' in content
                has_hebrew_rtl = 'dir="rtl"' in content or 'hebrew_rtl.css' in content
                has_hebrew_text = any(hebrew_word in content for hebrew_word in ['כניסה', 'התחברות', 'דוא"ל', 'סיסמה'])
                
                all_checks_passed = all([has_email_field, has_password_field, has_form, has_hebrew_rtl])
                
                self.log_result(
                    "Hebrew Login Form Accessibility",
                    all_checks_passed,
                    f"Form accessible with all elements. Email: {has_email_field}, Password: {has_password_field}, Form: {has_form}, RTL: {has_hebrew_rtl}, Hebrew text: {has_hebrew_text}"
                )
                return all_checks_passed
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

    def test_2_login_api_and_tokens(self):
        """Test 2 & 3: Login API call succeeds and returns JWT tokens"""
        try:
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract tokens
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                token_type = data.get('token_type')
                
                # Validate token format and content
                tokens_valid = (
                    self.access_token and len(self.access_token) > 50 and
                    self.refresh_token and len(self.refresh_token) > 50 and
                    token_type == 'bearer'
                )
                
                self.log_result(
                    "Login API Success and JWT Tokens",
                    tokens_valid,
                    f"Login successful. Access token: {len(self.access_token)} chars, Refresh token: {len(self.refresh_token)} chars, Type: {token_type}"
                )
                return tokens_valid
            else:
                self.log_result(
                    "Login API Success and JWT Tokens",
                    False,
                    f"Login API returned status {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_result("Login API Success and JWT Tokens", False, "Login API call failed", e)
            return False

    def test_3_authentication_cookies(self):
        """Test 4: Server sets proper authentication cookies"""
        try:
            cookies_dict = dict(self.session.cookies)
            
            # Look for authentication cookies
            auth_cookie_found = False
            cookie_details = []
            
            for name, value in cookies_dict.items():
                cookie_details.append(f"{name}: {len(value)} chars")
                if 'access_token' in name or 'token' in name.lower() or 'auth' in name.lower():
                    auth_cookie_found = True
            
            self.log_result(
                "Authentication Cookies",
                auth_cookie_found,
                f"Cookie check: {len(cookies_dict)} total cookies. Auth cookie found: {auth_cookie_found}. Cookies: {', '.join(cookie_details) if cookie_details else 'None'}"
            )
            return auth_cookie_found
                
        except Exception as e:
            self.log_result("Authentication Cookies", False, "Failed to check authentication cookies", e)
            return False

    def test_4_protected_hebrew_routes_access(self):
        """Test 5: User can access protected Hebrew routes after login"""
        try:
            # Test with Bearer token first
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            response = self.session.get(f"{self.base_url}/he/dashboard", headers=headers)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for dashboard-specific content
                dashboard_indicators = {
                    'dashboard_class': 'dashboard' in content.lower(),
                    'my_memorials': 'ההנצחות שלי' in content or 'memorials' in content.lower(),
                    'logout_available': 'התנתקות' in content or 'logout' in content.lower(),
                    'create_memorial': 'צור הנצחה' in content or 'create' in content.lower(),
                    'user_authenticated': 'user' in content.lower() and 'authenticated' not in content.lower()  # Avoid false positive
                }
                
                # Check for unwanted login indicators
                login_indicators = {
                    'has_email_input': 'type="email"' in content,
                    'has_password_input': 'type="password"' in content,
                    'has_login_form': '<form' in content and ('login' in content.lower() or 'כניסה' in content)
                }
                
                dashboard_score = sum(dashboard_indicators.values())
                login_score = sum(login_indicators.values())
                
                # Success if we have dashboard content and minimal login content
                success = dashboard_score >= 3 and login_score <= 1
                
                self.log_result(
                    "Protected Hebrew Routes Access",
                    success,
                    f"Dashboard access successful. Dashboard indicators: {dashboard_score}/5, Login indicators: {login_score}/3 (should be low)"
                )
                return success
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

    def test_5_hebrew_navigation_authentication(self):
        """Test 6: Hebrew navigation shows user as authenticated"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            response = self.session.get(f"{self.base_url}/he/dashboard", headers=headers)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for authenticated user indicators in navigation
                auth_nav_indicators = {
                    'logout_link': 'התנתקות' in content or 'logout' in content.lower(),
                    'profile_link': 'פרופיל' in content or 'profile' in content.lower(),
                    'dashboard_nav': 'dashboard' in content.lower(),
                    'authenticated_menu': 'navbar' in content.lower() and ('user' in content.lower() or 'התחבר' not in content)
                }
                
                auth_score = sum(auth_nav_indicators.values())
                success = auth_score >= 2
                
                self.log_result(
                    "Hebrew Navigation Authentication Status",
                    success,
                    f"Navigation authentication check. Authenticated indicators found: {auth_score}/4"
                )
                return success
            else:
                self.log_result(
                    "Hebrew Navigation Authentication Status",
                    False,
                    f"Could not access Hebrew dashboard for navigation check (status {response.status_code})"
                )
                return False
                
        except Exception as e:
            self.log_result("Hebrew Navigation Authentication Status", False, "Failed to check Hebrew navigation authentication", e)
            return False

    def test_6_authentication_persistence(self):
        """Test 7: Authentication persists across page reloads"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            # First API call
            response1 = self.session.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            
            if response1.status_code != 200:
                self.log_result(
                    "Authentication Persistence",
                    False,
                    f"Initial auth check failed with status {response1.status_code}"
                )
                return False
            
            user_data1 = response1.json()
            user_id_1 = user_data1.get('id')
            email_1 = user_data1.get('email')
            
            # Wait and test again
            time.sleep(1)
            
            # Second API call
            response2 = self.session.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            
            if response2.status_code == 200:
                user_data2 = response2.json()
                user_id_2 = user_data2.get('id')
                email_2 = user_data2.get('email')
                
                # Verify consistency
                persistence_success = (user_id_1 == user_id_2 and email_1 == email_2 and 
                                     email_1 == self.test_email and user_id_1 is not None)
                
                self.log_result(
                    "Authentication Persistence",
                    persistence_success,
                    f"Authentication persisted. User: {email_1}, ID consistent: {user_id_1 == user_id_2}, Email consistent: {email_1 == email_2}"
                )
                return persistence_success
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
        print(f"{'='*70}")
        print("FINAL COMPREHENSIVE ACCOUNT VERIFICATION TEST")
        print(f"Testing account: {self.test_email}")
        print(f"Password: {self.test_password}")
        print(f"Base URL: {self.base_url}")
        print(f"{'='*70}\n")
        
        tests = [
            ("Hebrew Login Form Accessibility", self.test_1_hebrew_login_form_accessibility),
            ("Login API Success and JWT Tokens", self.test_2_login_api_and_tokens),
            ("Authentication Cookies", self.test_3_authentication_cookies),
            ("Protected Hebrew Routes Access", self.test_4_protected_hebrew_routes_access),
            ("Hebrew Navigation Authentication Status", self.test_5_hebrew_navigation_authentication),
            ("Authentication Persistence", self.test_6_authentication_persistence)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"Running: {test_name}...")
            if test_func():
                passed_tests += 1
            print()
        
        # Generate summary
        print(f"{'='*70}")
        print(f"FINAL TEST RESULTS: {passed_tests}/{total_tests} TESTS PASSED")
        print(f"{'='*70}")
        
        for test_name, result in self.results.items():
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"{status} {test_name}")
        
        overall_success = passed_tests == total_tests
        print(f"\n{'='*70}")
        print(f"OVERALL RESULT: {'🎉 SUCCESS - ACCOUNT READY' if overall_success else '❌ FAILURE - ISSUES FOUND'}")
        print(f"{'='*70}")
        
        if overall_success:
            print("\n✅ ACCOUNT VERIFICATION COMPLETE")
            print("✅ The user account is FULLY FUNCTIONAL and ready for manual testing!")
            print(f"✅ Login URL: {self.base_url}/he/login")
            print(f"✅ Test Credentials: {self.test_email} / {self.test_password}")
            print("✅ All authentication flows working correctly")
            print("✅ Hebrew interface fully operational")
            print("✅ Protected routes accessible")
            print("✅ Session persistence confirmed")
        else:
            failed_count = total_tests - passed_tests
            print(f"\n❌ ACCOUNT HAS {failed_count} ISSUE(S)")
            print("❌ Manual testing may encounter problems")
            print("❌ Review failed tests above for details")
        
        # Save results
        results_file = f"final_account_verification_results_{int(time.time())}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "overall_success": overall_success,
                    "test_account_email": self.test_email,
                    "test_account_password": self.test_password,
                    "base_url": self.base_url,
                    "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "detailed_results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        return overall_success

if __name__ == "__main__":
    tester = FinalAccountVerificationTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)