"""
Schemas package initialization.
Exports all Pydantic models for API request/response validation.
"""

from .auth import *
from .memorial_simple import *
from .photo import *
from .user import *
from .payment import *
from .coupon import *

__all__ = [
    # Auth schemas
    "UserRegister",
    "UserRegisterResponse", 
    "UserLogin",
    "UserLoginResponse",
    "UserResponse",
    "UserMeResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "EmailVerificationRequest",
    "ResendVerificationRequest",
    "LogoutResponse",
    "PasswordChangeRequest",
    "UserProfileUpdate",
    "BaseResponse",
    "ErrorResponse",
    
    # Memorial schemas
    "MemorialCreate",
    "MemorialUpdate", 
    "MemorialResponse",
    "MemorialWithPhotos",
    "MemorialWithOwner",
    "PublicMemorialResponse",
    "MemorialListResponse",
    "MemorialSearchRequest",
    "MemorialSearchResponse",
    "MemorialStatsResponse",
    "MemorialSlugRequest",
    "MemorialSlugResponse",
    "MemorialVisibilityRequest",
    "MemorialLockRequest",
    "MemorialCreateResponse",
    "MemorialUpdateResponse",
    "MemorialDeleteResponse",
    "MemorialError",
    
    # Photo schemas
    "PhotoResponse",
    "PhotoCreate",
    
    # User schemas
    "UserResponse",
    
    # Payment schemas
    "PaymentCreateRequest",
    "PaymentExecuteRequest", 
    "PaymentCancelRequest",
    "PaymentResponse",
    "PaymentWithUserResponse",
    "PaymentCreateResponse",
    "PaymentExecuteResponse",
    "PaymentCancelResponse",
    "PaymentListResponse",
    "PaymentStatusResponse",
    "PaymentSummaryResponse",
    "PaymentErrorResponse",
    "PaymentAmountInfo",
    "PaymentMethodInfo",
    "PayPalWebhookEvent",
    "PayPalWebhookResponse",
    
    # Coupon schemas
    "CouponCreate",
    "CouponValidation",
    "CouponRevoke",
    "CouponSummary", 
    "CouponDetail",
    "CouponResponse",
    "CouponValidationResponse",
    "CouponListResponse",
    "CouponStatsResponse",
    "CouponErrorResponse",
    "CouponCodeCheck",
    "CouponSearchFilter"
]