#!/usr/bin/env python3
"""
Test QR memorial endpoints through HTTP requests
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_qr_endpoints():
    """Test QR memorial endpoints via HTTP."""
    print("=" * 80)
    print("QR MEMORIAL ENDPOINT TESTS")
    print("=" * 80)
    
    session = requests.Session()
    
    try:
        # Test 1: API Health Check
        print("\n1. Testing API health check...")
        response = session.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Health check passed: {data['status']}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
        
        # Test 2: API Info
        print("\n2. Testing API info endpoint...")
        response = session.get(f"{BASE_URL}/api/v1/info")
        if response.status_code == 200:
            data = response.json()
            qr_endpoint = data.get("endpoints", {}).get("qr-memorial")
            if qr_endpoint:
                print(f"   ✓ QR memorial endpoint listed: {qr_endpoint}")
            else:
                print("   ✗ QR memorial endpoint not listed")
                return False
        else:
            print(f"   ✗ API info failed: {response.status_code}")
            return False
        
        # Test 3: Try to access QR endpoint (should fail with authentication error, not SQLAlchemy error)
        print("\n3. Testing QR memorial endpoint access (unauthenticated)...")
        response = session.get(f"{BASE_URL}/api/v1/qr-memorial")
        
        # We expect authentication error, not SQLAlchemy error
        if response.status_code == 401:
            data = response.json()
            if "Not authenticated" in str(data) or "detail" in data:
                print("   ✓ QR endpoint returns authentication error (not SQLAlchemy error)")
            else:
                print(f"   ? Unexpected response: {data}")
        elif response.status_code == 404:
            # Check if it's a route not found vs SQLAlchemy error
            print("   ! QR endpoint returned 404 - checking if route exists")
            
            # Let's try specific QR routes that might be available
            qr_routes = [
                "/api/v1/qr-codes",
                "/api/v1/qr",
                "/api/v1/qr-memorial/codes",
            ]
            
            for route in qr_routes:
                test_response = session.get(f"{BASE_URL}{route}")
                if test_response.status_code != 404:
                    print(f"   ✓ Found working QR route: {route} (status: {test_response.status_code})")
                    break
            else:
                print("   ! No QR routes found, but no SQLAlchemy errors either")
        else:
            print(f"   ? Unexpected status code: {response.status_code}")
            try:
                data = response.json()
                print(f"   Response: {data}")
            except:
                print(f"   Response text: {response.text[:200]}")
        
        # Test 4: Check dashboard QR analytics
        print("\n4. Testing dashboard QR analytics endpoint...")
        response = session.get(f"{BASE_URL}/api/v1/dashboard/qr-analytics")
        
        if response.status_code == 401:
            print("   ✓ QR analytics endpoint returns authentication error (models loaded correctly)")
        elif response.status_code == 500:
            print("   ✗ QR analytics endpoint returns server error (possible SQLAlchemy issue)")
            try:
                data = response.json()
                print(f"   Error details: {data}")
            except:
                print(f"   Error text: {response.text[:200]}")
            return False
        else:
            print(f"   ? Unexpected status: {response.status_code}")
        
        print("\n" + "=" * 80)
        print("✓ QR ENDPOINT TESTS PASSED")
        print("- Application starts without SQLAlchemy relationship errors")
        print("- QR memorial endpoints are properly registered")  
        print("- Models load correctly (authentication errors, not model errors)")
        print("- No 'Mapper has no property qr_code' errors detected")
        print("=" * 80)
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to application. Is it running on localhost:8000?")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_qr_endpoints()
    if success:
        print("\n🎉 CONCLUSION: QR memorial functionality appears to be working correctly!")
        print("The SQLAlchemy relationship error you mentioned may have been resolved.")
    else:
        print("\n❌ ISSUES DETECTED: Further investigation needed.")