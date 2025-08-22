"""
Photo schemas for Memorial Website.
Pydantic models for photo upload, management, and display.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator
from enum import Enum


class PhotoType(str, Enum):
    """Photo type enumeration."""
    DECEASED = "deceased"
    GRAVE = "grave"
    MEMORIAL1 = "memorial1"
    MEMORIAL2 = "memorial2"
    MEMORIAL3 = "memorial3"
    MEMORIAL4 = "memorial4"


class PhotoBase(BaseModel):
    """Base photo schema with common fields."""
    photo_type: PhotoType = Field(description="Type of photo")
    caption: Optional[str] = Field(None, max_length=500, description="Photo caption")
    display_order: int = Field(ge=1, le=6, description="Display order (1-6)")
    
    @validator('display_order')
    def validate_display_order(cls, v, values):
        """Validate display order based on photo type."""
        photo_type = values.get('photo_type')
        if photo_type == PhotoType.DECEASED and v != 1:
            raise ValueError("Deceased photo must have display_order = 1")
        elif photo_type == PhotoType.GRAVE and v != 2:
            raise ValueError("Grave photo must have display_order = 2")
        return v


class PhotoCreate(PhotoBase):
    """Schema for creating a new photo."""
    # File will be handled separately in the upload endpoint
    pass


class PhotoUpdate(BaseModel):
    """Schema for updating a photo."""
    caption: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = Field(None, ge=1, le=6)
    is_primary: Optional[bool] = None


class PhotoResponse(PhotoBase):
    """Schema for photo response."""
    id: UUID
    memorial_id: UUID
    file_path: str
    file_url: Optional[str] = None
    original_filename: str
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: Optional[str] = None
    is_primary: bool = False
    is_approved: bool = True
    is_processed: bool = False
    processing_error: Optional[str] = None
    uploaded_by_user_id: Optional[UUID] = None
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    public_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    display_name: str
    
    class Config:
        from_attributes = True


class PhotoListResponse(BaseModel):
    """Schema for photo list response."""
    photos: list[PhotoResponse]
    total: int


class PhotoUploadRequest(BaseModel):
    """Schema for photo upload request metadata."""
    photo_type: PhotoType = Field(description="Type of photo being uploaded")
    caption: Optional[str] = Field(None, max_length=500, description="Photo caption")


class PhotoUploadResponse(BaseModel):
    """Schema for photo upload response."""
    success: bool
    message: str
    photo: Optional[PhotoResponse] = None
    upload_id: Optional[str] = None


class PhotoDeleteResponse(BaseModel):
    """Schema for photo deletion response."""
    success: bool
    message: str
    photo_id: UUID
    deleted_at: datetime


class PhotoReorderRequest(BaseModel):
    """Schema for photo reordering request."""
    photo_id: UUID
    new_display_order: int = Field(ge=1, le=6)


class PhotoBatchUploadResponse(BaseModel):
    """Schema for batch photo upload response."""
    success: bool
    message: str
    uploaded_photos: list[PhotoResponse] = []
    failed_uploads: list[dict] = []
    total_uploaded: int = 0
    total_failed: int = 0