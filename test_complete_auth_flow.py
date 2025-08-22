#!/usr/bin/env python3
"""
Complete Authentication Flow Test
Tests registration → verification → login flow with exact credentials.

Email: shaktee@maxseeding.vn
Password: Keren@3823
Hebrew names: אביגיל בת רבקה (Avigail bat Rivka)
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, Any

import aiohttp
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "shaktee@maxseeding.vn",
    "password": "Keren@3823",
    "confirm_password": "Keren@3823",
    "first_name": "אביגיל",  # Avigail
    "last_name": "בת רבקה",  # bat Rivka  
    "hebrew_name": "אביגיל בת רבקה",
    "phone_number": "+972-50-123-4567"
}

# Database configuration
DATABASE_URL = "postgresql+asyncpg://memorial_user:memorial_pass_123@localhost/memorial_db"


class AuthFlowTester:
    """Complete authentication flow tester."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.engine = None
        self.tokens = {}
        self.cookies = {}
        self.test_results = {
            "registration": {"success": False, "details": {}},
            "email_verification": {"success": False, "details": {}},
            "login": {"success": False, "details": {}},
            "protected_routes": {"success": False, "details": {}},
            "cookie_persistence": {"success": False, "details": {}}
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Memorial-Auth-Tester/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
        
        # Initialize database connection
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        if self.engine:
            await self.engine.dispose()
    
    async def cleanup_existing_user(self):
        """Remove existing test user if present."""
        logger.info("Cleaning up existing test user...")
        
        try:
            async with self.engine.begin() as conn:
                # Delete user and related data
                await conn.execute(
                    text("DELETE FROM users WHERE email = :email"),
                    {"email": TEST_USER["email"]}
                )
                logger.info(f"Cleaned up existing user: {TEST_USER['email']}")
        except Exception as e:
            logger.warning(f"Error during cleanup (user might not exist): {e}")
    
    async def test_registration(self) -> bool:
        """Test user registration."""
        logger.info("=== Testing User Registration ===")
        
        try:
            # Clean up first
            await self.cleanup_existing_user()
            
            # Register new user
            async with self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=TEST_USER
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Registration response status: {response.status}")
                logger.info(f"Registration response body: {response_text}")
                
                if response.status == 201:
                    response_data = json.loads(response_text)
                    self.test_results["registration"] = {
                        "success": True,
                        "details": {
                            "status_code": response.status,
                            "response": response_data,
                            "user_id": response_data.get("user_id"),
                            "verification_required": response_data.get("verification_required", True)
                        }
                    }
                    logger.info("✅ Registration successful!")
                    return True
                else:
                    self.test_results["registration"] = {
                        "success": False,
                        "details": {
                            "status_code": response.status,
                            "error": response_text
                        }
                    }
                    logger.error(f"❌ Registration failed: {response_text}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            self.test_results["registration"] = {
                "success": False,
                "details": {"error": str(e)}
            }
            return False
    
    async def get_verification_token_from_db(self) -> Optional[str]:
        """Get verification token directly from database."""
        logger.info("Fetching verification token from database...")
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT verification_token FROM users WHERE email = :email"),
                    {"email": TEST_USER["email"]}
                )
                row = result.fetchone()
                
                if row and row.verification_token:
                    logger.info("✅ Found verification token in database")
                    return row.verification_token
                else:
                    logger.error("❌ No verification token found")
                    return None
        
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            return None
    
    async def test_email_verification(self) -> bool:
        """Test email verification process."""
        logger.info("=== Testing Email Verification ===")
        
        try:
            # Get verification token from database
            verification_token = await self.get_verification_token_from_db()
            
            if not verification_token:
                self.test_results["email_verification"] = {
                    "success": False,
                    "details": {"error": "No verification token found"}
                }
                return False
            
            # Verify email using the token
            async with self.session.get(
                f"{BASE_URL}/api/v1/auth/verify-email?token={verification_token}"
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Email verification response status: {response.status}")
                logger.info(f"Email verification response: {response_text}")
                
                if response.status == 200:
                    response_data = json.loads(response_text)
                    self.test_results["email_verification"] = {
                        "success": True,
                        "details": {
                            "status_code": response.status,
                            "response": response_data,
                            "token_used": verification_token
                        }
                    }
                    logger.info("✅ Email verification successful!")
                    return True
                else:
                    self.test_results["email_verification"] = {
                        "success": False,
                        "details": {
                            "status_code": response.status,
                            "error": response_text,
                            "token_used": verification_token
                        }
                    }
                    logger.error(f"❌ Email verification failed: {response_text}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Email verification error: {e}")
            self.test_results["email_verification"] = {
                "success": False,
                "details": {"error": str(e)}
            }
            return False
    
    async def test_login(self) -> bool:
        """Test user login via API."""
        logger.info("=== Testing Login ===")
        
        try:
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "remember_me": True
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Login response status: {response.status}")
                logger.info(f"Login response body: {response_text}")
                
                # Capture cookies
                if response.cookies:
                    for cookie_name, cookie_obj in response.cookies.items():
                        self.cookies[cookie_name] = cookie_obj.value
                        logger.info(f"Cookie captured: {cookie_name} = {cookie_obj.value}")
                
                if response.status == 200:
                    response_data = json.loads(response_text)
                    self.tokens = {
                        "access_token": response_data.get("access_token"),
                        "refresh_token": response_data.get("refresh_token")
                    }
                    
                    self.test_results["login"] = {
                        "success": True,
                        "details": {
                            "status_code": response.status,
                            "response": response_data,
                            "tokens": {
                                "access_token_present": bool(self.tokens["access_token"]),
                                "refresh_token_present": bool(self.tokens["refresh_token"])
                            },
                            "cookies": dict(self.cookies)
                        }
                    }
                    logger.info("✅ Login successful!")
                    return True
                else:
                    self.test_results["login"] = {
                        "success": False,
                        "details": {
                            "status_code": response.status,
                            "error": response_text
                        }
                    }
                    logger.error(f"❌ Login failed: {response_text}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            self.test_results["login"] = {
                "success": False,
                "details": {"error": str(e)}
            }
            return False
    
    async def test_hebrew_login_form(self) -> bool:
        """Test Hebrew login form access."""
        logger.info("=== Testing Hebrew Login Form ===")
        
        try:
            async with self.session.get(f"{BASE_URL}/he/login") as response:
                response_text = await response.text()
                logger.info(f"Hebrew login form status: {response.status}")
                
                if response.status == 200:
                    # Check if form contains expected Hebrew content
                    form_checks = {
                        "has_login_form": "form" in response_text.lower(),
                        "has_hebrew_content": any(ord(char) > 1500 for char in response_text),
                        "has_email_field": "email" in response_text.lower(),
                        "has_password_field": "password" in response_text.lower()
                    }
                    
                    logger.info("Hebrew form checks:", form_checks)
                    return all(form_checks.values())
                else:
                    logger.error(f"❌ Hebrew login form failed: {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Hebrew login form error: {e}")
            return False
    
    async def test_protected_routes(self) -> bool:
        """Test access to protected routes after login."""
        logger.info("=== Testing Protected Routes ===")
        
        if not self.tokens.get("access_token"):
            logger.error("❌ No access token available for protected route tests")
            return False
        
        try:
            # Test /api/v1/auth/me endpoint
            headers = {
                "Authorization": f"Bearer {self.tokens['access_token']}",
                "Accept": "application/json"
            }
            
            async with self.session.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=headers
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Protected route (/me) status: {response.status}")
                logger.info(f"Protected route response: {response_text}")
                
                if response.status == 200:
                    response_data = json.loads(response_text)
                    user_data = response_data.get("user", {})
                    
                    # Verify user data
                    verification_checks = {
                        "correct_email": user_data.get("email") == TEST_USER["email"],
                        "is_verified": user_data.get("is_verified") == True,
                        "is_active": user_data.get("is_active") == True,
                        "has_hebrew_name": bool(user_data.get("hebrew_name"))
                    }
                    
                    self.test_results["protected_routes"] = {
                        "success": all(verification_checks.values()),
                        "details": {
                            "status_code": response.status,
                            "user_data": user_data,
                            "verification_checks": verification_checks
                        }
                    }
                    
                    if all(verification_checks.values()):
                        logger.info("✅ Protected routes test successful!")
                        return True
                    else:
                        logger.error("❌ Protected routes data verification failed")
                        return False
                else:
                    self.test_results["protected_routes"] = {
                        "success": False,
                        "details": {
                            "status_code": response.status,
                            "error": response_text
                        }
                    }
                    logger.error(f"❌ Protected routes failed: {response_text}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Protected routes error: {e}")
            self.test_results["protected_routes"] = {
                "success": False,
                "details": {"error": str(e)}
            }
            return False
    
    async def test_cookie_persistence(self) -> bool:
        """Test cookie-based authentication persistence."""
        logger.info("=== Testing Cookie Persistence ===")
        
        if not self.cookies:
            logger.error("❌ No cookies available for persistence test")
            return False
        
        try:
            # Create a new session with stored cookies
            cookie_jar = aiohttp.CookieJar()
            for name, value in self.cookies.items():
                cookie_jar.update_cookies({name: value}, response_url=BASE_URL)
            
            async with aiohttp.ClientSession(cookie_jar=cookie_jar) as cookie_session:
                # Test Hebrew dashboard access with cookies
                async with cookie_session.get(f"{BASE_URL}/he/dashboard") as response:
                    response_text = await response.text()
                    logger.info(f"Cookie persistence test status: {response.status}")
                    
                    # Check if we get the dashboard (not redirected to login)
                    if response.status == 200:
                        # Look for dashboard indicators
                        dashboard_indicators = [
                            "dashboard" in response_text.lower(),
                            any(ord(char) > 1500 for char in response_text),  # Hebrew content
                            "login" not in response.url.path  # Not redirected to login
                        ]
                        
                        self.test_results["cookie_persistence"] = {
                            "success": any(dashboard_indicators),
                            "details": {
                                "status_code": response.status,
                                "url": str(response.url),
                                "dashboard_indicators": dashboard_indicators
                            }
                        }
                        
                        if any(dashboard_indicators):
                            logger.info("✅ Cookie persistence test successful!")
                            return True
                        else:
                            logger.error("❌ Cookie persistence failed - no dashboard access")
                            return False
                    
                    elif response.status == 302:
                        # Check if redirect is to login (bad) or elsewhere (maybe ok)
                        location = response.headers.get("Location", "")
                        if "login" in location:
                            logger.error(f"❌ Cookie persistence failed - redirected to login: {location}")
                            return False
                        else:
                            logger.info(f"Cookie persistence - redirected to: {location}")
                            return True
                    
                    else:
                        logger.error(f"❌ Cookie persistence failed: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Cookie persistence error: {e}")
            self.test_results["cookie_persistence"] = {
                "success": False,
                "details": {"error": str(e)}
            }
            return False
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete authentication flow test."""
        logger.info("🚀 Starting Complete Authentication Flow Test")
        logger.info(f"Test User: {TEST_USER['email']} / {TEST_USER['password']}")
        logger.info(f"Hebrew Name: {TEST_USER['hebrew_name']}")
        logger.info("-" * 80)
        
        # Run tests in sequence
        test_steps = [
            ("Registration", self.test_registration),
            ("Email Verification", self.test_email_verification),
            ("Login", self.test_login),
            ("Protected Routes", self.test_protected_routes),
            ("Cookie Persistence", self.test_cookie_persistence)
        ]
        
        results_summary = {"total_steps": len(test_steps), "passed": 0, "failed": 0}
        
        for step_name, test_func in test_steps:
            logger.info(f"\n🧪 Running: {step_name}")
            try:
                success = await test_func()
                if success:
                    results_summary["passed"] += 1
                    logger.info(f"✅ {step_name}: PASSED")
                else:
                    results_summary["failed"] += 1
                    logger.error(f"❌ {step_name}: FAILED")
                    
                    # Stop on critical failures
                    if step_name in ["Registration", "Email Verification", "Login"]:
                        logger.error(f"Critical step failed: {step_name}. Stopping test.")
                        break
            
            except Exception as e:
                results_summary["failed"] += 1
                logger.error(f"❌ {step_name}: ERROR - {e}")
                break
        
        # Additional Hebrew form test (non-blocking)
        logger.info(f"\n🧪 Running: Hebrew Login Form (Accessibility)")
        try:
            hebrew_form_success = await self.test_hebrew_login_form()
            if hebrew_form_success:
                logger.info("✅ Hebrew Login Form: ACCESSIBLE")
            else:
                logger.error("❌ Hebrew Login Form: INACCESSIBLE")
        except Exception as e:
            logger.error(f"❌ Hebrew Login Form: ERROR - {e}")
        
        # Compile final results
        final_results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_user": {
                "email": TEST_USER["email"],
                "hebrew_name": TEST_USER["hebrew_name"]
            },
            "summary": results_summary,
            "detailed_results": self.test_results,
            "overall_success": results_summary["failed"] == 0
        }
        
        return final_results


async def main():
    """Main test runner."""
    print("🔐 Memorial Authentication Flow Test")
    print("=" * 60)
    
    async with AuthFlowTester() as tester:
        results = await tester.run_complete_test()
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Steps: {results['summary']['total_steps']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Overall Success: {'✅ YES' if results['overall_success'] else '❌ NO'}")
        
        print(f"\nTest User: {results['test_user']['email']}")
        print(f"Hebrew Name: {results['test_user']['hebrew_name']}")
        
        # Save detailed results to file
        results_file = f"auth_flow_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📋 Detailed results saved to: {results_file}")
        
        # Print critical findings
        if not results['overall_success']:
            print("\n🔍 CRITICAL ISSUES FOUND:")
            for test_name, test_result in results['detailed_results'].items():
                if not test_result['success']:
                    print(f"   ❌ {test_name}: {test_result['details'].get('error', 'Unknown error')}")
        
        return 0 if results['overall_success'] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))