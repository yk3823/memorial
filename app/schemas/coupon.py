"""
Pydantic schemas for coupon endpoints in Memorial Website.
Defines request and response models for coupon management API.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, validator, EmailStr
from pydantic.types import PositiveInt


class CouponCreate(BaseModel):
    """Schema for creating a new coupon."""
    
    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Name of customer who made the manual payment"
    )
    
    unique_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Unique password for secure coupon code generation"
    )
    
    customer_email: Optional[EmailStr] = Field(
        None,
        description="Customer email for additional validation (optional)"
    )
    
    payment_amount: Decimal = Field(
        Decimal("100.00"),
        gt=0,
        le=Decimal("10000.00"),
        description="Amount that was paid manually"
    )
    
    currency: str = Field(
        "ILS",
        pattern="^(ILS|USD|EUR)$",
        description="Currency of the manual payment"
    )
    
    office_payment_reference: Optional[str] = Field(
        None,
        max_length=100,
        description="Office payment reference/receipt number"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the payment"
    )
    
    expires_in_days: int = Field(
        90,
        ge=1,
        le=365,
        description="Number of days until coupon expires"
    )
    
    subscription_months: PositiveInt = Field(
        1,
        le=12,
        description="Number of subscription months to grant"
    )
    
    max_memorials_granted: PositiveInt = Field(
        1,
        le=10,
        description="Number of memorials to allow"
    )
    
    @validator('customer_name')
    def validate_customer_name(cls, v):
        """Validate customer name format."""
        if not v or not v.strip():
            raise ValueError("שם הלקוח חובה")
        
        # Remove extra whitespaces
        return v.strip()
    
    @validator('unique_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not v or len(v.strip()) < 8:
            raise ValueError("סיסמה חייבת להיות באורך של לפחות 8 תווים")
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "customer_name": "יוסי כהן",
                "unique_password": "SecurePass2024!",
                "customer_email": "yossi@example.com",
                "payment_amount": "100.00",
                "currency": "ILS",
                "office_payment_reference": "REC-2024-001",
                "notes": "תשלום במזומן במשרד",
                "expires_in_days": 90,
                "subscription_months": 1,
                "max_memorials_granted": 1
            }
        }


class CouponValidation(BaseModel):
    """Schema for validating a coupon code."""
    
    coupon_code: str = Field(
        ...,
        min_length=10,
        max_length=100,
        description="Coupon code to validate"
    )
    
    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Customer name for validation"
    )
    
    customer_email: Optional[EmailStr] = Field(
        None,
        description="Customer email for additional validation"
    )
    
    @validator('coupon_code')
    def validate_coupon_code(cls, v):
        """Clean and validate coupon code."""
        if not v or not v.strip():
            raise ValueError("קוד קופון חובה")
        
        # Remove whitespaces and convert to uppercase
        return v.strip().upper()
    
    @validator('customer_name')
    def validate_customer_name(cls, v):
        """Validate customer name."""
        if not v or not v.strip():
            raise ValueError("שם הלקוח חובה")
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "coupon_code": "MEMORIAL-A1B2-C3D4-E5F6",
                "customer_name": "יוסי כהן",
                "customer_email": "yossi@example.com"
            }
        }


class CouponRevoke(BaseModel):
    """Schema for revoking a coupon."""
    
    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Reason for revoking the coupon"
    )
    
    @validator('reason')
    def validate_reason(cls, v):
        """Validate revocation reason."""
        if not v or not v.strip():
            raise ValueError("סיבה לביטול חובה")
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "reason": "הלקוח ביקש החזר כספי"
            }
        }


class CouponSummary(BaseModel):
    """Summary information about a coupon."""
    
    id: uuid.UUID
    code: str
    customer_name: str
    customer_email: Optional[str]
    payment_amount: Decimal
    currency: str
    formatted_amount: str
    status: str
    display_status: str
    is_used: bool
    is_valid: bool
    is_expired: bool
    created_at: datetime
    used_at: Optional[datetime]
    expires_at: Optional[datetime]
    age_in_days: int
    is_recent: bool
    
    class Config:
        from_attributes = True


class CouponDetail(CouponSummary):
    """Detailed coupon information (for admin views)."""
    
    created_by_admin_id: uuid.UUID
    used_by_user_id: Optional[uuid.UUID]
    office_payment_reference: Optional[str]
    notes: Optional[str]
    subscription_months: int
    max_memorials_granted: int
    validation_ip: Optional[str]
    validation_user_agent: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CouponResponse(BaseModel):
    """Response model for single coupon operations."""
    
    success: bool
    message: Optional[str] = None
    coupon: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "קופון נוצר בהצלחה",
                "coupon": {
                    "id": "12345678-1234-1234-1234-123456789012",
                    "code": "MEMORIAL-A1B2-C3D4-E5F6",
                    "customer_name": "יוסי כהן",
                    "payment_amount": "100.00",
                    "currency": "ILS",
                    "status": "active",
                    "is_used": False,
                    "created_at": "2024-08-24T16:00:00Z"
                }
            }
        }


class CouponValidationResponse(BaseModel):
    """Response model for coupon validation."""
    
    success: bool
    message: str
    is_valid: bool
    coupon: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "הקופון תקין ונוצל בהצלחה! המנוי שלך הופעל",
                "is_valid": True,
                "coupon": {
                    "id": "12345678-1234-1234-1234-123456789012",
                    "code": "****E5F6",
                    "customer_name": "יוסי כהן",
                    "payment_amount": "100.00",
                    "formatted_amount": "₪100.00",
                    "status": "used",
                    "is_used": True
                }
            }
        }


class CouponListResponse(BaseModel):
    """Response model for coupon listing."""
    
    success: bool
    coupons: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int
    has_more: bool
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "coupons": [
                    {
                        "id": "12345678-1234-1234-1234-123456789012",
                        "code": "MEMORIAL-A1B2-C3D4-E5F6",
                        "customer_name": "יוסי כהן",
                        "payment_amount": "100.00",
                        "status": "active",
                        "is_used": False,
                        "created_at": "2024-08-24T16:00:00Z"
                    }
                ],
                "total_count": 1,
                "limit": 50,
                "offset": 0,
                "has_more": False
            }
        }


class CouponStatsResponse(BaseModel):
    """Response model for coupon statistics."""
    
    success: bool
    stats: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "stats": {
                    "total_coupons": 100,
                    "used_coupons": 75,
                    "active_coupons": 20,
                    "expired_coupons": 5,
                    "unused_coupons": 25,
                    "usage_rate": 75.0,
                    "total_value_used": "7500.00",
                    "average_value": "100.00"
                }
            }
        }


# Error response models
class CouponErrorResponse(BaseModel):
    """Error response model for coupon operations."""
    
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "קוד הקופון לא נמצא במערכת",
                "error_code": "COUPON_NOT_FOUND"
            }
        }


# Additional utility schemas
class CouponCodeCheck(BaseModel):
    """Schema for checking if a coupon code exists."""
    
    coupon_code: str = Field(
        ...,
        min_length=10,
        max_length=100,
        description="Coupon code to check"
    )
    
    @validator('coupon_code')
    def validate_coupon_code(cls, v):
        """Clean coupon code."""
        return v.strip().upper() if v else ""


class CouponSearchFilter(BaseModel):
    """Schema for advanced coupon search filters."""
    
    customer_name: Optional[str] = Field(None, description="Customer name filter")
    status: Optional[str] = Field(None, description="Status filter")
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")
    used_after: Optional[datetime] = Field(None, description="Used after date")
    used_before: Optional[datetime] = Field(None, description="Used before date")
    min_amount: Optional[Decimal] = Field(None, description="Minimum payment amount")
    max_amount: Optional[Decimal] = Field(None, description="Maximum payment amount")
    currency: Optional[str] = Field(None, description="Currency filter")
    created_by_admin: Optional[uuid.UUID] = Field(None, description="Created by admin ID")
    include_expired: bool = Field(True, description="Include expired coupons")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_name": "יוסי",
                "status": "active",
                "created_after": "2024-01-01T00:00:00Z",
                "min_amount": "50.00",
                "currency": "ILS",
                "include_expired": False
            }
        }