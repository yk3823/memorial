#!/usr/bin/env python3
"""
Test script for the complete coupon workflow.
Verifies coupon generation, validation, and payment completion.
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, date

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.models.user import User, UserRole
from app.models.coupon import Coupon, CouponStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.services.coupon import CouponService
from app.services.auth import AuthService


async def main():
    """Test the complete coupon workflow."""
    settings = get_settings()
    
    # Create database connection
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
    
    SessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False
    )
    
    async with SessionLocal() as db:
        print("🧪 Testing Coupon Workflow")
        print("=" * 50)
        
        try:
            # Step 1: Create/Get admin user for testing
            print("1. Setting up test admin user...")
            admin_user = await setup_admin_user(db)
            print(f"   ✅ Admin user: {admin_user.email} (ID: {admin_user.id})")
            
            # Step 2: Create/Get regular user for testing
            print("2. Setting up test regular user...")
            regular_user = await setup_regular_user(db)
            print(f"   ✅ Regular user: {regular_user.email} (ID: {regular_user.id})")
            
            # Step 3: Generate a coupon
            print("3. Generating coupon...")
            coupon_service = CouponService()
            
            coupon = await coupon_service.generate_coupon(
                db=db,
                customer_name=regular_user.display_name,
                unique_password="TestPassword123!",
                created_by_admin_id=admin_user.id,
                customer_email=regular_user.email,
                payment_amount=Decimal("100.00"),
                currency="ILS",
                office_payment_reference="TEST-REF-001",
                notes="Test coupon for workflow verification",
                expires_in_days=30,
                subscription_months=1,
                max_memorials_granted=1
            )
            
            print(f"   ✅ Coupon generated: {coupon.code}")
            print(f"   📋 Status: {coupon.display_status}")
            print(f"   💰 Amount: {coupon.formatted_amount}")
            
            # Step 4: Validate the coupon
            print("4. Validating coupon...")
            is_valid, coupon_obj, error_message = await coupon_service.validate_coupon(
                db=db,
                coupon_code=coupon.code,
                customer_name=regular_user.display_name,
                customer_email=regular_user.email
            )
            
            if is_valid:
                print(f"   ✅ Coupon validation successful")
            else:
                print(f"   ❌ Coupon validation failed: {error_message}")
                return
            
            # Step 5: Use the coupon (simulate payment)
            print("5. Using coupon for payment...")
            await coupon_service.use_coupon(
                db=db,
                coupon=coupon,
                user=regular_user,
                validation_ip="127.0.0.1",
                validation_user_agent="Test-Agent/1.0"
            )
            
            print(f"   ✅ Coupon used successfully")
            
            # Step 6: Verify payment was created
            print("6. Verifying payment creation...")
            stmt = (
                select(Payment)
                .where(Payment.coupon_code == coupon.code)
                .where(Payment.user_id == regular_user.id)
            )
            result = await db.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if payment:
                print(f"   ✅ Payment created: ID {payment.id}")
                print(f"   💳 Method: {payment.payment_method}")
                print(f"   📈 Status: {payment.display_status}")
                print(f"   💰 Amount: {payment.formatted_amount}")
            else:
                print(f"   ❌ Payment not found")
                return
            
            # Step 7: Verify user subscription was activated
            print("7. Verifying subscription activation...")
            await db.refresh(regular_user)
            
            if regular_user.is_subscription_active():
                print(f"   ✅ Subscription activated")
                print(f"   📅 Status: {regular_user.subscription_status}")
                print(f"   🏠 Max memorials: {regular_user.max_memorials}")
            else:
                print(f"   ❌ Subscription not activated")
                return
            
            # Step 8: Verify coupon is marked as used
            print("8. Verifying coupon status...")
            await db.refresh(coupon)
            
            if coupon.is_used:
                print(f"   ✅ Coupon marked as used")
                print(f"   🕐 Used at: {coupon.used_at}")
                print(f"   👤 Used by: {coupon.used_by_user_id}")
            else:
                print(f"   ❌ Coupon not marked as used")
                return
            
            # Step 9: Test coupon statistics
            print("9. Testing coupon statistics...")
            stats = await coupon_service.get_coupon_stats(db=db, admin_id=admin_user.id)
            
            print(f"   📊 Admin's coupon stats:")
            print(f"   📦 Total coupons: {stats.get('total_coupons', 0)}")
            print(f"   ✅ Used coupons: {stats.get('used_coupons', 0)}")
            print(f"   📈 Usage rate: {stats.get('usage_rate', 0):.1f}%")
            print(f"   💰 Total value: ₪{stats.get('total_value_used', 0)}")
            
            # Step 10: Test duplicate coupon validation (should fail)
            print("10. Testing duplicate coupon usage...")
            is_valid_dup, _, error_msg_dup = await coupon_service.validate_coupon(
                db=db,
                coupon_code=coupon.code,
                customer_name=regular_user.display_name,
                customer_email=regular_user.email
            )
            
            if not is_valid_dup:
                print(f"   ✅ Duplicate usage correctly blocked: {error_msg_dup}")
            else:
                print(f"   ❌ Duplicate usage not blocked (this should not happen)")
                return
            
            print("\n🎉 All tests passed! Coupon workflow is working correctly.")
            print("=" * 50)
            print("✅ Coupon generation")
            print("✅ Coupon validation")  
            print("✅ Payment creation")
            print("✅ Subscription activation")
            print("✅ Coupon usage tracking")
            print("✅ Statistics calculation")
            print("✅ Duplicate prevention")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    await engine.dispose()
    return True


async def setup_admin_user(db) -> User:
    """Create or get admin user for testing."""
    # Check if admin exists
    stmt = select(User).where(User.email == "admin@memorial-test.com")
    result = await db.execute(stmt)
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        # Create admin user
        admin_user = User(
            email="admin@memorial-test.com",
            first_name="Test",
            last_name="Admin",
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True,
            subscription_status="active",
            subscription_end_date=date(2025, 12, 31)
        )
        admin_user.set_password("AdminPass123!")
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
    
    return admin_user


async def setup_regular_user(db) -> User:
    """Create or get regular user for testing."""
    # Check if user exists
    stmt = select(User).where(User.email == "user@memorial-test.com")
    result = await db.execute(stmt)
    regular_user = result.scalar_one_or_none()
    
    if not regular_user:
        # Create regular user
        regular_user = User(
            email="user@memorial-test.com",
            first_name="Test",
            last_name="User",
            hebrew_name="משתמש בדיקה",
            role=UserRole.USER.value,
            is_active=True,
            is_verified=True,
            subscription_status="trial"
        )
        regular_user.set_password("UserPass123!")
        
        db.add(regular_user)
        await db.commit()
        await db.refresh(regular_user)
    
    return regular_user


if __name__ == "__main__":
    print("🚀 Starting Coupon Workflow Test")
    
    success = asyncio.run(main())
    
    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed!")
        sys.exit(1)