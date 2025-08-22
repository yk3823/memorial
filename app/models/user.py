"""
User model for Memorial Website authentication and user management.
Handles user accounts, authentication, subscriptions, and authorization.
"""

import enum
import uuid
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import String, Boolean, DateTime, Date, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import check_password_hash, generate_password_hash

from .base import BaseModel


class UserRole(enum.Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class SubscriptionStatus(enum.Enum):
    """Subscription status enumeration."""
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class User(BaseModel):
    """
    User model for authentication and user management.
    
    Handles user accounts with authentication, subscription management,
    and role-based access control.
    """
    
    __tablename__ = "users"
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address (unique)"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed password using Werkzeug"
    )
    
    # Personal information
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's first name"
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's last name"
    )
    
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="User's phone number"
    )
    
    hebrew_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User's Hebrew name (optional)"
    )
    
    # Account status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the user account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the user's email is verified"
    )
    
    # Authentication tokens
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Token for email verification"
    )
    
    reset_password_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Token for password reset"
    )
    
    reset_password_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Password reset token expiration time"
    )
    
    # Subscription management
    subscription_status: Mapped[str] = mapped_column(
        String(20),
        default="trial",
        nullable=False,
        index=True,
        comment="User's subscription status"
    )
    
    subscription_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When the subscription expires"
    )
    
    trial_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When the trial period ends"
    )
    
    # Memorial limits based on subscription
    max_memorials: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        comment="Maximum number of memorials allowed for this user"
    )
    
    # Authorization
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False,
        index=True,
        comment="User's role for authorization"
    )
    
    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )
    
    login_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Total number of successful logins"
    )
    
    # Relationships
    memorials: Mapped[List["Memorial"]] = relationship(
        "Memorial",
        back_populates="owner",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("ix_user_email_active", "email", "is_active"),
        Index("ix_user_subscription_status", "subscription_status", "subscription_end_date"),
        Index("ix_user_role_active", "role", "is_active"),
        Index("ix_user_verification_token", "verification_token", unique=True, postgresql_where="verification_token IS NOT NULL"),
        Index("ix_user_reset_token", "reset_password_token", unique=True, postgresql_where="reset_password_token IS NOT NULL"),
    )
    
    # Password management methods
    def set_password(self, password: str) -> None:
        """
        Set user password with proper hashing.
        
        Args:
            password: Plain text password to hash and store
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self) -> str:
        """
        Generate a unique verification token for email confirmation.
        
        Returns:
            str: Generated verification token
        """
        self.verification_token = str(uuid.uuid4())
        return self.verification_token
    
    def generate_reset_password_token(self, expires_in_hours: int = 1) -> str:
        """
        Generate a password reset token with expiration.
        
        Args:
            expires_in_hours: How many hours the token should be valid
            
        Returns:
            str: Generated reset token
        """
        from datetime import timedelta
        
        self.reset_password_token = str(uuid.uuid4())
        self.reset_password_expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        return self.reset_password_token
    
    def clear_reset_password_token(self) -> None:
        """Clear password reset token and expiration."""
        self.reset_password_token = None
        self.reset_password_expires_at = None
    
    def is_reset_token_valid(self) -> bool:
        """
        Check if the current reset token is still valid.
        
        Returns:
            bool: True if token exists and hasn't expired
        """
        if not self.reset_password_token or not self.reset_password_expires_at:
            return False
        return datetime.utcnow() < self.reset_password_expires_at
    
    def verify_email(self) -> None:
        """Mark user email as verified and clear verification token."""
        self.is_verified = True
        self.verification_token = None
    
    def record_login(self) -> None:
        """Record a successful login."""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
    
    # Subscription management methods
    def is_subscription_active(self) -> bool:
        """
        Check if user has an active subscription.
        
        Returns:
            bool: True if subscription is active and not expired
        """
        if self.subscription_status == "active":
            if self.subscription_end_date:
                return date.today() <= self.subscription_end_date
            return True
        elif self.subscription_status == "trial":
            if self.trial_end_date:
                return date.today() <= self.trial_end_date
            return True
        return False
    
    def activate_subscription(self, end_date: date) -> None:
        """
        Activate user subscription.
        
        Args:
            end_date: When the subscription should end
        """
        self.subscription_status = "active"
        self.subscription_end_date = end_date
    
    def cancel_subscription(self) -> None:
        """Cancel user subscription."""
        self.subscription_status = "cancelled"
    
    def expire_subscription(self) -> None:
        """Mark subscription as expired."""
        self.subscription_status = "expired"
    
    def start_trial(self, trial_days: int = 14) -> None:
        """
        Start trial period for user.
        
        Args:
            trial_days: Number of days for trial period
        """
        from datetime import timedelta
        
        self.subscription_status = "trial"
        self.trial_end_date = date.today() + timedelta(days=trial_days)
    
    # Authorization methods
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
    
    def can_create_memorial(self) -> bool:
        """Check if user can create memorial pages."""
        if not (self.is_active and self.is_verified and self.is_subscription_active()):
            return False
        
        # Check memorial limit
        active_memorials_count = len([m for m in self.memorials if not m.is_deleted])
        return active_memorials_count < self.max_memorials
    
    def get_memorial_usage(self) -> dict:
        """Get memorial usage statistics."""
        active_memorials_count = len([m for m in self.memorials if not m.is_deleted])
        return {
            "current": active_memorials_count,
            "limit": self.max_memorials,
            "remaining": max(0, self.max_memorials - active_memorials_count),
            "can_create": active_memorials_count < self.max_memorials
        }
    
    def can_edit_memorial(self, memorial_id: uuid.UUID) -> bool:
        """
        Check if user can edit a specific memorial.
        
        Args:
            memorial_id: ID of the memorial to check
            
        Returns:
            bool: True if user can edit the memorial
        """
        if not self.is_active:
            return False
        
        if self.is_admin():
            return True
        
        # Check if user owns the memorial
        for memorial in self.memorials:
            if memorial.id == memorial_id:
                return True
        
        return False
    
    # Computed properties
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get display name (Hebrew name if available, otherwise full name)."""
        return self.hebrew_name if self.hebrew_name else self.full_name
    
    def __repr__(self) -> str:
        """String representation of user."""
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert user to dictionary, excluding sensitive fields by default.
        
        Args:
            exclude: Additional fields to exclude
            
        Returns:
            dict: User data dictionary
        """
        default_exclude = [
            'password_hash', 
            'verification_token', 
            'reset_password_token',
            'reset_password_expires_at'
        ]
        
        if exclude:
            default_exclude.extend(exclude)
        
        return super().to_dict(exclude=default_exclude)