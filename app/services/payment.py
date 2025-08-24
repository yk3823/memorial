"""
PayPal Payment Service for Memorial Website.
Handles PayPal SDK integration, payment creation, and transaction processing.
"""

import logging
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import paypalrestsdk
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.payment import Payment, PaymentStatus, PaymentMethod, CurrencyCode
from app.models.user import User
from app.services.coupon import CouponService, get_coupon_service

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Base exception for payment-related errors."""
    pass


class PayPalError(PaymentError):
    """Exception for PayPal API errors."""
    pass


class PaymentService:
    """
    Service for handling PayPal payments and subscription management.
    
    Integrates with PayPal REST SDK to process payments and manage
    user subscription activations.
    """
    
    def __init__(self):
        """Initialize PayPal service with configuration."""
        self.settings = get_settings()
        self._configure_paypal()
    
    def _configure_paypal(self) -> None:
        """Configure PayPal SDK with environment settings."""
        try:
            paypalrestsdk.configure({
                "mode": self.settings.PAYPAL_MODE,  # 'sandbox' or 'live'
                "client_id": self.settings.PAYPAL_CLIENT_ID,
                "client_secret": self.settings.PAYPAL_CLIENT_SECRET
            })
            logger.info(f"PayPal configured in {self.settings.PAYPAL_MODE} mode")
        except Exception as e:
            logger.error(f"PayPal configuration failed: {e}")
            raise PaymentError(f"PayPal configuration failed: {e}")
    
    async def create_payment(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: Decimal,
        currency: str = "ILS",
        description: str = "Memorial Website Subscription",
        success_url: str = None,
        cancel_url: str = None,
        coupon_code: str = None
    ) -> Payment:
        """
        Create a new payment record and PayPal payment.
        
        Args:
            db: Database session
            user_id: User ID making the payment
            amount: Payment amount
            currency: Currency code (ILS, USD, EUR)
            description: Payment description
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            coupon_code: Optional coupon code for manual payments
            
        Returns:
            Payment: Created payment record
            
        Raises:
            PaymentError: If payment creation fails
        """
        try:
            logger.info(f"Creating payment for user {user_id}: {amount} {currency}")
            
            # Validate user exists
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise PaymentError("User not found")
            
            if not user.is_verified:
                raise PaymentError("User email must be verified before payment")
            
            # Handle coupon payment (manual office payment)
            if coupon_code:
                return await self._create_coupon_payment(
                    db, user, amount, currency, description, coupon_code
                )
            
            # Create database payment record first
            payment = Payment(
                user_id=user_id,
                amount=amount,
                currency=currency,
                description=description,
                payment_method=PaymentMethod.PAYPAL.value,
                status=PaymentStatus.PENDING.value
            )
            
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            
            # Create PayPal payment
            paypal_payment = await self._create_paypal_payment(
                payment, success_url, cancel_url
            )
            
            # Update payment with PayPal details
            payment.payment_id = paypal_payment.id
            payment.order_id = paypal_payment.id  # PayPal uses same ID for both
            
            await db.commit()
            await db.refresh(payment)
            
            logger.info(f"Payment created successfully: {payment.id}")
            return payment
            
        except PaymentError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Payment creation failed: {e}")
            raise PaymentError(f"Payment creation failed: {str(e)}")
    
    async def _create_coupon_payment(
        self,
        db: AsyncSession,
        user: User,
        amount: Decimal,
        currency: str,
        description: str,
        coupon_code: str
    ) -> Payment:
        """Create a coupon-based payment (for manual office payments)."""
        logger.info(f"Processing coupon payment with code: {coupon_code}")
        
        # Get coupon service
        coupon_service = get_coupon_service()
        
        # Validate the coupon
        is_valid, coupon, error_message = await coupon_service.validate_coupon(
            db=db,
            coupon_code=coupon_code,
            customer_name=user.display_name,
            customer_email=user.email
        )
        
        if not is_valid:
            logger.warning(f"Coupon validation failed: {error_message}")
            raise PaymentError(f"אימות הקופון נכשל: {error_message}")
        
        if not coupon:
            logger.error(f"Coupon object not found for code: {coupon_code}")
            raise PaymentError("קוד הקופון לא תקין")
        
        # Use the coupon (this creates the payment and activates subscription)
        await coupon_service.use_coupon(
            db=db,
            coupon=coupon,
            user=user
        )
        
        # Get the created payment from the coupon usage
        stmt = (
            select(Payment)
            .where(
                and_(
                    Payment.user_id == user.id,
                    Payment.coupon_code == coupon_code,
                    Payment.payment_method == PaymentMethod.COUPON.value,
                    Payment.status == PaymentStatus.COMPLETED.value
                )
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        payment = result.scalar_one_or_none()
        
        if not payment:
            logger.error(f"Payment not found after coupon usage: {coupon_code}")
            raise PaymentError("שגיאה ביצירת התשלום מהקופון")
        
        logger.info(f"Coupon payment processed successfully: {payment.id} with code {coupon_code}")
        return payment
    
    async def _create_paypal_payment(
        self,
        payment: Payment,
        success_url: str = None,
        cancel_url: str = None
    ) -> paypalrestsdk.Payment:
        """
        Create PayPal payment using PayPal SDK.
        
        Args:
            payment: Database payment record
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL
            
        Returns:
            paypalrestsdk.Payment: PayPal payment object
        """
        try:
            # Default URLs if not provided
            base_url = self.settings.BASE_URL
            if not success_url:
                success_url = f"{base_url}/payment/success"
            if not cancel_url:
                cancel_url = f"{base_url}/payment/cancel"
            
            # Create PayPal payment object
            paypal_payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": f"{success_url}?paymentId={payment.id}",
                    "cancel_url": f"{cancel_url}?paymentId={payment.id}"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Memorial Website Subscription",
                            "sku": "memorial-sub-1",
                            "price": str(payment.amount),
                            "currency": payment.currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(payment.amount),
                        "currency": payment.currency
                    },
                    "description": payment.description
                }]
            })
            
            # Create the payment
            if not paypal_payment.create():
                error_msg = f"PayPal payment creation failed: {paypal_payment.error}"
                logger.error(error_msg)
                raise PayPalError(error_msg)
            
            logger.info(f"PayPal payment created: {paypal_payment.id}")
            return paypal_payment
            
        except Exception as e:
            logger.error(f"PayPal payment creation failed: {e}")
            raise PayPalError(f"PayPal payment creation failed: {str(e)}")
    
    def get_approval_url(self, payment: Payment) -> Optional[str]:
        """
        Get PayPal approval URL for redirect.
        
        Args:
            payment: Payment record
            
        Returns:
            str: PayPal approval URL or None
        """
        try:
            if not payment.payment_id:
                return None
            
            # Find PayPal payment
            paypal_payment = paypalrestsdk.Payment.find(payment.payment_id)
            
            if not paypal_payment:
                return None
            
            # Find approval URL
            for link in paypal_payment.links:
                if link.rel == "approval_url":
                    return link.href
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get approval URL: {e}")
            return None
    
    async def execute_payment(
        self,
        db: AsyncSession,
        payment_id: uuid.UUID,
        paypal_payment_id: str,
        payer_id: str
    ) -> Payment:
        """
        Execute PayPal payment after user approval.
        
        Args:
            db: Database session
            payment_id: Database payment ID
            paypal_payment_id: PayPal payment ID
            payer_id: PayPal payer ID
            
        Returns:
            Payment: Updated payment record
            
        Raises:
            PaymentError: If execution fails
        """
        try:
            logger.info(f"Executing payment: {payment_id}")
            
            # Get payment record
            stmt = select(Payment).options(selectinload(Payment.user)).where(Payment.id == payment_id)
            result = await db.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if not payment:
                raise PaymentError("Payment not found")
            
            if payment.status != PaymentStatus.PENDING.value:
                raise PaymentError(f"Payment is not in pending status: {payment.status}")
            
            # Execute PayPal payment
            paypal_payment = paypalrestsdk.Payment.find(paypal_payment_id)
            
            if not paypal_payment:
                raise PayPalError("PayPal payment not found")
            
            # Execute the payment
            if not paypal_payment.execute({"payer_id": payer_id}):
                error_msg = f"PayPal execution failed: {paypal_payment.error}"
                logger.error(error_msg)
                
                # Mark payment as failed
                payment.mark_failed("EXECUTION_FAILED", error_msg)
                await db.commit()
                
                raise PayPalError(error_msg)
            
            # Payment executed successfully - get transaction details
            transaction = paypal_payment.transactions[0]
            related_resources = transaction.related_resources[0]
            sale = related_resources.sale
            
            # Update payment record
            payment.mark_completed(sale.id)
            payment.paypal_payer_id = payer_id
            payment.paypal_transaction_id = sale.id
            
            # Get payer email from PayPal response
            if hasattr(paypal_payment, 'payer') and hasattr(paypal_payment.payer, 'payer_info'):
                payment.paypal_payer_email = paypal_payment.payer.payer_info.email
            
            await db.commit()
            
            # Activate user subscription
            await self._activate_user_subscription(db, payment)
            
            logger.info(f"Payment executed successfully: {payment.id}")
            return payment
            
        except PaymentError:
            raise
        except Exception as e:
            logger.error(f"Payment execution failed: {e}")
            raise PaymentError(f"Payment execution failed: {str(e)}")
    
    async def _activate_user_subscription(self, db: AsyncSession, payment: Payment) -> None:
        """Activate user subscription based on successful payment."""
        try:
            user = payment.user
            
            # Activate subscription from payment
            user.activate_subscription_from_payment(payment)
            
            await db.commit()
            
            logger.info(f"Subscription activated for user {user.id}")
            
        except Exception as e:
            logger.error(f"Failed to activate subscription: {e}")
            # Don't raise error here - payment was successful
    
    async def cancel_payment(
        self,
        db: AsyncSession,
        payment_id: uuid.UUID,
        reason: str = "User cancelled"
    ) -> Payment:
        """
        Cancel a payment.
        
        Args:
            db: Database session
            payment_id: Payment ID to cancel
            reason: Cancellation reason
            
        Returns:
            Payment: Updated payment record
        """
        try:
            stmt = select(Payment).where(Payment.id == payment_id)
            result = await db.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if not payment:
                raise PaymentError("Payment not found")
            
            payment.mark_cancelled(reason)
            await db.commit()
            
            logger.info(f"Payment cancelled: {payment_id}")
            return payment
            
        except Exception as e:
            logger.error(f"Payment cancellation failed: {e}")
            raise PaymentError(f"Payment cancellation failed: {str(e)}")
    
    async def get_payment(self, db: AsyncSession, payment_id: uuid.UUID) -> Optional[Payment]:
        """Get payment by ID."""
        try:
            stmt = select(Payment).options(selectinload(Payment.user)).where(Payment.id == payment_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get payment: {e}")
            return None
    
    async def get_user_payments(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[Payment]:
        """Get user's payment history."""
        try:
            stmt = (
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get user payments: {e}")
            return []
    
    def get_standard_payment_amount(self) -> Decimal:
        """Get standard payment amount (100 ILS)."""
        return Decimal("100.00")
    
    def get_payment_description(self) -> str:
        """Get standard payment description."""
        return "אתר הנצחה - מנוי חודשי"


# Dependency injection
def get_payment_service() -> PaymentService:
    """Get PaymentService instance."""
    return PaymentService()