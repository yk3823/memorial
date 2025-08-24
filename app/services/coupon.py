"""
Coupon Service for Memorial Website Manual Payment System.
Handles coupon generation, validation, and management for office payments.
"""

import logging
import secrets
import hashlib
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.coupon import Coupon, CouponStatus
from app.models.user import User
from app.models.payment import Payment, PaymentStatus, PaymentMethod

logger = logging.getLogger(__name__)


class CouponError(Exception):
    """Base exception for coupon-related errors."""
    pass


class CouponGenerationError(CouponError):
    """Exception for coupon generation errors."""
    pass


class CouponValidationError(CouponError):
    """Exception for coupon validation errors."""
    pass


class CouponService:
    """
    Service for handling coupon generation, validation, and management.
    
    Provides secure coupon creation for manual office payments and
    validates coupon usage during payment processing.
    """
    
    def __init__(self):
        """Initialize coupon service."""
        self.settings = get_settings()
        self._coupon_prefix = "MEMORIAL"
        self._code_length = 16  # Total length including prefix
    
    def _generate_secure_code(self, customer_name: str, unique_password: str) -> str:
        """
        Generate a secure coupon code based on customer name and password.
        
        Args:
            customer_name: Customer's name
            unique_password: Unique password for this coupon
            
        Returns:
            str: Secure coupon code
        """
        try:
            # Create a unique seed from customer name, password, and timestamp
            timestamp = str(int(datetime.utcnow().timestamp()))
            seed_data = f"{customer_name.lower().strip()}:{unique_password}:{timestamp}"
            
            # Add server-side secret for additional security
            server_secret = self.settings.SECRET_KEY or "default-secret"
            seed_data += f":{server_secret}"
            
            # Generate hash
            hash_object = hashlib.sha256(seed_data.encode())
            hash_hex = hash_object.hexdigest()
            
            # Create readable code from hash
            # Use alternating pattern of letters and numbers for readability
            code_part = ""
            for i in range(0, min(12, len(hash_hex)), 2):
                # Convert hex pairs to alphanumeric characters
                hex_pair = hash_hex[i:i+2]
                num_val = int(hex_pair, 16)
                
                if len(code_part) % 2 == 0:
                    # Use letters (A-Z)
                    char = chr(65 + (num_val % 26))
                else:
                    # Use numbers (0-9)  
                    char = str(num_val % 10)
                
                code_part += char
            
            # Format as readable groups
            formatted_code = f"{self._coupon_prefix}-{code_part[:4]}-{code_part[4:8]}-{code_part[8:]}"
            
            return formatted_code
            
        except Exception as e:
            logger.error(f"Failed to generate secure coupon code: {e}")
            raise CouponGenerationError(f"Code generation failed: {str(e)}")
    
    async def generate_coupon(
        self,
        db: AsyncSession,
        customer_name: str,
        unique_password: str,
        created_by_admin_id: uuid.UUID,
        customer_email: str = None,
        payment_amount: Decimal = Decimal("100.00"),
        currency: str = "ILS",
        office_payment_reference: str = None,
        notes: str = None,
        expires_in_days: int = 90,
        subscription_months: int = 1,
        max_memorials_granted: int = 1
    ) -> Coupon:
        """
        Generate a new coupon for manual office payment.
        
        Args:
            db: Database session
            customer_name: Name of customer who made payment
            unique_password: Unique password for secure code generation
            created_by_admin_id: ID of admin creating the coupon
            customer_email: Customer email (optional)
            payment_amount: Amount that was paid manually
            currency: Payment currency
            office_payment_reference: Office payment reference/receipt
            notes: Additional notes
            expires_in_days: How many days until coupon expires
            subscription_months: Months of subscription to grant
            max_memorials_granted: Number of memorials to allow
            
        Returns:
            Coupon: Created coupon object
            
        Raises:
            CouponGenerationError: If generation fails
        """
        try:
            logger.info(f"Generating coupon for customer: {customer_name}")
            
            # Validate admin exists and has permission
            stmt = select(User).where(User.id == created_by_admin_id)
            result = await db.execute(stmt)
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                raise CouponGenerationError("Admin user not found")
            
            if not admin_user.is_admin():
                raise CouponGenerationError("User does not have admin privileges")
            
            # Generate secure coupon code
            code = self._generate_secure_code(customer_name, unique_password)
            
            # Check if code already exists (very unlikely but possible)
            existing_coupon = await self._get_coupon_by_code(db, code)
            if existing_coupon:
                # Add timestamp suffix to ensure uniqueness
                timestamp_suffix = str(int(datetime.utcnow().timestamp()))[-4:]
                code = f"{code}-{timestamp_suffix}"
            
            # Set expiration date
            expires_at = None
            if expires_in_days > 0:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create coupon record
            coupon = Coupon(
                code=code,
                customer_name=customer_name.strip(),
                customer_email=customer_email.strip() if customer_email else None,
                payment_amount=payment_amount,
                currency=currency,
                created_by_admin_id=created_by_admin_id,
                office_payment_reference=office_payment_reference,
                notes=notes,
                expires_at=expires_at,
                subscription_months=subscription_months,
                max_memorials_granted=max_memorials_granted,
                status=CouponStatus.ACTIVE.value
            )
            
            db.add(coupon)
            await db.commit()
            await db.refresh(coupon)
            
            logger.info(f"Coupon generated successfully: {coupon.id} with code {code}")
            return coupon
            
        except CouponGenerationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Coupon generation failed: {e}")
            raise CouponGenerationError(f"Failed to generate coupon: {str(e)}")
    
    async def validate_coupon(
        self,
        db: AsyncSession,
        coupon_code: str,
        customer_name: str,
        customer_email: str = None
    ) -> Tuple[bool, Optional[Coupon], Optional[str]]:
        """
        Validate a coupon code for use.
        
        Args:
            db: Database session
            coupon_code: Coupon code to validate
            customer_name: Customer name for validation
            customer_email: Customer email for additional validation
            
        Returns:
            Tuple of (is_valid, coupon_object, error_message)
        """
        try:
            logger.info(f"Validating coupon: {coupon_code} for customer: {customer_name}")
            
            # Get coupon by code
            coupon = await self._get_coupon_by_code(db, coupon_code)
            
            if not coupon:
                return False, None, "קוד הקופון לא נמצא במערכת"
            
            # Check if coupon is already used
            if coupon.is_used:
                return False, coupon, f"קוד הקופון כבר נוצל בתאריך {coupon.used_at.strftime('%d/%m/%Y')}"
            
            # Check if coupon is active
            if coupon.status != CouponStatus.ACTIVE.value:
                status_messages = {
                    CouponStatus.EXPIRED.value: "פג תוקף הקופון",
                    CouponStatus.REVOKED.value: "הקופון בוטל",
                }
                message = status_messages.get(coupon.status, f"סטטוס הקופון: {coupon.display_status}")
                return False, coupon, message
            
            # Check expiration
            if coupon.is_expired():
                # Mark as expired if not already
                if coupon.status == CouponStatus.ACTIVE.value:
                    coupon.expire()
                    await db.commit()
                return False, coupon, f"פג תוקף הקופון בתאריך {coupon.expires_at.strftime('%d/%m/%Y')}"
            
            # Validate customer name
            if not coupon.can_be_used_by(customer_name, customer_email):
                return False, coupon, "שם הלקוח אינו תואם את פרטי הקופון"
            
            logger.info(f"Coupon validation successful: {coupon_code}")
            return True, coupon, None
            
        except Exception as e:
            logger.error(f"Coupon validation failed: {e}")
            return False, None, f"שגיאה בבדיקת הקופון: {str(e)}"
    
    async def use_coupon(
        self,
        db: AsyncSession,
        coupon: Coupon,
        user: User,
        validation_ip: str = None,
        validation_user_agent: str = None
    ) -> bool:
        """
        Mark coupon as used and create payment record.
        
        Args:
            db: Database session
            coupon: Coupon to mark as used
            user: User who is using the coupon
            validation_ip: IP address of validation
            validation_user_agent: User agent of validation
            
        Returns:
            bool: True if successfully used
        """
        try:
            logger.info(f"Using coupon {coupon.code} for user {user.id}")
            
            # Double-check coupon can be used
            if not coupon.is_valid():
                raise CouponValidationError("Coupon is not valid for use")
            
            # Mark coupon as used
            coupon.mark_as_used(
                user_id=user.id,
                validation_ip=validation_ip,
                validation_user_agent=validation_user_agent
            )
            
            # Create payment record for the coupon usage
            payment = Payment(
                user_id=user.id,
                amount=coupon.payment_amount,
                currency=coupon.currency,
                description=f"תשלום במשרד - קופון {coupon.code}",
                payment_method=PaymentMethod.COUPON.value,
                status=PaymentStatus.COMPLETED.value,
                coupon_code=coupon.code,
                processed_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                subscription_months=coupon.subscription_months,
                max_memorials_granted=coupon.max_memorials_granted,
                client_ip=validation_ip,
                user_agent=validation_user_agent
            )
            
            db.add(payment)
            await db.commit()
            
            # Activate user subscription
            user.activate_subscription_from_payment(payment)
            await db.commit()
            
            logger.info(f"Coupon used successfully: {coupon.code}, payment created: {payment.id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to use coupon: {e}")
            raise CouponValidationError(f"Failed to use coupon: {str(e)}")
    
    async def _get_coupon_by_code(self, db: AsyncSession, code: str) -> Optional[Coupon]:
        """Get coupon by code."""
        try:
            stmt = (
                select(Coupon)
                .options(selectinload(Coupon.created_by_admin), selectinload(Coupon.used_by_user))
                .where(Coupon.code == code)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get coupon by code: {e}")
            return None
    
    async def get_coupon_by_id(self, db: AsyncSession, coupon_id: uuid.UUID) -> Optional[Coupon]:
        """Get coupon by ID."""
        try:
            stmt = (
                select(Coupon)
                .options(selectinload(Coupon.created_by_admin), selectinload(Coupon.used_by_user))
                .where(Coupon.id == coupon_id)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get coupon by ID: {e}")
            return None
    
    async def list_coupons(
        self,
        db: AsyncSession,
        created_by_admin_id: uuid.UUID = None,
        status: str = None,
        customer_name: str = None,
        limit: int = 50,
        offset: int = 0,
        include_expired: bool = True
    ) -> List[Coupon]:
        """
        List coupons with filtering options.
        
        Args:
            db: Database session
            created_by_admin_id: Filter by admin who created coupons
            status: Filter by coupon status
            customer_name: Filter by customer name (partial match)
            limit: Maximum number of results
            offset: Number of results to skip
            include_expired: Whether to include expired coupons
            
        Returns:
            List[Coupon]: List of matching coupons
        """
        try:
            stmt = (
                select(Coupon)
                .options(selectinload(Coupon.created_by_admin), selectinload(Coupon.used_by_user))
            )
            
            # Apply filters
            conditions = []
            
            if created_by_admin_id:
                conditions.append(Coupon.created_by_admin_id == created_by_admin_id)
            
            if status:
                conditions.append(Coupon.status == status)
            
            if customer_name:
                conditions.append(Coupon.customer_name.ilike(f"%{customer_name}%"))
            
            if not include_expired:
                conditions.append(
                    or_(
                        Coupon.expires_at.is_(None),
                        Coupon.expires_at > datetime.utcnow()
                    )
                )
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Order by creation date (newest first)
            stmt = stmt.order_by(Coupon.created_at.desc())
            
            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)
            
            result = await db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to list coupons: {e}")
            return []
    
    async def get_coupon_stats(self, db: AsyncSession, admin_id: uuid.UUID = None) -> Dict[str, Any]:
        """
        Get coupon usage statistics.
        
        Args:
            db: Database session
            admin_id: Optional admin ID to filter by
            
        Returns:
            Dict: Statistics about coupon usage
        """
        try:
            base_query = select(Coupon)
            
            if admin_id:
                base_query = base_query.where(Coupon.created_by_admin_id == admin_id)
            
            # Total coupons
            total_result = await db.execute(select(func.count()).select_from(base_query))
            total = total_result.scalar()
            
            # Used coupons
            used_query = base_query.where(Coupon.is_used == True)
            used_result = await db.execute(select(func.count()).select_from(used_query))
            used = used_result.scalar()
            
            # Active coupons
            active_query = base_query.where(Coupon.status == CouponStatus.ACTIVE.value)
            active_result = await db.execute(select(func.count()).select_from(active_query))
            active = active_result.scalar()
            
            # Expired coupons
            expired_query = base_query.where(
                and_(
                    Coupon.expires_at.is_not(None),
                    Coupon.expires_at < datetime.utcnow()
                )
            )
            expired_result = await db.execute(select(func.count()).select_from(expired_query))
            expired = expired_result.scalar()
            
            # Total value of used coupons
            value_query = base_query.where(Coupon.is_used == True)
            value_result = await db.execute(
                select(func.sum(Coupon.payment_amount)).select_from(value_query)
            )
            total_value = value_result.scalar() or Decimal("0.00")
            
            return {
                "total_coupons": total,
                "used_coupons": used,
                "active_coupons": active,
                "expired_coupons": expired,
                "unused_coupons": total - used,
                "usage_rate": (used / total * 100) if total > 0 else 0,
                "total_value_used": total_value,
                "average_value": (total_value / used) if used > 0 else Decimal("0.00")
            }
            
        except Exception as e:
            logger.error(f"Failed to get coupon stats: {e}")
            return {}
    
    async def revoke_coupon(
        self,
        db: AsyncSession,
        coupon_id: uuid.UUID,
        reason: str,
        admin_id: uuid.UUID
    ) -> bool:
        """
        Revoke a coupon, making it unusable.
        
        Args:
            db: Database session
            coupon_id: ID of coupon to revoke
            reason: Reason for revocation
            admin_id: ID of admin performing the revocation
            
        Returns:
            bool: True if successfully revoked
        """
        try:
            # Get coupon
            coupon = await self.get_coupon_by_id(db, coupon_id)
            if not coupon:
                return False
            
            # Check if coupon is already used
            if coupon.is_used:
                raise CouponValidationError("Cannot revoke a coupon that has already been used")
            
            # Revoke the coupon
            coupon.revoke(reason)
            await db.commit()
            
            logger.info(f"Coupon {coupon.code} revoked by admin {admin_id}: {reason}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to revoke coupon: {e}")
            return False
    
    async def cleanup_expired_coupons(self, db: AsyncSession) -> int:
        """
        Mark expired coupons as expired status.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of coupons marked as expired
        """
        try:
            stmt = (
                update(Coupon)
                .where(
                    and_(
                        Coupon.expires_at < datetime.utcnow(),
                        Coupon.status == CouponStatus.ACTIVE.value
                    )
                )
                .values(status=CouponStatus.EXPIRED.value)
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            expired_count = result.rowcount
            logger.info(f"Marked {expired_count} coupons as expired")
            return expired_count
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cleanup expired coupons: {e}")
            return 0


# Dependency injection
def get_coupon_service() -> CouponService:
    """Get CouponService instance."""
    return CouponService()