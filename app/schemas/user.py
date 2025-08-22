"""
User schemas for Memorial Website.
Pydantic models for user data validation and serialization.
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr

from app.models.user import UserRole, SubscriptionStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    hebrew_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Schema for user updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    hebrew_name: Optional[str] = Field(None, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    is_active: bool
    is_verified: bool
    subscription_status: SubscriptionStatus
    subscription_end_date: Optional[date]
    trial_end_date: Optional[date]
    role: UserRole
    last_login_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Extended user profile schema."""
    memorial_count: int = 0
    total_photos: int = 0
    subscription_days_remaining: Optional[int] = None