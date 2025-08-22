#!/usr/bin/env python3
"""
Focused test to verify dashboard access issue from the comprehensive test.
"""

import requests
import json
import time

def test_dashboard_access():
    session = requests.Session()
    base_url = "http://localhost:8000"
    test_email = "shaktee@maxseeding.vn"
    test_password = "Keren@3823"
    
    print("Testing Dashboard Access After Login\n")
    
    # Step 1: Login via API
    print("1. Logging in via API...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    response = session.post(
        f"{base_url}/api/v1/auth/login",
        json=login_data,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
    )
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token')
        print(f"✓ Login successful. Access token length: {len(access_token)} chars")
    else:
        print(f"✗ Login failed with status {response.status_code}")
        return False
    
    # Step 2: Access dashboard with token
    print("\n2. Accessing Hebrew dashboard with Bearer token...")
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = session.get(f"{base_url}/he/dashboard", headers=headers)
    
    print(f"Status code: {response.status_code}")
    print(f"Response size: {len(response.text)} chars")
    
    if response.status_code == 200:
        content = response.text
        
        # Check for specific dashboard indicators
        dashboard_indicators = {
            'Hebrew title': 'לוח בקרה' in content or 'דשבורד' in content,
            'Dashboard class': 'dashboard' in content.lower(),
            'Protected content': 'ההנצחות שלי' in content or 'my memorials' in content.lower(),
            'User menu': 'התנתקות' in content or 'logout' in content.lower(),
            'Create memorial': 'צור הנצחה' in content or 'create memorial' in content.lower(),
        }
        
        print("\nDashboard indicators found:")
        for indicator, found in dashboard_indicators.items():
            status = "✓" if found else "✗"
            print(f"  {status} {indicator}: {found}")
        
        # Check if this looks like a login form (bad)
        login_form_indicators = {
            'Email input': 'type="email"' in content,
            'Password input': 'type="password"' in content,
            'Login form': '<form' in content and ('login' in content.lower() or 'כניסה' in content),
            'Login button': 'התחבר' in content or 'login' in content.lower(),
        }
        
        print("\nLogin form indicators (should be False):")
        for indicator, found in login_form_indicators.items():
            status = "✗" if found else "✓"
            print(f"  {status} {indicator}: {found}")
        
        # Determine if we actually got the dashboard
        dashboard_score = sum(dashboard_indicators.values())
        login_score = sum(login_form_indicators.values())
        
        print(f"\nScore: Dashboard indicators: {dashboard_score}/5, Login indicators: {login_score}/4")
        
        if dashboard_score >= 2 and login_score <= 1:
            print("✓ Successfully accessed Hebrew dashboard!")
            return True
        elif login_score >= 2:
            print("✗ Got login form instead of dashboard")
            return False
        else:
            print("? Dashboard access unclear - mixed indicators")
            
            # Print a snippet of the content for manual review
            print("\nContent snippet (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            return False
    else:
        print(f"✗ Dashboard access failed with status {response.status_code}")
        return False
    
    # Step 3: Also test without Bearer token (using cookies only)
    print("\n3. Accessing Hebrew dashboard with cookies only...")
    response = session.get(f"{base_url}/he/dashboard")
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Dashboard accessible with cookies")
        return True
    else:
        print(f"✗ Dashboard not accessible with cookies (status {response.status_code})")
        return False

if __name__ == "__main__":
    success = test_dashboard_access()
    print(f"\nFinal result: {'SUCCESS' if success else 'FAILURE'}")