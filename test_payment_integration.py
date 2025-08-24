#!/usr/bin/env python3
"""
Comprehensive Payment Integration Test Script
Tests PayPal integration, payment flow, and subscription management
"""

import asyncio
import json
import requests
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/v1"

class PaymentIntegrationTester:
    """Comprehensive PayPal payment integration tester."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/v1"
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.test_user_email = f"test_payment_{uuid.uuid4().hex[:8]}@test.com"
        self.test_user_password = "TestPassword123!"
        self.test_payment_id: Optional[str] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with proper headers."""
        headers = kwargs.pop('headers', {})
        
        # Add authorization header if token is available
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        # Add content-type for JSON requests
        if method.upper() in ['POST', 'PUT', 'PATCH'] and 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
        
        url = f"{self.api_base}{endpoint}"
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            
            # Log request details
            self.log(f"{method.upper()} {url} -> {response.status_code}")
            
            # Try to parse JSON response
            try:
                return {
                    'status_code': response.status_code,
                    'data': response.json(),
                    'headers': dict(response.headers)
                }
            except json.JSONDecodeError:
                return {
                    'status_code': response.status_code,
                    'data': response.text,
                    'headers': dict(response.headers)
                }
                
        except Exception as e:
            self.log(f"Request error: {e}", "ERROR")
            return {
                'status_code': 0,
                'data': {'error': str(e)},
                'headers': {}
            }
    
    def test_api_health(self) -> bool:
        """Test API health and availability."""
        self.log("Testing API health...")
        
        try:
            response = self.make_request('GET', '/health')
            if response['status_code'] == 200:
                self.log("✓ API health check passed")
                return True
            else:
                self.log(f"✗ API health check failed: {response['status_code']}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ API health check error: {e}", "ERROR")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration."""
        self.log("Testing user registration...")
        
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "confirm_password": self.test_user_password,
            "first_name": "Test",
            "last_name": "Payment",
            "hebrew_name": "בדיקה תשלום"
        }
        
        response = self.make_request('POST', '/auth/register', json=user_data)
        
        if response['status_code'] == 201 and response['data'].get('success'):
            self.log("✓ User registration successful")
            return True
        else:
            self.log(f"✗ User registration failed: {response['data']}", "ERROR")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login and token retrieval."""
        self.log("Testing user login...")
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = self.make_request('POST', '/auth/login', json=login_data)
        
        if response['status_code'] == 200 and response['data'].get('success'):
            self.access_token = response['data'].get('access_token')
            self.log("✓ User login successful")
            self.log(f"  Access token: {self.access_token[:20]}..." if self.access_token else "  No token received")
            return True
        else:
            self.log(f"✗ User login failed: {response['data']}", "ERROR")
            return False
    
    def test_payment_info_endpoints(self) -> bool:
        """Test payment information endpoints."""
        self.log("Testing payment info endpoints...")
        
        # Test amount info
        response = self.make_request('GET', '/payment/info/amount')
        if response['status_code'] != 200:
            self.log(f"✗ Payment amount info failed: {response['status_code']}", "ERROR")
            return False
        
        amount_info = response['data']
        if amount_info.get('standard_amount') != 100.0:
            self.log("✗ Incorrect standard amount", "ERROR")
            return False
        
        # Test methods info
        response = self.make_request('GET', '/payment/info/methods')
        if response['status_code'] != 200:
            self.log(f"✗ Payment methods info failed: {response['status_code']}", "ERROR")
            return False
        
        methods_info = response['data']
        if not methods_info.get('paypal_enabled'):
            self.log("✗ PayPal not enabled", "ERROR")
            return False
        
        self.log("✓ Payment info endpoints working")
        return True
    
    def test_payment_creation_paypal(self) -> bool:
        """Test PayPal payment creation."""
        self.log("Testing PayPal payment creation...")
        
        payment_data = {
            "amount": 100.00,
            "currency": "ILS",
            "description": "Test Memorial Website Subscription",
            "success_url": f"{self.base_url}/payment/success",
            "cancel_url": f"{self.base_url}/payment/cancel"
        }
        
        response = self.make_request('POST', '/payment/create', json=payment_data)
        
        if response['status_code'] == 201 and response['data'].get('success'):
            payment_info = response['data'].get('payment', {})
            self.test_payment_id = payment_info.get('id')
            approval_url = response['data'].get('approval_url')
            
            self.log("✓ PayPal payment creation successful")
            self.log(f"  Payment ID: {self.test_payment_id}")
            self.log(f"  Approval URL: {approval_url[:50]}..." if approval_url else "  No approval URL")
            self.log(f"  Amount: {payment_info.get('formatted_amount', 'N/A')}")
            
            return True
        else:
            self.log(f"✗ PayPal payment creation failed: {response['data']}", "ERROR")
            return False
    
    def test_payment_creation_coupon(self) -> bool:
        """Test coupon payment creation."""
        self.log("Testing coupon payment creation...")
        
        payment_data = {
            "amount": 100.00,
            "currency": "ILS",
            "description": "Test Memorial Website Subscription - Coupon",
            "coupon_code": "TEST2024"
        }
        
        response = self.make_request('POST', '/payment/create', json=payment_data)
        
        if response['status_code'] == 201 and response['data'].get('success'):
            payment_info = response['data'].get('payment', {})
            self.log("✓ Coupon payment creation successful")
            self.log(f"  Payment ID: {payment_info.get('id')}")
            self.log(f"  Coupon Code: {payment_info.get('coupon_code', 'N/A')}")
            self.log(f"  Requires Approval: {response['data'].get('requires_approval', True)}")
            
            return True
        else:
            self.log(f"✗ Coupon payment creation failed: {response['data']}", "ERROR")
            return False
    
    def test_payment_status_check(self) -> bool:
        """Test payment status retrieval."""
        self.log("Testing payment status check...")
        
        if not self.test_payment_id:
            self.log("✗ No test payment ID available", "ERROR")
            return False
        
        response = self.make_request('GET', f'/payment/status/{self.test_payment_id}')
        
        if response['status_code'] == 200 and response['data'].get('success'):
            payment_info = response['data'].get('payment', {})
            self.log("✓ Payment status check successful")
            self.log(f"  Status: {payment_info.get('display_status', 'N/A')}")
            self.log(f"  Method: {payment_info.get('payment_method', 'N/A')}")
            
            return True
        else:
            self.log(f"✗ Payment status check failed: {response['data']}", "ERROR")
            return False
    
    def test_payment_history(self) -> bool:
        """Test payment history retrieval."""
        self.log("Testing payment history...")
        
        response = self.make_request('GET', '/payment/history')
        
        if response['status_code'] == 200 and response['data'].get('success'):
            payments = response['data'].get('payments', [])
            total_count = response['data'].get('total_count', 0)
            
            self.log("✓ Payment history retrieval successful")
            self.log(f"  Total payments: {total_count}")
            self.log(f"  Retrieved: {len(payments)} payments")
            
            return True
        else:
            self.log(f"✗ Payment history failed: {response['data']}", "ERROR")
            return False
    
    def test_payment_summary(self) -> bool:
        """Test payment summary retrieval."""
        self.log("Testing payment summary...")
        
        response = self.make_request('GET', '/payment/summary')
        
        if response['status_code'] == 200 and response['data'].get('success'):
            summary = response['data']
            self.log("✓ Payment summary retrieval successful")
            self.log(f"  Total payments: {summary.get('total_payments', 0)}")
            self.log(f"  Completed payments: {summary.get('completed_payments', 0)}")
            self.log(f"  Total amount paid: {summary.get('total_amount_paid', 0)}")
            self.log(f"  Has active subscription: {summary.get('has_active_subscription', False)}")
            
            return True
        else:
            self.log(f"✗ Payment summary failed: {response['data']}", "ERROR")
            return False
    
    def test_payment_cancellation(self) -> bool:
        """Test payment cancellation."""
        self.log("Testing payment cancellation...")
        
        if not self.test_payment_id:
            self.log("✗ No test payment ID available", "ERROR")
            return False
        
        cancel_data = {
            "payment_id": self.test_payment_id,
            "reason": "Test cancellation"
        }
        
        response = self.make_request('POST', '/payment/cancel', json=cancel_data)
        
        if response['status_code'] == 200 and response['data'].get('success'):
            payment_info = response['data'].get('payment', {})
            self.log("✓ Payment cancellation successful")
            self.log(f"  Final status: {payment_info.get('display_status', 'N/A')}")
            
            return True
        else:
            self.log(f"✗ Payment cancellation failed: {response['data']}", "ERROR")
            return False
    
    def test_web_routes(self) -> bool:
        """Test payment web routes availability."""
        self.log("Testing payment web routes...")
        
        routes_to_test = [
            ("/payment", "Payment form page"),
            ("/payment/success", "Payment success page"),
            ("/payment/cancel", "Payment cancel page"),
            ("/payment/history", "Payment history page"),
        ]
        
        for route, description in routes_to_test:
            try:
                response = requests.get(f"{self.base_url}{route}", allow_redirects=False, timeout=5)
                if response.status_code in [200, 302]:  # 302 for redirect is OK
                    self.log(f"✓ {description} available ({response.status_code})")
                else:
                    self.log(f"✗ {description} not available ({response.status_code})", "ERROR")
                    return False
            except Exception as e:
                self.log(f"✗ {description} error: {e}", "ERROR")
                return False
        
        return True
    
    def test_authentication_requirements(self) -> bool:
        """Test authentication requirements for payment endpoints."""
        self.log("Testing authentication requirements...")
        
        # Temporarily remove access token
        original_token = self.access_token
        self.access_token = None
        
        # Test endpoints that should require authentication
        protected_endpoints = [
            ('POST', '/payment/create'),
            ('GET', '/payment/history'),
            ('GET', '/payment/summary'),
        ]
        
        for method, endpoint in protected_endpoints:
            response = self.make_request(method, endpoint, json={})
            if response['status_code'] not in [401, 403]:
                self.log(f"✗ {endpoint} should require authentication", "ERROR")
                self.access_token = original_token
                return False
        
        # Restore access token
        self.access_token = original_token
        self.log("✓ Authentication requirements properly enforced")
        return True
    
    async def run_comprehensive_test(self) -> bool:
        """Run comprehensive payment integration test."""
        self.log("=" * 60)
        self.log("STARTING COMPREHENSIVE PAYMENT INTEGRATION TEST")
        self.log("=" * 60)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Payment Info Endpoints", self.test_payment_info_endpoints),
            ("Authentication Requirements", self.test_authentication_requirements),
            ("PayPal Payment Creation", self.test_payment_creation_paypal),
            ("Payment Status Check", self.test_payment_status_check),
            ("Coupon Payment Creation", self.test_payment_creation_coupon),
            ("Payment History", self.test_payment_history),
            ("Payment Summary", self.test_payment_summary),
            ("Payment Cancellation", self.test_payment_cancellation),
            ("Web Routes Availability", self.test_web_routes),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- Running: {test_name} ---")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"✗ {test_name} crashed: {e}", "ERROR")
                failed += 1
        
        self.log("\n" + "=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        self.log(f"Total tests: {passed + failed}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log(f"Success rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Payment integration is working correctly.")
        else:
            self.log("❌ SOME TESTS FAILED. Please check the logs above.")
        
        return failed == 0


def main():
    """Main test runner."""
    print("PayPal Payment Integration Test Suite")
    print("====================================")
    
    # Instructions
    print("\n📋 SETUP INSTRUCTIONS:")
    print("1. Ensure the Memorial Website server is running on http://localhost:8000")
    print("2. Database should be migrated with the Payment model")
    print("3. PayPal sandbox credentials should be configured")
    print("4. Press Enter when ready to start testing...")
    input()
    
    # Run tests
    tester = PaymentIntegrationTester()
    
    try:
        # Use asyncio to run the comprehensive test
        success = asyncio.run(tester.run_comprehensive_test())
        
        if success:
            print("\n✅ Payment integration test completed successfully!")
            print("You can now:")
            print("- Create payments via API")
            print("- Process PayPal payments")
            print("- Handle coupon payments")
            print("- View payment history")
            print("- Manage user subscriptions")
        else:
            print("\n❌ Payment integration test failed!")
            print("Please check the error messages above and fix any issues.")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)