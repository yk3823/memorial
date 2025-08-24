#!/usr/bin/env python3
"""
Test script to verify dashboard metrics are showing correct values.
"""

import requests
import json
import sys

def test_dashboard_metrics():
    """Test the dashboard metrics API endpoint"""
    base_url = "http://localhost:8000"
    test_email = "shaktee@maxseeding.vn"
    test_password = "Keren@3823"
    
    session = requests.Session()
    
    print("Testing Dashboard Metrics Fix\n")
    
    # Step 1: Login
    print("1. Logging in...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = session.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            print(f"✓ Login successful")
        else:
            print(f"✗ Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Login request failed: {e}")
        return False
    
    # Step 2: Test dashboard stats API
    print("\n2. Testing dashboard stats API...")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        response = session.get(f"{base_url}/api/v1/dashboard/stats", headers=headers)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have the expected structure
            print("\n✓ Dashboard stats API accessible")
            print("Response structure:")
            print(f"  Status: {data.get('status', 'missing')}")
            
            # Check main metrics (what the frontend expects)
            main_metrics = {
                'total_memorials': data.get('total_memorials'),
                'public_memorials': data.get('public_memorials'), 
                'total_views': data.get('total_views'),
                'total_verses': data.get('total_verses')
            }
            
            print("\nMain metrics (expected by frontend):")
            for metric, value in main_metrics.items():
                if value is not None:
                    print(f"  ✓ {metric}: {value}")
                else:
                    print(f"  ✗ {metric}: missing")
            
            # Check if we have detailed data structure too
            detailed_data = data.get('data', {})
            if detailed_data:
                print(f"\n✓ Detailed data structure also present with {len(detailed_data)} entries")
                
                # Show some detailed info
                for key in ['total_memorials', 'public_memorials', 'total_views', 'total_verses']:
                    detail = detailed_data.get(key, {})
                    if detail and isinstance(detail, dict):
                        label = detail.get('label', 'No label')
                        description = detail.get('description', 'No description')
                        print(f"  {key}: {label} - {description}")
            
            # Check if all main metrics are numbers (not None)
            all_present = all(v is not None for v in main_metrics.values())
            all_numbers = all(isinstance(v, (int, float)) for v in main_metrics.values() if v is not None)
            
            if all_present and all_numbers:
                print("\n🎉 SUCCESS: All metrics are present and numeric!")
                
                # Show the actual values
                print("\nMetric Summary:")
                print(f"  סה״כ הנצחות (Total Memorials): {main_metrics['total_memorials']}")
                print(f"  הנצחות ציבוריות (Public Memorials): {main_metrics['public_memorials']}")
                print(f"  סה״כ צפיות (Total Views): {main_metrics['total_views']}")
                print(f"  פסוקי תהילים (Psalms Verses): {main_metrics['total_verses']}")
                
                # Explain what "פסוקי תהילים" means
                print(f"\nExplanation of 'פסוקי תהילים' (Psalms Verses):")
                print(f"This metric counts the unique Psalm 119 verses that have been")
                print(f"automatically associated with your memorials based on the Hebrew")
                print(f"letters in the deceased person's names. Each Hebrew letter")
                print(f"corresponds to a section of Psalm 119 with 8 verses.")
                
                return True
            else:
                print(f"\n✗ ISSUE: Some metrics missing or invalid")
                missing = [k for k, v in main_metrics.items() if v is None]
                if missing:
                    print(f"Missing metrics: {missing}")
                return False
                
        else:
            print(f"✗ Dashboard stats API failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Dashboard stats request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_metrics()
    print(f"\nFinal result: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)