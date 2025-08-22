"""
Notification model for Memorial Website.
Handles scheduling and tracking of memorial-related notifications.
"""

import enum
import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Index, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class NotificationType(enum.Enum):
    """Notification type enumeration."""
    YAHRZEIT_REMINDER = "yahrzeit_reminder"
    MEMORIAL_UPDATE = "memorial_update"
    SYSTEM = "system"
    WELCOME = "welcome"
    VERIFICATION_REMINDER = "verification_reminder"


class NotificationStatus(enum.Enum):
    """Notification status enumeration."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class Notification(BaseModel):
    """
    Notification model for managing memorial-related communications.
    
    Handles yahrzeit reminders, memorial updates, and system notifications
    with support for scheduling, retry logic, and delivery tracking.
    """
    
    __tablename__ = "notifications"
    
    # Memorial relationship (optional for system notifications)
    memorial_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memorials.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID of the memorial this notification relates to (optional for system notifications)"
    )
    
    # Contact relationship (optional for broadcast notifications)
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID of the specific contact to notify (optional for broadcast notifications)"
    )
    
    # User relationship (for user-specific notifications)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID of the user this notification is for (optional)"
    )
    
    # Notification details
    notification_type: Mapped[NotificationType] = mapped_column(
        nullable=False,
        index=True,
        comment="Type of notification"
    )
    
    status: Mapped[NotificationStatus] = mapped_column(
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current status of the notification"
    )
    
    # Scheduling
    scheduled_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Date when the notification should be sent"
    )
    
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Specific time when notification should be sent"
    )
    
    # Delivery tracking
    sent_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the notification was actually sent"
    )
    
    delivered_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the notification was delivered (if tracking available)"
    )
    
    opened_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the notification was opened (if tracking available)"
    )
    
    # Error handling and retry logic
    retry_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of retry attempts made"
    )
    
    max_retries: Mapped[int] = mapped_column(
        default=3,
        nullable=False,
        comment="Maximum number of retry attempts allowed"
    )
    
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When the next retry should be attempted"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if notification failed"
    )
    
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Error code for categorizing failures"
    )
    
    # Content
    subject: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Subject line for email notifications"
    )
    
    content: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Notification content as JSON (templates, variables, etc.)"
    )
    
    template_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Name of the template to use for rendering"
    )
    
    # Delivery channel
    delivery_channel: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Channel used for delivery (email, whatsapp, etc.)"
    )
    
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="External service ID for tracking (SendGrid message ID, etc.)"
    )
    
    # Priority and batching
    priority: Mapped[int] = mapped_column(
        default=5,
        nullable=False,
        comment="Priority level (1=highest, 10=lowest)"
    )
    
    batch_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="ID for grouping notifications into batches"
    )
    
    # Relationships
    memorial: Mapped[Optional["Memorial"]] = relationship(
        "Memorial",
        back_populates="notifications",
        lazy="select"
    )
    
    contact: Mapped[Optional["Contact"]] = relationship(
        "Contact",
        back_populates="notifications",
        lazy="select"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="select"
    )
    
    # Database constraints and indexes
    __table_args__ = (
        # Ensure valid priority range
        CheckConstraint(
            "priority >= 1 AND priority <= 10",
            name="ck_notification_priority_range"
        ),
        
        # Ensure non-negative retry counts
        CheckConstraint(
            "retry_count >= 0",
            name="ck_notification_retry_count_non_negative"
        ),
        
        CheckConstraint(
            "max_retries >= 0",
            name="ck_notification_max_retries_non_negative"
        ),
        
        # Performance indexes
        Index("ix_notification_status_type", "status", "notification_type"),
        Index("ix_notification_scheduled", "scheduled_date", "scheduled_time", postgresql_where="status IN ('pending', 'scheduled')"),
        Index("ix_notification_retry", "status", "next_retry_at", postgresql_where="status = 'retry'"),
        Index("ix_notification_memorial_type", "memorial_id", "notification_type"),
        Index("ix_notification_contact_status", "contact_id", "status"),
        Index("ix_notification_user_type", "user_id", "notification_type"),
        Index("ix_notification_batch", "batch_id", "status"),
        Index("ix_notification_priority_pending", "priority", "created_at", postgresql_where="status IN ('pending', 'scheduled')"),
        Index("ix_notification_delivery_tracking", "sent_date", "delivered_date", "opened_date"),
    )
    
    # Status management methods
    def mark_as_scheduled(self, scheduled_at: datetime) -> None:
        """
        Mark notification as scheduled for delivery.
        
        Args:
            scheduled_at: When to send the notification
        """
        self.status = NotificationStatus.SCHEDULED
        self.scheduled_time = scheduled_at
    
    def mark_as_sent(self, external_id: Optional[str] = None) -> None:
        """
        Mark notification as sent.
        
        Args:
            external_id: External service ID for tracking
        """
        self.status = NotificationStatus.SENT
        self.sent_date = datetime.utcnow()
        if external_id:
            self.external_id = external_id
        
        # Record delivery in contact if applicable
        if self.contact:
            self.contact.record_notification_sent()
    
    def mark_as_delivered(self) -> None:
        """Mark notification as delivered."""
        self.delivered_date = datetime.utcnow()
    
    def mark_as_opened(self) -> None:
        """Mark notification as opened/read."""
        self.opened_date = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str, error_code: Optional[str] = None) -> None:
        """
        Mark notification as failed.
        
        Args:
            error_message: Description of the error
            error_code: Error code for categorization
        """
        self.error_message = error_message
        self.error_code = error_code
        
        if self.retry_count < self.max_retries:
            self.schedule_retry()
        else:
            self.status = NotificationStatus.FAILED
            
            # Record bounce in contact if applicable
            if self.contact:
                self.contact.record_bounce()
    
    def schedule_retry(self, delay_minutes: int = None) -> None:
        """
        Schedule notification for retry.
        
        Args:
            delay_minutes: Minutes to wait before retry (auto-calculated if not provided)
        """
        from datetime import timedelta
        
        self.retry_count += 1
        self.status = NotificationStatus.RETRY
        
        if delay_minutes is None:
            # Exponential backoff: 5min, 30min, 2hr
            delay_map = {1: 5, 2: 30, 3: 120}
            delay_minutes = delay_map.get(self.retry_count, 120)
        
        self.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
    
    def cancel_notification(self, reason: Optional[str] = None) -> None:
        """
        Cancel the notification.
        
        Args:
            reason: Optional reason for cancellation
        """
        self.status = NotificationStatus.CANCELLED
        if reason:
            self.error_message = f"Cancelled: {reason}"
    
    # Query methods
    def is_ready_to_send(self) -> bool:
        """
        Check if notification is ready to be sent.
        
        Returns:
            bool: True if ready to send
        """
        if self.status not in [NotificationStatus.PENDING, NotificationStatus.SCHEDULED, NotificationStatus.RETRY]:
            return False
        
        now = datetime.utcnow()
        
        # Check if scheduled time has arrived
        if self.scheduled_time and now < self.scheduled_time:
            return False
        
        # Check retry timing
        if self.status == NotificationStatus.RETRY and self.next_retry_at and now < self.next_retry_at:
            return False
        
        return True
    
    def can_be_retried(self) -> bool:
        """
        Check if notification can be retried.
        
        Returns:
            bool: True if can be retried
        """
        return (
            self.status == NotificationStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    # Content management
    def set_content(self, content: Dict[str, Any]) -> None:
        """
        Set notification content.
        
        Args:
            content: Content dictionary
        """
        self.content = content
    
    def get_content_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the content JSON.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from content or default
        """
        if not self.content:
            return default
        return self.content.get(key, default)
    
    def update_content(self, updates: Dict[str, Any]) -> None:
        """
        Update specific content values.
        
        Args:
            updates: Dictionary of values to update
        """
        if not self.content:
            self.content = {}
        self.content.update(updates)
    
    # Template and rendering
    def get_template_variables(self) -> Dict[str, Any]:
        """
        Get variables for template rendering.
        
        Returns:
            dict: Template variables
        """
        variables = self.content.copy() if self.content else {}
        
        # Add common variables
        variables.update({
            'notification_id': str(self.id),
            'created_at': self.created_at,
            'scheduled_date': self.scheduled_date,
        })
        
        # Add memorial-specific variables
        if self.memorial:
            variables.update({
                'memorial_name': self.memorial.deceased_name_hebrew,
                'memorial_name_english': self.memorial.deceased_name_english,
                'memorial_url': self.memorial.public_url,
                'yahrzeit_date': self.memorial.next_yahrzeit_gregorian,
            })
        
        # Add contact-specific variables
        if self.contact:
            variables.update({
                'contact_name': self.contact.contact_name,
                'contact_relationship': self.contact.relationship,
            })
        
        return variables
    
    # Display properties
    @hybrid_property
    def display_type(self) -> str:
        """Get display name for notification type."""
        type_names = {
            NotificationType.YAHRZEIT_REMINDER: "Yahrzeit Reminder",
            NotificationType.MEMORIAL_UPDATE: "Memorial Update",
            NotificationType.SYSTEM: "System Notification",
            NotificationType.WELCOME: "Welcome Message",
            NotificationType.VERIFICATION_REMINDER: "Verification Reminder",
        }
        return type_names.get(self.notification_type, self.notification_type.value)
    
    @hybrid_property
    def display_status(self) -> str:
        """Get display name for status."""
        status_names = {
            NotificationStatus.PENDING: "Pending",
            NotificationStatus.SCHEDULED: "Scheduled",
            NotificationStatus.SENT: "Sent",
            NotificationStatus.FAILED: "Failed",
            NotificationStatus.CANCELLED: "Cancelled",
            NotificationStatus.RETRY: "Retrying",
        }
        return status_names.get(self.status, self.status.value)
    
    @hybrid_property
    def is_delivered(self) -> bool:
        """Check if notification was delivered."""
        return self.delivered_date is not None
    
    @hybrid_property
    def is_opened(self) -> bool:
        """Check if notification was opened."""
        return self.opened_date is not None
    
    @hybrid_property
    def delivery_time_seconds(self) -> Optional[int]:
        """Calculate delivery time in seconds if both sent and delivered."""
        if self.sent_date and self.delivered_date:
            delta = self.delivered_date - self.sent_date
            return int(delta.total_seconds())
        return None
    
    def __repr__(self) -> str:
        """String representation of notification."""
        return f"<Notification(id={self.id}, type={self.notification_type.value}, status={self.status.value}, memorial_id={self.memorial_id})>"
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert notification to dictionary.
        
        Args:
            exclude: Fields to exclude
            
        Returns:
            dict: Notification data dictionary
        """
        data = super().to_dict(exclude=exclude)
        
        # Add computed fields
        data['display_type'] = self.display_type
        data['display_status'] = self.display_status
        data['is_ready_to_send'] = self.is_ready_to_send()
        data['can_be_retried'] = self.can_be_retried()
        data['is_delivered'] = self.is_delivered
        data['is_opened'] = self.is_opened
        data['delivery_time_seconds'] = self.delivery_time_seconds
        
        return data
    
    @staticmethod
    def get_notification_types() -> List[str]:
        """Get list of available notification types."""
        return [nt.value for nt in NotificationType]
    
    @staticmethod
    def get_notification_statuses() -> List[str]:
        """Get list of available notification statuses."""
        return [ns.value for ns in NotificationStatus]