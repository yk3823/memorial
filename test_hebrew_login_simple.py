#!/usr/bin/env python3
"""
Simple Hebrew Login Flow Test
============================

Tests the Hebrew login flow using requests library for better cookie handling.
"""

import requests
import json
from datetime import datetime

def test_hebrew_login_flow():
    """Test the complete Hebrew login flow"""
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    results = []
    
    print("🧪 Testing Hebrew Login Flow")
    print("=" * 50)
    
    # Test 1: Access Hebrew login page
    print("📄 Test 1: Accessing Hebrew login page...")
    try:
        response = session.get(f"{base_url}/he/login")
        
        hebrew_content_checks = [
            "כניסה לחשבון" in response.text,  # Login to account
            "כתובת דוא\"ל" in response.text,   # Email address  
            "סיסמה" in response.text,          # Password
            "זכור אותי" in response.text,      # Remember me
            "dir=\"rtl\"" in response.text,    # RTL direction
            "lang=\"he\"" in response.text     # Hebrew language
        ]
        
        success = response.status_code == 200 and sum(hebrew_content_checks) >= 5
        print(f"   Status: {response.status_code}")
        print(f"   Hebrew elements found: {sum(hebrew_content_checks)}/6")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        results.append({
            "test": "Hebrew Login Page Access",
            "success": success,
            "status_code": response.status_code,
            "hebrew_elements": sum(hebrew_content_checks)
        })
        
    except Exception as e:
        print(f"   ❌ FAIL: {str(e)}")
        results.append({"test": "Hebrew Login Page Access", "success": False, "error": str(e)})
    
    # Test 2: Login API call
    print("\\n🔑 Test 2: Testing login API call...")
    try:
        login_data = {
            "email": "kolesnikovilj@extraku.net",
            "password": "J0seph123!",
            "remember_me": True
        }
        
        response = session.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        response_data = response.json()
        
        success = (
            response.status_code == 200 and
            response_data.get("success") is True and
            "access_token" in response_data and
            "refresh_token" in response_data
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Success field: {response_data.get('success')}")
        print(f"   Has access token: {'access_token' in response_data}")
        print(f"   Has refresh token: {'refresh_token' in response_data}")
        print(f"   Cookies received: {len(session.cookies)}")
        print(f"   Cookie names: {list(session.cookies.keys())}")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        results.append({
            "test": "Login API Call",
            "success": success,
            "status_code": response.status_code,
            "has_tokens": "access_token" in response_data,
            "cookies_count": len(session.cookies),
            "user_id": response_data.get("user", {}).get("id") if success else None
        })
        
        if not success:
            print(f"   Response: {response_data}")
        
    except Exception as e:
        print(f"   ❌ FAIL: {str(e)}")
        results.append({"test": "Login API Call", "success": False, "error": str(e)})
        success = False
    
    # Test 3: Access protected Hebrew route
    print("\\n🔒 Test 3: Testing protected Hebrew route access...")
    if success:  # Only test if login succeeded
        try:
            response = session.get(f"{base_url}/he/memorials")
            
            # Check if we're successfully accessing the memorials page
            success = (
                response.status_code == 200 and
                "כניסה לחשבון" not in response.text  # Should not see login form
            )
            
            # Additional checks
            has_memorials_content = any([
                "ההנצחות שלי" in response.text,
                "memorials" in response.text.lower(),
                "memorial" in response.text.lower()
            ])
            
            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")
            print(f"   Contains login form: {'כניסה לחשבון' in response.text}")
            print(f"   Has memorials content: {has_memorials_content}")
            print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
            
            results.append({
                "test": "Protected Route Access",
                "success": success,
                "status_code": response.status_code,
                "has_memorials_content": has_memorials_content,
                "redirected_to_login": "כניסה לחשבון" in response.text
            })
            
        except Exception as e:
            print(f"   ❌ FAIL: {str(e)}")
            results.append({"test": "Protected Route Access", "success": False, "error": str(e)})
    else:
        print("   ⏭️ SKIPPED: Login failed, cannot test protected routes")
        results.append({"test": "Protected Route Access", "success": False, "skipped": True})
    
    # Test 4: Hebrew navigation with authentication
    print("\\n🧭 Test 4: Testing Hebrew navigation (authenticated state)...")
    if success:  # Only test if login succeeded
        try:
            response = session.get(f"{base_url}/he")
            
            # Look for authenticated navigation elements
            auth_indicators = [
                "ההנצחות שלי" in response.text,      # My memorials
                "פרופיל אישי" in response.text,       # Personal profile
                "התנתק" in response.text,            # Logout
                "dropdown" in response.text.lower()   # User dropdown
            ]
            
            # Look for unauthenticated elements (should not be present)
            unauth_indicators = [
                'href="/he/login"' in response.text,
                'href="/he/register"' in response.text,
                ">התחבר<" in response.text,  # Login button
                ">הרשם<" in response.text    # Register button
            ]
            
            success = (
                response.status_code == 200 and
                sum(auth_indicators) >= 2 and
                sum(unauth_indicators) == 0
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Authenticated elements: {sum(auth_indicators)}/4")
            print(f"   Unauthenticated elements: {sum(unauth_indicators)}")
            print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
            
            results.append({
                "test": "Hebrew Navigation Authentication",
                "success": success,
                "status_code": response.status_code,
                "auth_elements": sum(auth_indicators),
                "unauth_elements": sum(unauth_indicators)
            })
            
        except Exception as e:
            print(f"   ❌ FAIL: {str(e)}")
            results.append({"test": "Hebrew Navigation Authentication", "success": False, "error": str(e)})
    else:
        print("   ⏭️ SKIPPED: Login failed, cannot test authenticated navigation")
        results.append({"test": "Hebrew Navigation Authentication", "success": False, "skipped": True})
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get("success"))
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\\n🎉 ALL TESTS PASSED - Hebrew login flow is working correctly!")
    else:
        print(f"\\n⚠️  {total_tests - passed_tests} test(s) failed - Hebrew login flow needs attention")
    
    # Save results
    with open('hebrew_login_test_results_simple.json', 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{passed_tests/total_tests*100:.1f}%",
                "overall_success": passed_tests == total_tests
            },
            "detailed_results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\\nDetailed results saved to: hebrew_login_test_results_simple.json")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = test_hebrew_login_flow()
    exit(0 if success else 1)