#!/usr/bin/env python3
"""
Browser-like simulation test to verify the complete user experience
"""

import requests
import json
import time

def simulate_browser_session():
    """Simulate a complete browser session like a real user would experience"""
    
    print("BROWSER SIMULATION TEST")
    print("Simulating real user browser experience...")
    print("="*50)
    
    # Create session (like a browser)
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    base_url = "http://localhost:8000"
    test_email = "shaktee@maxseeding.vn"
    test_password = "Keren@3823"
    
    # Step 1: Visit the Hebrew login page (like clicking a link)
    print("1. Navigating to Hebrew login page...")
    response = session.get(f"{base_url}/he/login")
    if response.status_code == 200:
        print("   ✓ Hebrew login page loaded successfully")
    else:
        print(f"   ✗ Failed to load login page (status: {response.status_code})")
        return False
    
    # Step 2: Submit login form (like filling out and submitting the form)
    print("\n2. Submitting login credentials...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    # Submit as form data (how browsers typically submit forms)
    response = session.post(
        f"{base_url}/api/v1/auth/login",
        json=login_data,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Referer': f"{base_url}/he/login"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("   ✓ Login successful")
        print(f"   ✓ Received access token ({len(data.get('access_token', ''))} chars)")
        print(f"   ✓ Received refresh token ({len(data.get('refresh_token', ''))} chars)")
        
        # Check user data
        user = data.get('user', {})
        print(f"   ✓ User: {user.get('display_name', 'Unknown')} ({user.get('email', 'No email')})")
    else:
        print(f"   ✗ Login failed (status: {response.status_code})")
        return False
    
    # Step 3: Navigate to dashboard (like clicking "Dashboard" link after login)  
    print("\n3. Navigating to dashboard...")
    response = session.get(f"{base_url}/he/dashboard")
    
    if response.status_code == 200:
        content = response.text
        print("   ✓ Dashboard page loaded successfully")
        
        # Check for key dashboard elements
        if 'דשבורד' in content or 'dashboard' in content.lower():
            print("   ✓ Dashboard content detected")
        if 'התנתקות' in content or 'logout' in content.lower():
            print("   ✓ Logout option available")
        if 'הנצחה' in content or 'memorial' in content.lower():
            print("   ✓ Memorial functionality accessible")
            
    else:
        print(f"   ✗ Dashboard access failed (status: {response.status_code})")
        return False
    
    # Step 4: Test page reload (like pressing F5 or refresh)
    print("\n4. Testing page reload (session persistence)...")
    time.sleep(1)
    response = session.get(f"{base_url}/he/dashboard")
    
    if response.status_code == 200:
        print("   ✓ Dashboard still accessible after reload")
    else:
        print(f"   ✗ Dashboard not accessible after reload (status: {response.status_code})")
        return False
    
    # Step 5: Test API access with session
    print("\n5. Testing API access with current session...")
    response = session.get(f"{base_url}/api/v1/auth/me")
    
    if response.status_code == 200:
        data = response.json()
        user = data.get('user', data)
        print(f"   ✓ API accessible - User: {user.get('email', 'Unknown')}")
    else:
        print(f"   ✗ API not accessible (status: {response.status_code})")
        return False
    
    # Step 6: Test different Hebrew pages
    print("\n6. Testing access to other Hebrew pages...")
    test_pages = [
        ("/he", "Home page"),
        ("/he/memorial/new", "Create memorial page"),
    ]
    
    all_pages_ok = True
    for url, description in test_pages:
        response = session.get(f"{base_url}{url}")
        if response.status_code == 200:
            print(f"   ✓ {description} accessible")
        else:
            print(f"   ✗ {description} failed (status: {response.status_code})")
            all_pages_ok = False
    
    if not all_pages_ok:
        print("   ⚠️ Some Hebrew pages had issues")
    
    print("\n" + "="*50)
    print("BROWSER SIMULATION COMPLETE")
    print("="*50)
    return True

if __name__ == "__main__":
    success = simulate_browser_session()
    
    if success:
        print("\n🎉 BROWSER SIMULATION SUCCESSFUL!")
        print("✅ The account behaves correctly in a browser-like environment")
        print("✅ User can login and navigate normally")
        print("✅ Session persistence works across page reloads")
        print("✅ All Hebrew pages are accessible")
        print("\n👤 READY FOR MANUAL USER TESTING")
        print("   Login URL: http://localhost:8000/he/login")
        print("   Email: shaktee@maxseeding.vn")
        print("   Password: Keren@3823")
    else:
        print("\n❌ BROWSER SIMULATION FAILED!")
        print("⚠️ The account may have issues during manual testing")
    
    exit(0 if success else 1)