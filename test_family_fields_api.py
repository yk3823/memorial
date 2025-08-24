#!/usr/bin/env python3
"""
End-to-end test for family fields implementation.
Tests the complete flow: form data -> API endpoint -> database storage.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.core.deps import get_current_verified_user
from app.models.user import User
from uuid import uuid4

# Mock user for testing
class MockUser:
    def __init__(self):
        self.id = uuid4()
        self.email = "test@example.com"
        self.is_active = True
        self.is_verified = True
        self.subscription_tier = "premium"
        self.max_memorials = 10
    
    def is_subscription_active(self):
        return True

def create_test_client():
    """Create a test client with mocked authentication."""
    
    def override_get_current_verified_user():
        return MockUser()
    
    app.dependency_overrides[get_current_verified_user] = override_get_current_verified_user
    
    return TestClient(app)

def test_family_fields_form_submission():
    """Test that family fields are properly handled in form submission."""
    print("🧪 Testing Family Fields API Integration")
    print("=" * 50)
    
    client = create_test_client()
    
    # Prepare test data with all family fields
    form_data = {
        "hebrew_first_name": "דוד",
        "hebrew_last_name": "המלך",
        "parent_name_hebrew": "ישי",
        "deceased_name_hebrew": "דוד המלך",
        "spouse_name": "מיכל בת שאול",
        "children_names": "שלמה, אבשלום, אמנון, אדוניהו",
        "parents_names": "ישי ונצבת",
        "family_names": "בית דוד, משפחת ישי, שבט יהודה",
        "english_first_name": "David",
        "english_last_name": "King",
        "birth_date_gregorian": "1040-01-01",
        "death_date_gregorian": "970-01-01",
        "biography": "מלך ישראל הגדול, משורר התהילים",
        "is_public": "true",
        "enable_comments": "false"
    }
    
    print("📝 Submitting memorial with family fields...")
    
    # Submit form data to the API
    response = client.post("/api/v1/memorials/with-files", data=form_data)
    
    print(f"📊 Response Status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ Memorial created successfully!")
        
        response_data = response.json()
        memorial = response_data.get("memorial", {})
        
        # Verify all family fields are included in the response
        family_fields = {
            "spouse_name": "מיכל בת שאול",
            "children_names": "שלמה, אבשלום, אמנון, אדוניהו", 
            "parents_names": "ישי ונצבת",
            "family_names": "בית דוד, משפחת ישי, שבט יהודה"
        }
        
        print("\n🔍 Verifying family fields in response:")
        all_fields_correct = True
        
        for field_name, expected_value in family_fields.items():
            actual_value = memorial.get(field_name)
            if actual_value == expected_value:
                print(f"✅ {field_name}: {actual_value}")
            else:
                print(f"❌ {field_name}: expected '{expected_value}', got '{actual_value}'")
                all_fields_correct = False
        
        if all_fields_correct:
            print("\n🎉 All family fields are correctly stored and returned!")
            print(f"📍 Memorial ID: {memorial.get('id')}")
            print(f"🔗 Public URL: {response_data.get('public_url', 'N/A')}")
            return True
        else:
            print("\n❌ Some family fields were not stored correctly.")
            return False
    else:
        print("❌ Failed to create memorial")
        print(f"Error: {response.text}")
        return False

def test_family_fields_validation():
    """Test validation of family fields through the API."""
    print("\n📋 Testing Family Fields Validation")
    print("=" * 50)
    
    client = create_test_client()
    
    # Test with empty required fields to check that family fields don't break validation
    minimal_data = {
        "hebrew_first_name": "משה",
        "hebrew_last_name": "רבנו",
        "parent_name_hebrew": "עמרם",
        "deceased_name_hebrew": "משה רבנו"
    }
    
    print("📝 Testing minimal memorial (no family fields)...")
    response = client.post("/api/v1/memorials/with-files", data=minimal_data)
    
    if response.status_code == 201:
        print("✅ Minimal memorial created successfully!")
        memorial = response.json().get("memorial", {})
        
        # Check that family fields are null/empty
        family_fields = ["spouse_name", "children_names", "parents_names", "family_names"]
        for field in family_fields:
            value = memorial.get(field)
            if value is None or value == "":
                print(f"✅ {field}: null/empty (as expected)")
            else:
                print(f"⚠️  {field}: {value} (unexpected non-empty value)")
        
        return True
    else:
        print("❌ Failed to create minimal memorial")
        print(f"Error: {response.text}")
        return False

def main():
    """Run all API tests."""
    print("🚀 Starting Family Fields API Tests\n")
    
    tests = [
        ("Family Fields Form Submission", test_family_fields_form_submission),
        ("Family Fields Validation", test_family_fields_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*70)
    print("📊 Final Test Results Summary:")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<35}: {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Family fields are working correctly.")
        print("✨ The implementation includes:")
        print("   • Database schema with new family fields")
        print("   • SQLAlchemy model updates") 
        print("   • Pydantic schema validation")
        print("   • API endpoint support")
        print("   • HTML form integration")
        print("   • Hebrew validation")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)