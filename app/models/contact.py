"""
Contact model for Memorial Website.
Handles contact information for memorial notifications via email and WhatsApp.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional, List
import re

from sqlalchemy import String, Boolean, ForeignKey, Index, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class ContactType(enum.Enum):
    """Contact type enumeration."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class Contact(BaseModel):
    """
    Contact model for memorial page notification recipients.
    
    Stores email addresses and WhatsApp phone numbers for sending
    yahrzeit reminders and memorial updates.
    """
    
    __tablename__ = "contacts"
    
    # Memorial relationship
    memorial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memorials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the memorial this contact belongs to"
    )
    
    # Contact information
    contact_type: Mapped[ContactType] = mapped_column(
        nullable=False,
        index=True,
        comment="Type of contact (email or whatsapp)"
    )
    
    contact_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email address or phone number"
    )
    
    contact_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the contact person"
    )
    
    relationship_to_deceased: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Relationship to the deceased (son, daughter, friend, etc.)"
    )
    
    # Notification settings
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether notifications are enabled for this contact"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the contact has been verified (clicked confirmation link)"
    )
    
    # Verification
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Token for contact verification"
    )
    
    verification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the verification message was sent"
    )
    
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the contact was verified"
    )
    
    # Notification preferences
    yahrzeit_reminder_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether to send yahrzeit reminders"
    )
    
    yahrzeit_reminder_days_before: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        comment="How many days before yahrzeit to send reminder"
    )
    
    memorial_updates_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether to send memorial update notifications"
    )
    
    # Activity tracking
    last_notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the last notification was sent to this contact"
    )
    
    notification_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Total number of notifications sent to this contact"
    )
    
    # Bounce/error tracking
    bounce_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of bounced/failed notifications"
    )
    
    last_bounce_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the last bounce occurred"
    )
    
    is_bouncing: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this contact is currently bouncing (too many failures)"
    )
    
    # Added by information
    added_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID of the user who added this contact"
    )
    
    # Relationships
    memorial: Mapped["Memorial"] = relationship(
        "Memorial",
        back_populates="contacts",
        lazy="select"
    )
    
    added_by: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="select"
    )
    
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="contact",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Database constraints and indexes
    __table_args__ = (
        # Ensure valid reminder days
        CheckConstraint(
            "yahrzeit_reminder_days_before >= 0 AND yahrzeit_reminder_days_before <= 30",
            name="ck_contact_reminder_days_range"
        ),
        
        # Ensure non-negative counters
        CheckConstraint(
            "notification_count >= 0",
            name="ck_contact_notification_count_non_negative"
        ),
        
        CheckConstraint(
            "bounce_count >= 0", 
            name="ck_contact_bounce_count_non_negative"
        ),
        
        # Performance indexes
        Index("ix_contact_memorial_type", "memorial_id", "contact_type"),
        Index("ix_contact_memorial_enabled", "memorial_id", "notification_enabled"),
        Index("ix_contact_memorial_verified", "memorial_id", "is_verified"),
        Index("ix_contact_type_value", "contact_type", "contact_value"),
        Index("ix_contact_bouncing", "is_bouncing", "bounce_count"),
        Index("ix_contact_verification", "verification_token", unique=True, postgresql_where="verification_token IS NOT NULL"),
        
        # Unique constraint: one contact value per memorial
        Index(
            "ix_contact_memorial_value_unique",
            "memorial_id", "contact_value",
            unique=True,
            postgresql_where="is_deleted = false"
        ),
    )
    
    # Validation methods
    def is_valid_email(self) -> bool:
        """
        Validate email address format.
        
        Returns:
            bool: True if valid email format
        """
        if self.contact_type != ContactType.EMAIL:
            return True  # Not an email, so N/A
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, self.contact_value))
    
    def is_valid_phone(self) -> bool:
        """
        Validate phone number format for WhatsApp.
        
        Returns:
            bool: True if valid phone format
        """
        if self.contact_type != ContactType.WHATSAPP:
            return True  # Not a phone, so N/A
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', self.contact_value)
        
        # Should be between 10-15 digits (international format)
        return 10 <= len(digits_only) <= 15
    
    def normalize_contact_value(self) -> str:
        """
        Normalize the contact value based on type.
        
        Returns:
            str: Normalized contact value
        """
        if self.contact_type == ContactType.EMAIL:
            return self.contact_value.lower().strip()
        
        elif self.contact_type == ContactType.WHATSAPP:
            # Remove all non-digit characters and add + prefix if not present
            digits_only = re.sub(r'\D', '', self.contact_value)
            return f"+{digits_only}" if not digits_only.startswith('+') else digits_only
        
        return self.contact_value
    
    # Verification methods
    def generate_verification_token(self) -> str:
        """
        Generate a unique verification token.
        
        Returns:
            str: Generated verification token
        """
        self.verification_token = str(uuid.uuid4())
        self.verification_sent_at = datetime.utcnow()
        return self.verification_token
    
    def verify_contact(self) -> None:
        """Mark contact as verified and clear verification token."""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        self.verification_token = None
        self.is_bouncing = False  # Reset bouncing status on verification
        self.bounce_count = 0
    
    def is_verification_expired(self, hours: int = 24) -> bool:
        """
        Check if verification token has expired.
        
        Args:
            hours: Hours until expiration
            
        Returns:
            bool: True if verification has expired
        """
        if not self.verification_sent_at:
            return True
        
        from datetime import timedelta
        expiry_time = self.verification_sent_at + timedelta(hours=hours)
        return datetime.utcnow() > expiry_time
    
    def needs_verification(self) -> bool:
        """
        Check if contact needs verification.
        
        Returns:
            bool: True if contact needs to be verified
        """
        return not self.is_verified and not self.is_bouncing
    
    # Notification management
    def can_receive_notifications(self) -> bool:
        """
        Check if contact can receive notifications.
        
        Returns:
            bool: True if contact can receive notifications
        """
        return (
            self.notification_enabled and
            self.is_verified and
            not self.is_bouncing and
            not self.is_deleted
        )
    
    def record_notification_sent(self) -> None:
        """Record that a notification was sent to this contact."""
        self.last_notification_sent_at = datetime.utcnow()
        self.notification_count += 1
    
    def record_bounce(self) -> None:
        """Record a bounced/failed notification."""
        self.bounce_count += 1
        self.last_bounce_at = datetime.utcnow()
        
        # Mark as bouncing if too many failures
        if self.bounce_count >= 3:
            self.is_bouncing = True
            self.notification_enabled = False
    
    def reset_bounce_status(self) -> None:
        """Reset bouncing status after successful delivery."""
        self.bounce_count = 0
        self.is_bouncing = False
        self.last_bounce_at = None
    
    # Notification preference methods
    def enable_yahrzeit_reminders(self, days_before: int = 1) -> None:
        """
        Enable yahrzeit reminders.
        
        Args:
            days_before: How many days before to send reminder
        """
        if 0 <= days_before <= 30:
            self.yahrzeit_reminder_enabled = True
            self.yahrzeit_reminder_days_before = days_before
        else:
            raise ValueError("Days before must be between 0 and 30")
    
    def disable_yahrzeit_reminders(self) -> None:
        """Disable yahrzeit reminders."""
        self.yahrzeit_reminder_enabled = False
    
    def enable_memorial_updates(self) -> None:
        """Enable memorial update notifications."""
        self.memorial_updates_enabled = True
    
    def disable_memorial_updates(self) -> None:
        """Disable memorial update notifications."""
        self.memorial_updates_enabled = False
    
    def disable_all_notifications(self) -> None:
        """Disable all notifications for this contact."""
        self.notification_enabled = False
        self.yahrzeit_reminder_enabled = False
        self.memorial_updates_enabled = False
    
    def enable_all_notifications(self) -> None:
        """Enable all notifications for this contact."""
        if self.can_receive_notifications():
            self.notification_enabled = True
            self.yahrzeit_reminder_enabled = True
            self.memorial_updates_enabled = True
    
    # Display properties
    @hybrid_property
    def display_contact(self) -> str:
        """Get formatted contact value for display."""
        if self.contact_type == ContactType.EMAIL:
            return self.contact_value
        
        elif self.contact_type == ContactType.WHATSAPP:
            # Format phone number for display
            digits = re.sub(r'\D', '', self.contact_value)
            if len(digits) >= 10:
                # Format as international number
                return f"+{digits}"
            return self.contact_value
        
        return self.contact_value
    
    @hybrid_property
    def contact_type_display(self) -> str:
        """Get display name for contact type."""
        return {
            ContactType.EMAIL: "Email",
            ContactType.WHATSAPP: "WhatsApp"
        }.get(self.contact_type, self.contact_type.value)
    
    @hybrid_property
    def status_display(self) -> str:
        """Get display status for contact."""
        if self.is_bouncing:
            return "Bouncing"
        elif not self.is_verified:
            return "Pending Verification"
        elif not self.notification_enabled:
            return "Disabled"
        else:
            return "Active"
    
    @hybrid_property
    def display_name_with_relationship(self) -> str:
        """Get display name with relationship if available."""
        if self.relationship_to_deceased:
            return f"{self.contact_name} ({self.relationship_to_deceased})"
        return self.contact_name
    
    def __repr__(self) -> str:
        """String representation of contact."""
        return f"<Contact(id={self.id}, memorial_id={self.memorial_id}, type={self.contact_type.value}, contact={self.contact_value})>"
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert contact to dictionary.
        
        Args:
            exclude: Fields to exclude
            
        Returns:
            dict: Contact data dictionary
        """
        default_exclude = ['verification_token']
        if exclude:
            default_exclude.extend(exclude)
        
        data = super().to_dict(exclude=default_exclude)
        
        # Add computed fields
        data['display_contact'] = self.display_contact
        data['contact_type_display'] = self.contact_type_display
        data['status_display'] = self.status_display
        data['display_name_with_relationship'] = self.display_name_with_relationship
        data['can_receive_notifications'] = self.can_receive_notifications()
        data['needs_verification'] = self.needs_verification()
        data['is_valid_format'] = (
            self.is_valid_email() if self.contact_type == ContactType.EMAIL 
            else self.is_valid_phone()
        )
        
        return data
    
    @staticmethod
    def get_supported_contact_types() -> List[str]:
        """Get list of supported contact types."""
        return [ct.value for ct in ContactType]
    
    @staticmethod
    def get_max_contacts_per_memorial() -> int:
        """Get maximum number of contacts allowed per memorial."""
        return 20  # Reasonable limit to prevent spam