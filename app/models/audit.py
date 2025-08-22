"""
Audit model for Memorial Website.
Tracks all user actions for security and compliance.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class AuditLog(BaseModel):
    """
    Audit log model for tracking user actions.
    
    Stores detailed information about user activities for security,
    compliance, and debugging purposes.
    """
    
    __tablename__ = "audit_logs"
    
    # User information
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID of the user who performed the action"
    )
    
    user_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Email of the user who performed the action"
    )
    
    # Action details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of action performed (create, update, delete, etc.)"
    )
    
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of resource affected (user, memorial, photo, etc.)"
    )
    
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID of the affected resource"
    )
    
    # Request details
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        comment="IP address of the client"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User agent string from the client"
    )
    
    request_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Unique request identifier for correlation"
    )
    
    # Additional data
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional details about the action (JSON format)"
    )
    
    old_values: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Previous values before the action (for updates/deletes)"
    )
    
    new_values: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="New values after the action (for creates/updates)"
    )
    
    # Outcome
    success: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
        comment="Whether the action was successful"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if the action failed"
    )
    
    # Timing
    duration_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Duration of the action in milliseconds"
    )
    
    def __repr__(self) -> str:
        """String representation of audit log."""
        return f"<AuditLog(action='{self.action}', resource_type='{self.resource_type}', user_email='{self.user_email}')>"
    
    def to_dict(self) -> dict:
        """Convert audit log to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "user_email": self.user_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "ip_address": self.ip_address,
            "success": self.success,
            "created_at": self.created_at.isoformat(),
            "details": self.details,
        }