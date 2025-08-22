"""
Base model class with common fields for Memorial Website.
Provides UUID primary key, timestamps, and soft delete functionality.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class BaseModel(Base):
    """
    Abstract base model providing common fields for all models.
    
    Includes:
    - UUID primary key
    - Created/updated timestamps
    - Soft delete functionality
    """
    
    __abstract__ = True
    
    # Primary key using UUID for better security and distribution
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the record"
    )
    
    # Timestamp fields for audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Record creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
        comment="Record last update timestamp"
    )
    
    # Soft delete flag
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Soft delete flag - true if record is logically deleted"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        name = cls.__name__
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude: List of fields to exclude from output
            
        Returns:
            Dict representation of the model
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Convert UUID to string for JSON serialization
                if isinstance(value, uuid.UUID):
                    value = str(value)
                # Convert datetime to ISO format
                elif isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    def update(self, **kwargs) -> None:
        """
        Update model attributes.
        
        Args:
            **kwargs: Attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def soft_delete(self) -> None:
        """Mark record as deleted without actually removing it."""
        self.is_deleted = True
        self.updated_at = func.now()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.updated_at = func.now()
    
    @classmethod
    def get_active_query_filter(cls):
        """Get query filter for non-deleted records."""
        return cls.is_deleted == False
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.__repr__()


class TimestampMixin:
    """Mixin for models that only need timestamp fields."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )


class SoftDeleteMixin:
    """Mixin for models that need soft delete functionality."""
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Soft delete flag"
    )
    
    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.is_deleted = True
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
    
    @classmethod
    def get_active_filter(cls):
        """Get query filter for active records."""
        return cls.is_deleted == False