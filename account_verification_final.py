#!/usr/bin/env python3
"""
Corrected comprehensive account verification test with proper API response handling.
"""

import requests
import json
import time

def test_account_comprehensive():
    """Run all account verification tests"""
    session = requests.Session()
    base_url = "http://localhost:8000"
    test_email = "shaktee@maxseeding.vn"
    test_password = "Keren@3823"
    
    print("="*70)
    print("COMPREHENSIVE ACCOUNT VERIFICATION - FINAL TEST")
    print(f"Account: {test_email}")
    print(f"Password: {test_password}")
    print("="*70)
    
    results = {}
    
    # Test 1: Hebrew Login Form Accessibility
    print("\n1. Testing Hebrew Login Form Accessibility...")
    try:
        response = session.get(f"{base_url}/he/login")
        if response.status_code == 200:
            content = response.text
            has_email = 'type="email"' in content
            has_password = 'type="password"' in content
            has_form = '<form' in content
            has_hebrew = 'dir="rtl"' in content and 'hebrew_rtl.css' in content
            
            test1_pass = all([has_email, has_password, has_form, has_hebrew])
            results["hebrew_login_form"] = test1_pass
            print(f"   {'✓' if test1_pass else '✗'} Hebrew login form: {test1_pass}")
        else:
            results["hebrew_login_form"] = False
            print(f"   ✗ Hebrew login form: Failed (status {response.status_code})")
    except Exception as e:
        results["hebrew_login_form"] = False
        print(f"   ✗ Hebrew login form: Error - {e}")
    
    # Test 2: Login API and JWT Tokens
    print("\n2. Testing Login API and JWT Tokens...")
    access_token = None
    try:
        login_data = {"email": test_email, "password": test_password}
        response = session.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            token_type = data.get('token_type')
            
            test2_pass = (access_token and len(access_token) > 50 and 
                         refresh_token and len(refresh_token) > 50 and 
                         token_type == 'bearer')
            results["login_api_tokens"] = test2_pass
            print(f"   {'✓' if test2_pass else '✗'} Login API and tokens: {test2_pass}")
        else:
            results["login_api_tokens"] = False
            print(f"   ✗ Login API and tokens: Failed (status {response.status_code})")
    except Exception as e:
        results["login_api_tokens"] = False
        print(f"   ✗ Login API and tokens: Error - {e}")
    
    # Test 3: Authentication Cookies
    print("\n3. Testing Authentication Cookies...")
    try:
        cookies = dict(session.cookies)
        auth_cookie = any('access_token' in name or 'auth' in name.lower() for name in cookies.keys())
        results["auth_cookies"] = auth_cookie
        print(f"   {'✓' if auth_cookie else '✗'} Authentication cookies: {auth_cookie} ({len(cookies)} total cookies)")
    except Exception as e:
        results["auth_cookies"] = False
        print(f"   ✗ Authentication cookies: Error - {e}")
    
    # Test 4: Protected Hebrew Routes Access
    print("\n4. Testing Protected Hebrew Routes Access...")
    try:
        headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
        response = session.get(f"{base_url}/he/dashboard", headers=headers)
        
        if response.status_code == 200:
            content = response.text.lower()
            has_dashboard_content = 'dashboard' in content
            has_protected_content = 'memorial' in content or 'הנצח' in content
            no_login_form = content.count('type="email"') == 0 and content.count('type="password"') == 0
            
            test4_pass = has_dashboard_content and has_protected_content and no_login_form
            results["protected_routes"] = test4_pass
            print(f"   {'✓' if test4_pass else '✗'} Protected Hebrew routes: {test4_pass}")
        else:
            results["protected_routes"] = False
            print(f"   ✗ Protected Hebrew routes: Failed (status {response.status_code})")
    except Exception as e:
        results["protected_routes"] = False
        print(f"   ✗ Protected Hebrew routes: Error - {e}")
    
    # Test 5: Hebrew Navigation Authentication Status
    print("\n5. Testing Hebrew Navigation Authentication Status...")
    try:
        headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
        response = session.get(f"{base_url}/he/dashboard", headers=headers)
        
        if response.status_code == 200:
            content = response.text
            has_logout = 'התנתקות' in content or 'logout' in content.lower()
            has_nav = 'navbar' in content.lower() or 'navigation' in content.lower()
            has_user_menu = 'user' in content.lower() and 'menu' in content.lower()
            
            test5_pass = has_logout and has_nav
            results["nav_auth_status"] = test5_pass
            print(f"   {'✓' if test5_pass else '✗'} Hebrew navigation auth status: {test5_pass}")
        else:
            results["nav_auth_status"] = False
            print(f"   ✗ Hebrew navigation auth status: Failed (status {response.status_code})")
    except Exception as e:
        results["nav_auth_status"] = False
        print(f"   ✗ Hebrew navigation auth status: Error - {e}")
    
    # Test 6: Authentication Persistence
    print("\n6. Testing Authentication Persistence...")
    try:
        headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
        
        # First call
        response1 = session.get(f"{base_url}/api/v1/auth/me", headers=headers)
        if response1.status_code == 200:
            data1 = response1.json()
            # Handle nested user object
            user1 = data1.get('user', data1)  # Try nested first, fallback to root
            email1 = user1.get('email')
            user_id1 = user1.get('id')
            
            time.sleep(1)
            
            # Second call
            response2 = session.get(f"{base_url}/api/v1/auth/me", headers=headers)
            if response2.status_code == 200:
                data2 = response2.json()
                # Handle nested user object
                user2 = data2.get('user', data2)  # Try nested first, fallback to root
                email2 = user2.get('email')
                user_id2 = user2.get('id')
                
                test6_pass = (email1 == email2 == test_email and 
                             user_id1 == user_id2 and 
                             user_id1 is not None)
                results["auth_persistence"] = test6_pass
                print(f"   {'✓' if test6_pass else '✗'} Authentication persistence: {test6_pass} (User: {email1})")
            else:
                results["auth_persistence"] = False
                print(f"   ✗ Authentication persistence: Second call failed ({response2.status_code})")
        else:
            results["auth_persistence"] = False
            print(f"   ✗ Authentication persistence: First call failed ({response1.status_code})")
    except Exception as e:
        results["auth_persistence"] = False
        print(f"   ✗ Authentication persistence: Error - {e}")
    
    # Final Results Summary
    print("\n" + "="*70)
    print("FINAL TEST RESULTS SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    test_names = {
        "hebrew_login_form": "Hebrew Login Form Accessibility",
        "login_api_tokens": "Login API Success and JWT Tokens", 
        "auth_cookies": "Authentication Cookies",
        "protected_routes": "Protected Hebrew Routes Access",
        "nav_auth_status": "Hebrew Navigation Authentication Status",
        "auth_persistence": "Authentication Persistence"
    }
    
    for key, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_names[key]}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! ACCOUNT IS FULLY FUNCTIONAL")
        print("✅ The user account is ready for manual testing!")
        print(f"✅ Login URL: {base_url}/he/login")
        print(f"✅ Credentials: {test_email} / {test_password}")
        print("✅ All authentication flows working correctly")
        print("✅ Hebrew interface fully operational")
        return True
    else:
        print(f"\n❌ PARTIAL SUCCESS: {total - passed} test(s) failed")
        print("⚠️  The account may have issues during manual testing")
        return False

if __name__ == "__main__":
    success = test_account_comprehensive()
    print(f"\n{'='*70}")
    print(f"FINAL VERIFICATION: {'READY FOR USER TESTING' if success else 'NEEDS ATTENTION'}")
    print("="*70)
    exit(0 if success else 1)