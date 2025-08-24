"""
Simplified Memorial schemas for Memorial Website.
Pydantic models without complex validators for basic functionality.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field
try:
    from pydantic import HttpUrl
except ImportError:
    from pydantic.types import HttpUrl

from app.schemas.photo import PhotoResponse
from app.schemas.user import UserResponse


class MemorialBase(BaseModel):
    """Base memorial schema with common fields."""
    deceased_name_hebrew: str = Field(..., min_length=1, max_length=255, description="Hebrew name is required")
    deceased_name_english: Optional[str] = Field(None, max_length=255)
    parent_name_hebrew: str = Field(..., min_length=1, max_length=100, description="Parent name in Hebrew is required")
    
    # Family relationship fields (all optional)
    spouse_name: Optional[str] = Field(None, max_length=200, description="Name of spouse/husband/wife in Hebrew (optional)")
    children_names: Optional[str] = Field(None, max_length=1000, description="Names of children in Hebrew (optional)")
    parents_names: Optional[str] = Field(None, max_length=300, description="Names of both parents in Hebrew (optional)")
    family_names: Optional[str] = Field(None, max_length=1000, description="Names of family members or family groups in Hebrew (optional)")
    
    birth_date_gregorian: Optional[date] = None
    birth_date_hebrew: Optional[str] = Field(None, max_length=50)
    death_date_gregorian: Optional[date] = None  # Made optional
    death_date_hebrew: Optional[str] = Field(None, max_length=50)
    biography: Optional[str] = Field(None, max_length=10000)
    memorial_song_url: Optional[HttpUrl] = None
    is_public: bool = Field(default=False)


class MemorialCreate(MemorialBase):
    """Schema for creating a new memorial."""
    pass


class MemorialUpdate(BaseModel):
    """Schema for updating a memorial."""
    deceased_name_hebrew: Optional[str] = Field(None, max_length=255)
    deceased_name_english: Optional[str] = Field(None, max_length=255)
    parent_name_hebrew: Optional[str] = Field(None, min_length=1, max_length=100)
    
    # Family relationship fields (all optional for updates)
    spouse_name: Optional[str] = Field(None, max_length=200, description="Name of spouse/husband/wife in Hebrew (optional)")
    children_names: Optional[str] = Field(None, max_length=1000, description="Names of children in Hebrew (optional)")
    parents_names: Optional[str] = Field(None, max_length=300, description="Names of both parents in Hebrew (optional)")
    family_names: Optional[str] = Field(None, max_length=1000, description="Names of family members or family groups in Hebrew (optional)")
    
    birth_date_gregorian: Optional[date] = None
    birth_date_hebrew: Optional[str] = Field(None, max_length=50)
    death_date_gregorian: Optional[date] = None
    death_date_hebrew: Optional[str] = Field(None, max_length=50)
    biography: Optional[str] = Field(None, max_length=10000)
    memorial_song_url: Optional[HttpUrl] = None
    is_public: Optional[bool] = None


class MemorialResponse(MemorialBase):
    """Schema for memorial response."""
    id: UUID
    owner_id: UUID
    yahrzeit_date_hebrew: Optional[str] = None
    next_yahrzeit_gregorian: Optional[date] = None
    unique_slug: str
    page_views: int = 0
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime
    display_name: Optional[str] = None
    age_at_death: Optional[int] = None
    public_url: Optional[str] = None
    years_since_death: Optional[int] = None
    photo_count: int = 0
    contact_count: int = 0
    
    # Relationships
    owner: Optional[UserResponse] = None
    photos: List[PhotoResponse] = []
    
    class Config:
        from_attributes = True


class PublicMemorialResponse(BaseModel):
    """Schema for public memorial view (limited fields)."""
    id: UUID
    owner_id: UUID
    deceased_name_hebrew: Optional[str]
    deceased_name_english: Optional[str]
    birth_date_gregorian: Optional[date]
    birth_date_hebrew: Optional[str]
    death_date_gregorian: Optional[date]
    death_date_hebrew: Optional[str]
    biography: Optional[str]
    memorial_song_url: Optional[HttpUrl]
    unique_slug: Optional[str]
    photos: List[PhotoResponse] = []
    yahrzeit_date_hebrew: Optional[str]
    next_yahrzeit_gregorian: Optional[date]
    page_views: int
    created_at: datetime
    updated_at: datetime
    is_locked: bool
    is_public: bool
    display_name: Optional[str]
    age_at_death: Optional[int]
    public_url: Optional[str]
    years_since_death: Optional[int]
    primary_photo: Optional[PhotoResponse] = None


class MemorialListResponse(BaseModel):
    """Schema for memorial list response."""
    items: List[MemorialResponse]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool


class MemorialSearchRequest(BaseModel):
    """Schema for memorial search request."""
    query: Optional[str] = None
    deceased_name_hebrew: Optional[str] = None
    deceased_name_english: Optional[str] = None
    birth_year_from: Optional[int] = None
    birth_year_to: Optional[int] = None
    death_year_from: Optional[int] = None
    death_year_to: Optional[int] = None
    is_public: Optional[bool] = None
    has_photos: Optional[bool] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at")
    sort_order: str = Field("desc")


class MemorialSearchResponse(BaseModel):
    """Schema for memorial search response."""
    items: List[MemorialResponse]
    total: int
    skip: int
    limit: int
    query: Optional[str] = None
    filters_applied: Dict[str, Any] = {}
    search_time_ms: float = 0.0


class MemorialStatsResponse(BaseModel):
    """Schema for memorial statistics response."""
    id: UUID
    page_views: int = 0
    photo_count: int = 0
    contact_count: int = 0
    notification_count: int = 0
    days_since_created: int = 0
    next_yahrzeit_days: Optional[int] = None
    last_updated: datetime


class MemorialSlugRequest(BaseModel):
    """Schema for memorial slug update request."""
    new_slug: str = Field(min_length=3, max_length=100)


class MemorialSlugResponse(BaseModel):
    """Schema for memorial slug update response."""
    memorial_id: UUID
    old_slug: str
    new_slug: str
    updated_at: datetime


class MemorialWithPhotos(MemorialResponse):
    """Schema for memorial response with photos included."""
    photos: List[PhotoResponse] = []
    primary_photo: Optional[PhotoResponse] = None


class MemorialVisibilityRequest(BaseModel):
    """Schema for memorial visibility update request."""
    is_public: bool


class MemorialLockRequest(BaseModel):
    """Schema for memorial lock request."""
    is_locked: bool
    lock_reason: Optional[str] = None


class MemorialCreateResponse(BaseModel):
    """Schema for memorial creation response."""
    success: bool
    message: str
    memorial: MemorialResponse
    public_url: Optional[str] = None


class MemorialUpdateResponse(BaseModel):
    """Schema for memorial update response."""
    success: bool
    message: str
    memorial: MemorialResponse
    changes: List[str] = []


class MemorialDeleteResponse(BaseModel):
    """Schema for memorial deletion response."""
    success: bool
    message: str
    memorial_id: UUID
    deleted_at: datetime


class MemorialError(BaseModel):
    """Schema for memorial error response."""
    success: bool = False
    error: str
    message: str