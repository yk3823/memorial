"""
Pydantic schemas for authentication and authorization in Memorial Website.
Defines request and response models for all auth-related API endpoints.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole, SubscriptionStatus


# Base Response Model
class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = True
    message: str = "Operation successful"


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# User Registration Schemas
class UserRegister(BaseModel):
    """Schema for user registration request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    confirm_password: str = Field(..., description="Password confirmation")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    hebrew_name: Optional[str] = Field(None, max_length=100, description="User's Hebrew name (optional)")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number (optional)")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('passwords do not match')
        return v
    
    @field_validator('first_name', 'last_name', 'hebrew_name')
    @classmethod
    def names_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('name cannot be empty or whitespace only')
        return v.strip() if v else v
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "hebrew_name": "Hebrew Name",
                "phone_number": "+1-555-123-4567"
            }
        }
    }


class UserRegisterResponse(BaseResponse):
    """Schema for user registration response."""
    user_id: UUID = Field(..., description="Created user ID")
    email: EmailStr = Field(..., description="User's email address")
    verification_required: bool = Field(True, description="Whether email verification is required")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "User registered successfully. Please check your email to verify your account.",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "verification_required": True
            }
        }
    }


# User Login Schemas
class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    remember_me: bool = Field(False, description="Whether to remember the user (extends session)")
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }
    }


class UserLoginResponse(BaseResponse):
    """Schema for user login response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: "UserResponse" = Field(..., description="User information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Login successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1440,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_verified": True,
                    "role": "user"
                }
            }
        }
    }


# Token Schemas
class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., description="JWT refresh token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class RefreshTokenResponse(BaseResponse):
    """Schema for refresh token response."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User's email address")
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com"
            }
        }
    }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('passwords do not match')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "abc123def456ghi789",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }
    }


# Email Verification Schemas
class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""
    token: str = Field(..., description="Email verification token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "abc123def456ghi789"
            }
        }
    }


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""
    email: EmailStr = Field(..., description="User's email address")
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com"
            }
        }
    }


# User Response Schemas
class UserResponse(BaseModel):
    """Schema for user response data."""
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    full_name: str = Field(..., description="User's full name")
    hebrew_name: Optional[str] = Field(None, description="User's Hebrew name")
    display_name: str = Field(..., description="User's display name")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    
    # Account status
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(..., description="Whether user's email is verified")
    role: UserRole = Field(..., description="User's role")
    
    # Subscription information
    subscription_status: SubscriptionStatus = Field(..., description="User's subscription status")
    subscription_end_date: Optional[date] = Field(None, description="When subscription expires")
    trial_end_date: Optional[date] = Field(None, description="When trial period ends")
    
    # Activity information
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(..., description="Total number of logins")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last account update timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "hebrew_name": "Hebrew Name",
                "display_name": "�����",
                "phone_number": "+1-555-123-4567",
                "is_active": True,
                "is_verified": True,
                "role": "user",
                "subscription_status": "active",
                "subscription_end_date": "2024-12-31",
                "trial_end_date": None,
                "last_login_at": "2024-08-10T12:00:00Z",
                "login_count": 5,
                "created_at": "2024-08-01T10:00:00Z",
                "updated_at": "2024-08-10T12:00:00Z"
            }
        }
    }


class UserMeResponse(BaseResponse):
    """Schema for current user information response."""
    user: UserResponse = Field(..., description="Current user information")


# Logout Schema
class LogoutResponse(BaseResponse):
    """Schema for logout response."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Logged out successfully"
            }
        }
    }


# Password Change Schema
class PasswordChangeRequest(BaseModel):
    """Schema for password change request (authenticated users)."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('passwords do not match')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }
    }


# User Profile Update Schema
class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's last name")
    hebrew_name: Optional[str] = Field(None, max_length=100, description="User's Hebrew name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    
    @field_validator('first_name', 'last_name', 'hebrew_name')
    @classmethod
    def names_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('name cannot be empty or whitespace only')
        return v.strip() if v else v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "hebrew_name": "Hebrew Name",
                "phone_number": "+1-555-123-4567"
            }
        }
    }


# Authentication Status Schema
class AuthStatus(BaseModel):
    """Schema for authentication status."""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[UserResponse] = Field(None, description="User information if authenticated")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "authenticated": True,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "user"
                },
                "permissions": ["read:memorials", "write:own_memorials"]
            }
        }
    }


# Validation Error Schema
class ValidationErrorResponse(ErrorResponse):
    """Schema for validation error response."""
    validation_errors: List[Dict[str, Any]] = Field(..., description="List of validation errors")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "validation_errors": [
                    {
                        "field": "email",
                        "message": "field required",
                        "type": "value_error.missing"
                    }
                ]
            }
        }
    }