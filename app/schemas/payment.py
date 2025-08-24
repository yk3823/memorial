"""
Payment schemas for Memorial Website PayPal integration.
Handles request/response validation for payment API endpoints.
"""

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from pydantic.types import UUID4

from app.schemas.user import UserResponse


class PaymentStatusEnum(str, Enum):
    """Payment status enumeration for API."""
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration for API."""
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    COUPON = "coupon"


class CurrencyEnum(str, Enum):
    """Currency enumeration for API."""
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"


# Request Schemas

class PaymentCreateRequest(BaseModel):
    """Request schema for creating a new payment."""
    
    amount: Optional[Decimal] = Field(
        default=Decimal("100.00"),
        gt=0,
        le=10000,
        description="Payment amount (default: 100 ILS)"
    )
    
    currency: CurrencyEnum = Field(
        default=CurrencyEnum.ILS,
        description="Currency code (ILS, USD, EUR)"
    )
    
    description: Optional[str] = Field(
        default="אתר הנצחה - מנוי חודשי",
        max_length=500,
        description="Payment description"
    )
    
    coupon_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Coupon code for manual office payments"
    )
    
    success_url: Optional[str] = Field(
        default=None,
        description="Custom success redirect URL"
    )
    
    cancel_url: Optional[str] = Field(
        default=None,
        description="Custom cancel redirect URL"
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 10000:
            raise ValueError("Amount cannot exceed 10,000")
        return v
    
    @field_validator('coupon_code')
    @classmethod
    def validate_coupon_code(cls, v):
        if v is not None:
            v = v.strip().upper()
            if not v:
                return None
        return v


class PaymentExecuteRequest(BaseModel):
    """Request schema for executing PayPal payment."""
    
    payment_id: UUID4 = Field(description="Database payment ID")
    paypal_payment_id: str = Field(description="PayPal payment ID")
    payer_id: str = Field(description="PayPal payer ID")


class PaymentCancelRequest(BaseModel):
    """Request schema for cancelling payment."""
    
    payment_id: UUID4 = Field(description="Payment ID to cancel")
    reason: Optional[str] = Field(
        default="User cancelled",
        max_length=255,
        description="Cancellation reason"
    )


# Response Schemas

class PaymentResponse(BaseModel):
    """Base payment response schema."""
    
    id: UUID4
    user_id: UUID4
    amount: Decimal
    currency: str
    description: str
    payment_method: str
    status: str
    
    # PayPal specific fields (optional)
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Computed fields
    formatted_amount: str
    display_status: str
    is_paypal_payment: bool
    is_coupon_payment: bool
    
    # Subscription details
    subscription_months: int
    max_memorials_granted: int
    
    class Config:
        from_attributes = True


class PaymentWithUserResponse(PaymentResponse):
    """Payment response with user information."""
    
    user: UserResponse
    
    class Config:
        from_attributes = True


class PaymentCreateResponse(BaseModel):
    """Response schema for payment creation."""
    
    success: bool
    message: str
    payment: PaymentResponse
    approval_url: Optional[str] = None  # PayPal approval URL for redirect
    requires_approval: bool = True  # Whether payment needs user approval


class PaymentExecuteResponse(BaseModel):
    """Response schema for payment execution."""
    
    success: bool
    message: str
    payment: PaymentResponse
    subscription_activated: bool = False


class PaymentCancelResponse(BaseModel):
    """Response schema for payment cancellation."""
    
    success: bool
    message: str
    payment: PaymentResponse


class PaymentListResponse(BaseModel):
    """Response schema for payment list."""
    
    success: bool
    message: str
    payments: List[PaymentResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class PaymentStatusResponse(BaseModel):
    """Response schema for payment status check."""
    
    success: bool
    message: str
    payment: PaymentResponse


class PaymentSummaryResponse(BaseModel):
    """Response schema for user payment summary."""
    
    success: bool
    message: str
    total_payments: int
    completed_payments: int
    total_amount_paid: Decimal
    last_payment: Optional[PaymentResponse] = None
    has_active_subscription: bool


# Webhook Schemas

class PayPalWebhookEvent(BaseModel):
    """PayPal webhook event schema."""
    
    id: str
    event_type: str
    create_time: datetime
    resource_type: str
    resource: dict
    summary: Optional[str] = None


class PayPalWebhookResponse(BaseModel):
    """Response for PayPal webhook processing."""
    
    success: bool
    message: str
    processed_event_id: str


# Error Response Schemas

class PaymentErrorResponse(BaseModel):
    """Error response schema for payment operations."""
    
    success: bool = False
    message: str
    error_code: Optional[str] = None
    error_details: Optional[dict] = None
    payment_id: Optional[UUID4] = None


# Utility Schemas

class PaymentAmountInfo(BaseModel):
    """Information about payment amounts and pricing."""
    
    standard_amount: Decimal = Decimal("100.00")
    currency: str = "ILS"
    formatted_amount: str = "₪100.00"
    description: str = "אתר הנצחה - מנוי חודשי"
    subscription_duration_months: int = 1
    memorial_allowance: int = 1


class PaymentMethodInfo(BaseModel):
    """Information about available payment methods."""
    
    paypal_enabled: bool = True
    coupon_enabled: bool = True
    supported_currencies: List[str] = ["ILS", "USD", "EUR"]
    minimum_amount: Decimal = Decimal("1.00")
    maximum_amount: Decimal = Decimal("10000.00")


# Admin Schemas (for internal use)

class PaymentAdminResponse(PaymentResponse):
    """Extended payment response for admin users with sensitive data."""
    
    # PayPal sensitive fields
    paypal_payer_id: Optional[str] = None
    paypal_payer_email: Optional[str] = None
    paypal_transaction_id: Optional[str] = None
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Audit trail
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Webhook data
    webhook_data: Optional[dict] = None
    
    class Config:
        from_attributes = True


class PaymentStatsResponse(BaseModel):
    """Payment statistics for admin dashboard."""
    
    total_payments: int
    completed_payments: int
    pending_payments: int
    failed_payments: int
    cancelled_payments: int
    
    total_revenue: Decimal
    total_revenue_formatted: str
    
    paypal_payments: int
    coupon_payments: int
    
    payments_today: int
    payments_this_week: int
    payments_this_month: int
    
    average_payment_amount: Decimal
    success_rate: float