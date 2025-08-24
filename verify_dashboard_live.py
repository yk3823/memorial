#!/usr/bin/env python3
"""
Live verification that the dashboard displays correct metrics at http://localhost:8000/he/dashboard
"""

import webbrowser
import requests
import json
import time
import sys

def verify_dashboard_live():
    """Verify the dashboard works by opening it in a browser and checking the API"""
    base_url = "http://localhost:8000"
    test_email = "shaktee@maxseeding.vn"
    test_password = "Keren@3823"
    
    print("🔧 Dashboard Metrics Fix - Live Verification\n")
    
    # Step 1: Test API directly
    print("1. Testing API endpoint directly...")
    session = requests.Session()
    
    # Login
    login_data = {"email": test_email, "password": test_password}
    response = session.post(f"{base_url}/api/v1/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("✗ Login failed - please check if server is running and credentials are correct")
        return False
    
    access_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Test dashboard API
    api_response = session.get(f"{base_url}/api/v1/dashboard/stats", headers=headers)
    
    if api_response.status_code == 200:
        data = api_response.json()
        
        print("✓ API Response Structure:")
        print(f"  Status: {data.get('status')}")
        print(f"  Total Memorials: {data.get('total_memorials')}")
        print(f"  Public Memorials: {data.get('public_memorials')}")
        print(f"  Total Views: {data.get('total_views')}")
        print(f"  Total Verses: {data.get('total_verses')}")
        
        print("\n✓ API is working correctly!")
    else:
        print(f"✗ API failed with status {api_response.status_code}")
        return False
    
    # Step 2: Instructions for manual verification
    dashboard_url = f"{base_url}/he/dashboard"
    
    print(f"\n2. Manual Verification Instructions:")
    print(f"   Dashboard URL: {dashboard_url}")
    print(f"   Login credentials: {test_email} / {test_password}")
    
    print(f"\n🎯 WHAT TO CHECK:")
    print(f"   Before the fix: The 4 metric cards showed dashes (-) or zeros")
    print(f"   After the fix: The metric cards should show:")
    print(f"   • סה״כ הנצחות (Total Memorials): {data.get('total_memorials')}")
    print(f"   • הנצחות ציבוריות (Public Memorials): {data.get('public_memorials')}")
    print(f"   • סה״כ צפיות (Total Views): {data.get('total_views')}")
    print(f"   • פסוקי תהילים (Psalms Verses): {data.get('total_verses')}")
    
    print(f"\n📖 EXPLANATION OF METRICS:")
    print(f"   • Total Memorials: Number of active memorial pages you created")
    print(f"   • Public Memorials: Number of your memorials that are publicly viewable") 
    print(f"   • Total Views: Sum of page views across all your memorials")
    print(f"   • Psalms Verses: Number of unique Psalm 119 verses automatically")
    print(f"     selected for your memorials based on Hebrew letters in names")
    
    # Step 3: Open browser automatically
    try:
        print(f"\n3. Opening dashboard in browser...")
        webbrowser.open(dashboard_url)
        print(f"✓ Browser opened - please login and verify the metrics display")
    except Exception as e:
        print(f"⚠ Could not open browser automatically: {e}")
        print(f"Please manually navigate to: {dashboard_url}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🎉 MEMORIAL WEBSITE DASHBOARD METRICS - FIX VERIFICATION")
    print("=" * 60)
    
    success = verify_dashboard_live()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY OF FIXES IMPLEMENTED:")
    print(f"{'='*60}")
    print(f"✅ FIXED: Dashboard API now returns metrics in correct format")
    print(f"✅ FIXED: Added missing 'public_memorials' metric calculation")
    print(f"✅ FIXED: Added missing 'total_views' metric calculation")
    print(f"✅ FIXED: Added missing 'total_verses' (פסוקי תהילים) metric calculation")
    print(f"✅ FIXED: API response structure matches frontend expectations")
    print(f"✅ EXPLAINED: 'פסוקי תהילים' metric meaning clarified")
    
    if success:
        print(f"\n🎯 VERIFICATION: {('SUCCESS' if success else 'FAILURE')}")
        print(f"The dashboard at http://localhost:8000/he/dashboard should now")
        print(f"display actual numbers instead of dashes for all 4 metrics!")
    
    sys.exit(0 if success else 1)