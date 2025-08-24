"""
Payment model for Memorial Website PayPal integration.
Handles payment transactions, subscription management, and payment history.
"""

import enum
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Numeric, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class PaymentStatus(enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    """Payment method enumeration."""
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    COUPON = "coupon"  # For manual office payments


class CurrencyCode(enum.Enum):
    """Supported currency codes."""
    ILS = "ILS"  # Israeli Shekel
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro


class Payment(BaseModel):
    """
    Payment model for tracking PayPal transactions and subscription payments.
    
    Handles payment processing, status tracking, and integration with user subscriptions.
    """
    
    __tablename__ = "payments"
    
    # User relationship
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the user making the payment"
    )
    
    # Payment identification
    payment_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="PayPal payment ID"
    )
    
    order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="PayPal order ID"
    )
    
    # Payment details
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="ILS",
        comment="Currency code (ILS, USD, EUR)"
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="Memorial Website Subscription",
        comment="Payment description"
    )
    
    # Payment method and status
    payment_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="paypal",
        index=True,
        comment="Payment method used"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Payment status"
    )
    
    # PayPal specific fields
    paypal_payer_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="PayPal payer ID"
    )
    
    paypal_payer_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="PayPal payer email"
    )
    
    paypal_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="PayPal transaction ID"
    )
    
    # Coupon handling (for manual payments)
    coupon_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Coupon code used (for manual office payments)"
    )
    
    # Processing timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the payment was processed"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the payment was completed"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the payment approval expires"
    )
    
    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Error code if payment failed"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed error message if payment failed"
    )
    
    # Metadata for audit trail
    client_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address when payment was initiated"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent when payment was initiated"
    )
    
    # PayPal webhook data (stored as JSON)
    webhook_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="PayPal webhook notification data (JSON)"
    )
    
    # Subscription management
    subscription_months: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        comment="Number of subscription months purchased"
    )
    
    max_memorials_granted: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        comment="Number of memorials granted with this payment"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="payments",
        lazy="select"
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("ix_payment_user_status", "user_id", "status"),
        Index("ix_payment_method_status", "payment_method", "status"),
        Index("ix_payment_created_status", "created_at", "status"),
        Index("ix_payment_paypal_ids", "payment_id", "order_id", "paypal_transaction_id"),
        Index("ix_payment_currency_amount", "currency", "amount"),
    )
    
    # Payment status management methods
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status == PaymentStatus.PENDING.value
    
    def is_completed(self) -> bool:
        """Check if payment is completed."""
        return self.status == PaymentStatus.COMPLETED.value
    
    def is_cancelled(self) -> bool:
        """Check if payment is cancelled."""
        return self.status == PaymentStatus.CANCELLED.value
    
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED.value
    
    def mark_approved(self, payment_id: str = None, payer_id: str = None, payer_email: str = None) -> None:
        """Mark payment as approved by PayPal."""
        self.status = PaymentStatus.APPROVED.value
        self.processed_at = datetime.utcnow()
        
        if payment_id:
            self.payment_id = payment_id
        if payer_id:
            self.paypal_payer_id = payer_id
        if payer_email:
            self.paypal_payer_email = payer_email
    
    def mark_completed(self, transaction_id: str = None) -> None:
        """Mark payment as completed."""
        self.status = PaymentStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        
        if transaction_id:
            self.paypal_transaction_id = transaction_id
    
    def mark_cancelled(self, reason: str = None) -> None:
        """Mark payment as cancelled."""
        self.status = PaymentStatus.CANCELLED.value
        if reason:
            self.error_message = f"Payment cancelled: {reason}"
    
    def mark_failed(self, error_code: str = None, error_message: str = None) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED.value
        if error_code:
            self.error_code = error_code
        if error_message:
            self.error_message = error_message
    
    def set_webhook_data(self, webhook_data: dict) -> None:
        """Store PayPal webhook notification data."""
        import json
        self.webhook_data = json.dumps(webhook_data)
    
    def get_webhook_data(self) -> Optional[dict]:
        """Retrieve PayPal webhook notification data."""
        if self.webhook_data:
            import json
            try:
                return json.loads(self.webhook_data)
            except json.JSONDecodeError:
                return None
        return None
    
    # Computed properties
    @property
    def is_paypal_payment(self) -> bool:
        """Check if this is a PayPal payment."""
        return self.payment_method == PaymentMethod.PAYPAL.value
    
    @property
    def is_coupon_payment(self) -> bool:
        """Check if this is a coupon-based payment."""
        return self.payment_method == PaymentMethod.COUPON.value
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount with currency."""
        if self.currency == "ILS":
            return f"₪{self.amount:,.2f}"
        elif self.currency == "USD":
            return f"${self.amount:,.2f}"
        elif self.currency == "EUR":
            return f"€{self.amount:,.2f}"
        else:
            return f"{self.amount:,.2f} {self.currency}"
    
    @property
    def display_status(self) -> str:
        """Get user-friendly status display."""
        status_map = {
            PaymentStatus.PENDING.value: "ממתין לתשלום",
            PaymentStatus.APPROVED.value: "אושר",
            PaymentStatus.COMPLETED.value: "הושלם",
            PaymentStatus.CANCELLED.value: "בוטל",
            PaymentStatus.FAILED.value: "נכשל",
            PaymentStatus.REFUNDED.value: "הוחזר"
        }
        return status_map.get(self.status, self.status)
    
    def __repr__(self) -> str:
        """String representation of payment."""
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount} {self.currency}, status={self.status})>"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert payment to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive PayPal data
            
        Returns:
            dict: Payment data dictionary
        """
        data = super().to_dict()
        
        if not include_sensitive:
            # Remove sensitive fields for public API responses
            sensitive_fields = [
                'paypal_payer_id',
                'paypal_payer_email', 
                'paypal_transaction_id',
                'webhook_data',
                'client_ip',
                'user_agent',
                'error_message'
            ]
            for field in sensitive_fields:
                data.pop(field, None)
        
        # Add computed properties
        data['formatted_amount'] = self.formatted_amount
        data['display_status'] = self.display_status
        data['is_paypal_payment'] = self.is_paypal_payment
        data['is_coupon_payment'] = self.is_coupon_payment
        
        return data


# Update User model to include payment relationship
# This will be added to the User model via import or direct relationship
def add_payment_relationship_to_user():
    """
    Helper function to document the relationship that needs to be added to User model:
    
    # Add this to User model relationships section:
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="Payment.created_at.desc()"
    )
    """
    pass