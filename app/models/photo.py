"""
Photo model for Memorial Website.
Handles photo uploads, storage, and organization for memorial pages.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class Photo(BaseModel):
    """
    Photo model for memorial page images.
    
    Handles photo uploads, metadata, ordering, and relationships
    to memorial pages with support for up to 4 photos per memorial.
    """
    
    __tablename__ = "photos"
    
    # Memorial relationship
    memorial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memorials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the memorial this photo belongs to"
    )
    
    # File information
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Local file system path to the photo"
    )
    
    file_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Public URL to access the photo (CDN or static URL)"
    )
    
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original filename when uploaded"
    )
    
    # Photo type and metadata
    photo_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="memorial",
        comment="Type of photo: deceased, grave, memorial1, memorial2, memorial3, memorial4"
    )
    
    caption: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional caption or description for the photo"
    )
    
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Display order for photos (1-6)"
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes"
    )
    
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type of the photo (image/jpeg, image/png, etc.)"
    )
    
    # Image dimensions (if processed)
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Image width in pixels"
    )
    
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Image height in pixels"
    )
    
    # Photo settings
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is the primary/main photo for the memorial"
    )
    
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the photo is approved for display (content moderation)"
    )
    
    # Upload information
    uploaded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID of the user who uploaded this photo"
    )
    
    uploaded_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        comment="When the photo was uploaded"
    )
    
    # Processing status
    is_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the photo has been processed (resized, optimized, etc.)"
    )
    
    processing_error: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Error message if photo processing failed"
    )
    
    # Relationships
    memorial: Mapped["Memorial"] = relationship(
        "Memorial",
        back_populates="photos",
        lazy="select"
    )
    
    uploaded_by: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="select"
    )
    
    # Database constraints and indexes
    __table_args__ = (
        # Ensure display_order is between 1 and 6
        CheckConstraint(
            "display_order >= 1 AND display_order <= 6",
            name="ck_photo_display_order_range"
        ),
        
        # Ensure valid photo types
        CheckConstraint(
            "photo_type IN ('deceased', 'grave', 'memorial1', 'memorial2', 'memorial3', 'memorial4')",
            name="ck_photo_type_valid"
        ),
        
        # Ensure only positive file sizes
        CheckConstraint(
            "file_size > 0",
            name="ck_photo_file_size_positive"
        ),
        
        # Ensure positive dimensions
        CheckConstraint(
            "width > 0 AND height > 0",
            name="ck_photo_dimensions_positive"
        ),
        
        # Performance indexes
        Index("ix_photo_memorial_order", "memorial_id", "display_order"),
        Index("ix_photo_memorial_primary", "memorial_id", "is_primary"),
        Index("ix_photo_memorial_approved", "memorial_id", "is_approved"),
        Index("ix_photo_upload_date", "uploaded_at"),
        Index("ix_photo_processing", "is_processed", "processing_error", postgresql_where="is_processed = false"),
        
        # Unique constraint for primary photo per memorial
        Index(
            "ix_photo_memorial_primary_unique",
            "memorial_id",
            unique=True,
            postgresql_where="is_primary = true AND is_deleted = false"
        ),
        
        # Unique constraint for display order per memorial
        Index(
            "ix_photo_memorial_display_order_unique",
            "memorial_id", "display_order",
            unique=True,
            postgresql_where="is_deleted = false"
        ),
        
        # Unique constraint for deceased photo (max 1 per memorial)
        Index(
            "ix_photo_memorial_deceased_unique",
            "memorial_id",
            unique=True,
            postgresql_where="photo_type = 'deceased' AND is_deleted = false"
        ),
        
        # Unique constraint for grave photo (max 1 per memorial)
        Index(
            "ix_photo_memorial_grave_unique",
            "memorial_id",
            unique=True,
            postgresql_where="photo_type = 'grave' AND is_deleted = false"
        ),
        
        # Index for photo type filtering
        Index("ix_photo_memorial_type", "memorial_id", "photo_type"),
    )
    
    # File management methods
    def get_absolute_file_path(self) -> str:
        """
        Get the absolute file system path to the photo.
        
        Returns:
            str: Absolute path to the photo file
        """
        import os
        from app.core.config import get_settings
        
        settings = get_settings()
        if os.path.isabs(self.file_path):
            return self.file_path
        
        # Construct absolute path from upload directory
        return os.path.join(settings.UPLOAD_FOLDER, self.file_path)
    
    def get_public_url(self) -> str:
        """
        Get the public URL for accessing this photo.
        
        Returns:
            str: Public URL to the photo
        """
        if self.file_url:
            return self.file_url
        
        # Construct URL from file path
        from app.core.config import get_settings
        settings = get_settings()
        
        # Remove any leading path separators and construct URL
        clean_path = self.file_path.lstrip('/')
        return f"{settings.STATIC_URL}/uploads/{clean_path}"
    
    def generate_thumbnail_path(self, size: str = "150x150") -> str:
        """
        Generate path for thumbnail version of this photo.
        
        Args:
            size: Thumbnail size (e.g., "150x150")
            
        Returns:
            str: Path to thumbnail image
        """
        import os
        
        base_path, ext = os.path.splitext(self.file_path)
        return f"{base_path}_thumb_{size}{ext}"
    
    def get_thumbnail_url(self, size: str = "150x150") -> str:
        """
        Get URL for thumbnail version of this photo.
        
        Args:
            size: Thumbnail size (e.g., "150x150")
            
        Returns:
            str: URL to thumbnail image
        """
        thumbnail_path = self.generate_thumbnail_path(size)
        from app.core.config import get_settings
        settings = get_settings()
        
        clean_path = thumbnail_path.lstrip('/')
        return f"{settings.STATIC_URL}/uploads/{clean_path}"
    
    # Photo processing methods
    def mark_as_processed(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        """
        Mark photo as successfully processed.
        
        Args:
            width: Processed image width
            height: Processed image height
        """
        self.is_processed = True
        self.processing_error = None
        
        if width:
            self.width = width
        if height:
            self.height = height
    
    def mark_processing_failed(self, error_message: str) -> None:
        """
        Mark photo processing as failed.
        
        Args:
            error_message: Error description
        """
        self.is_processed = False
        self.processing_error = error_message
    
    def needs_processing(self) -> bool:
        """
        Check if photo needs processing.
        
        Returns:
            bool: True if photo needs processing
        """
        return not self.is_processed and not self.processing_error
    
    # Display and ordering methods
    def set_as_primary(self) -> None:
        """Set this photo as the primary photo for its memorial."""
        # Note: This should be handled at the service level to ensure
        # only one primary photo per memorial
        self.is_primary = True
    
    def unset_as_primary(self) -> None:
        """Unset this photo as primary."""
        self.is_primary = False
    
    def move_to_position(self, new_position: int) -> None:
        """
        Move photo to a new display position.
        
        Args:
            new_position: New display order (1-4)
        """
        if 1 <= new_position <= 4:
            self.display_order = new_position
        else:
            raise ValueError("Display order must be between 1 and 4")
    
    def can_be_deleted_by(self, user_id: uuid.UUID) -> bool:
        """
        Check if a user can delete this photo.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user can delete this photo
        """
        # User can delete if they own the memorial or uploaded the photo
        if self.memorial.owner_id == user_id:
            return True
        
        if self.uploaded_by_user_id == user_id:
            return True
        
        return False
    
    # Content validation
    def is_valid_image_type(self) -> bool:
        """
        Check if the photo has a valid image MIME type.
        
        Returns:
            bool: True if valid image type
        """
        valid_types = {
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/webp'
        }
        
        return self.mime_type in valid_types if self.mime_type else False
    
    def is_file_size_valid(self, max_size_mb: int = 10) -> bool:
        """
        Check if file size is within acceptable limits.
        
        Args:
            max_size_mb: Maximum file size in MB
            
        Returns:
            bool: True if file size is acceptable
        """
        if not self.file_size:
            return True  # Unknown size, assume valid
        
        max_size_bytes = max_size_mb * 1024 * 1024
        return self.file_size <= max_size_bytes
    
    # Display properties
    @hybrid_property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    @hybrid_property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate aspect ratio if dimensions are available."""
        if self.width and self.height:
            return self.width / self.height
        return None
    
    @hybrid_property
    def is_landscape(self) -> Optional[bool]:
        """Check if image is landscape orientation."""
        if self.aspect_ratio:
            return self.aspect_ratio > 1
        return None
    
    @hybrid_property
    def is_portrait(self) -> Optional[bool]:
        """Check if image is portrait orientation."""
        if self.aspect_ratio:
            return self.aspect_ratio < 1
        return None
    
    @hybrid_property
    def display_name(self) -> str:
        """Get display name for the photo."""
        if self.caption:
            return self.caption
        
        # Generate name based on photo type
        type_names = {
            'deceased': 'Deceased Photo',
            'grave': 'Grave Photo',
            'memorial1': 'Memorial Photo 1',
            'memorial2': 'Memorial Photo 2', 
            'memorial3': 'Memorial Photo 3',
            'memorial4': 'Memorial Photo 4'
        }
        
        return type_names.get(self.photo_type, f"Photo {self.display_order}")
    
    def __repr__(self) -> str:
        """String representation of photo."""
        return f"<Photo(id={self.id}, memorial_id={self.memorial_id}, order={self.display_order}, primary={self.is_primary})>"
    
    def to_dict(self, include_urls: bool = True, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert photo to dictionary.
        
        Args:
            include_urls: Whether to include computed URLs
            exclude: Fields to exclude
            
        Returns:
            dict: Photo data dictionary
        """
        data = super().to_dict(exclude=exclude)
        
        if include_urls:
            data['public_url'] = self.get_public_url()
            data['thumbnail_url'] = self.get_thumbnail_url()
        
        # Add computed fields
        data['file_size_mb'] = self.file_size_mb
        data['aspect_ratio'] = self.aspect_ratio
        data['is_landscape'] = self.is_landscape
        data['is_portrait'] = self.is_portrait
        data['display_name'] = self.display_name
        data['is_valid_type'] = self.is_valid_image_type()
        data['is_size_valid'] = self.is_file_size_valid()
        
        return data
    
    @staticmethod
    def get_allowed_extensions() -> List[str]:
        """Get list of allowed file extensions."""
        return ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    @staticmethod
    def get_max_file_size_mb() -> int:
        """Get maximum allowed file size in MB."""
        return 10
    
    @staticmethod
    def get_max_photos_per_memorial() -> int:
        """Get maximum number of photos allowed per memorial."""
        return 6
    
    @staticmethod
    def get_valid_photo_types() -> List[str]:
        """Get list of valid photo types."""
        return ['deceased', 'grave', 'memorial1', 'memorial2', 'memorial3', 'memorial4']
    
    @staticmethod
    def get_photo_type_limits() -> dict:
        """Get maximum number of photos allowed for each type."""
        return {
            'deceased': 1,
            'grave': 1,
            'memorial1': 1,
            'memorial2': 1,
            'memorial3': 1,
            'memorial4': 1
        }