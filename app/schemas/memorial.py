"""
Memorial schemas for Memorial Website.
Pydantic models for memorial CRUD operations with validation and serialization.
"""

import re
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
try:
    from pydantic import HttpUrl
except ImportError:
    from pydantic.types import HttpUrl

from app.schemas.photo import PhotoResponse, PhotoCreate
from app.schemas.user import UserResponse


class MemorialBase(BaseModel):
    """
    Base memorial schema with common fields.
    """
    # Separate first and last names for validation
    hebrew_first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name of the deceased in Hebrew (required)"
    )
    hebrew_last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name of the deceased in Hebrew (required)"
    )
    english_first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="First name of the deceased in English (optional)"
    )
    english_last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Last name of the deceased in English (optional)"
    )
    
    # Parent name (required)
    parent_name_hebrew: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of parent (mother or father) in Hebrew"
    )
    
    # Family relationship fields (all optional)
    spouse_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Name of spouse/husband/wife in Hebrew (optional)"
    )
    
    children_names: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Names of children in Hebrew (optional)"
    )
    
    parents_names: Optional[str] = Field(
        None,
        min_length=1,
        max_length=300,
        description="Names of both parents in Hebrew (optional)"
    )
    
    family_names: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Names of family members or family groups in Hebrew (optional)"
    )
    
    # Combined names (can be provided or computed)
    deceased_name_hebrew: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Full Hebrew name (computed if not provided)"
    )
    deceased_name_english: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Full English name (computed if not provided)"
    )
    
    @model_validator(mode='after')
    def compute_full_names(self):
        """Compute full names if not provided."""
        # Compute Hebrew name if not provided
        if not self.deceased_name_hebrew and self.hebrew_first_name and self.hebrew_last_name:
            self.deceased_name_hebrew = f"{self.hebrew_first_name} {self.hebrew_last_name}".strip()
        
        # Compute English name if not provided
        if not self.deceased_name_english:
            if self.english_first_name and self.english_last_name:
                self.deceased_name_english = f"{self.english_first_name} {self.english_last_name}".strip()
            elif self.english_first_name:
                self.deceased_name_english = self.english_first_name.strip()
            elif self.english_last_name:
                self.deceased_name_english = self.english_last_name.strip()
        
        return self
    birth_date_gregorian: Optional[date] = Field(
        None,
        description="Birth date in Gregorian calendar"
    )
    birth_date_hebrew: Optional[str] = Field(
        None,
        max_length=50,
        description="Birth date in Hebrew calendar (formatted string)"
    )
    death_date_gregorian: Optional[date] = Field(
        None,
        description="Death date in Gregorian calendar"
    )
    death_date_hebrew: Optional[str] = Field(
        None,
        max_length=50,
        description="Death date in Hebrew calendar (formatted string)"
    )
    biography: Optional[str] = Field(
        None,
        max_length=10000,
        description="Biography and life story of the deceased"
    )
    memorial_song_url: Optional[HttpUrl] = Field(
        None,
        description="URL to memorial song or audio file"
    )
    is_public: bool = Field(
        True,
        description="Whether the memorial is publicly viewable"
    )
    enable_comments: bool = Field(
        False,
        description="Whether memorial comments are enabled"
    )
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="Location text (cemetery, address, etc.)"
    )
    location_lat: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Location latitude"
    )
    location_lng: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Location longitude"
    )
    
    # Contact fields for notifications
    whatsapp_phones: Optional[List[str]] = Field(
        None,
        max_items=5,
        description="WhatsApp phone numbers for notifications (up to 5)"
    )
    notification_emails: Optional[List[str]] = Field(
        None,
        max_items=5,
        description="Email addresses for notifications (up to 5)"
    )
    
    @field_validator('hebrew_first_name', 'hebrew_last_name', 'parent_name_hebrew')
    def validate_hebrew_names(cls, v):
        """Validate Hebrew first and last name format."""
        if not v or not v.strip():
            raise ValueError("Hebrew name is required")
        
        # Remove extra whitespace
        v = v.strip()
        
        # Basic Hebrew character validation (allow Hebrew, spaces, punctuation)
        if not re.match(r'^[\u0590-\u05FF\s\.,\-\'"()]+$', v):
            # If not purely Hebrew, allow mixed Hebrew-English for names
            if not re.match(r'^[\u0590-\u05FF\w\s\.,\-\'"()]+$', v):
                raise ValueError("Hebrew name contains invalid characters")
        
        return v
    
    @field_validator('spouse_name', 'children_names', 'parents_names', 'family_names')
    def validate_hebrew_family_fields(cls, v):
        """Validate Hebrew family name fields format."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            
            # Basic Hebrew character validation (allow Hebrew, spaces, punctuation, numbers for ages/dates)
            if not re.match(r'^[\u0590-\u05FF\w\s\.,\-\'"()0-9]+$', v):
                raise ValueError("Family field contains invalid characters - only Hebrew, letters, numbers, spaces and basic punctuation are allowed")
            
            # Remove excessive whitespace
            v = re.sub(r'\s+', ' ', v)
        
        return v
    
    @field_validator('english_first_name', 'english_last_name')
    def validate_english_names(cls, v):
        """Validate English first and last name format."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            
            # Allow English letters, spaces, and common punctuation
            if not re.match(r'^[a-zA-Z\s\.,\-\'"()]+$', v):
                raise ValueError("English name contains invalid characters")
        
        return v
    
    @field_validator('birth_date_gregorian', 'death_date_gregorian')
    def validate_dates(cls, v):
        """Validate Gregorian dates are reasonable."""
        if v is not None:
            # Must be in the past
            if v > date.today():
                raise ValueError("Date cannot be in the future")
            
            # Must be after year 1800 (reasonable range)
            if v.year < 1800:
                raise ValueError("Date must be after year 1800")
        
        return v
    
    @field_validator('birth_date_hebrew', 'death_date_hebrew')
    def validate_hebrew_dates(cls, v):
        """Validate Hebrew date strings."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            
            # Basic Hebrew date format validation
            # Expected format: "DD Month YYYY" (e.g., "15 Tishrei 5784")
            parts = v.split()
            if len(parts) < 2:
                raise ValueError("Hebrew date must include at least day and month")
            
            # First part should be a day number
            try:
                day = int(parts[0])
                if not 1 <= day <= 30:
                    raise ValueError("Day in Hebrew date must be between 1 and 30")
            except ValueError:
                raise ValueError("First part of Hebrew date must be a valid day number")
        
        return v
    
    @field_validator('biography')
    def validate_biography(cls, v):
        """Validate biography content."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            
            # Remove excessive whitespace
            v = re.sub(r'\s+', ' ', v)
            
            # Check for minimum meaningful content
            if len(v) < 10:
                raise ValueError("Biography must be at least 10 characters long")
        
        return v
    
    @field_validator('whatsapp_phones')
    def validate_whatsapp_phones(cls, v):
        """Validate WhatsApp phone numbers."""
        if v is None:
            return v
        
        import re
        for phone in v:
            if phone and not re.match(r'^\+?\d{8,15}$', phone.strip()):
                raise ValueError("Invalid WhatsApp phone number format")
        return [phone.strip() for phone in v if phone.strip()]
    
    @field_validator('notification_emails')
    def validate_notification_emails(cls, v):
        """Validate notification email addresses."""
        if v is None:
            return v
        
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        for email in v:
            if email and not email_pattern.match(email.strip()):
                raise ValueError("Invalid email address format")
        return [email.strip().lower() for email in v if email.strip()]
    
    @model_validator(mode='after')
    def validate_dates_consistency(self):
        """Validate date consistency."""
        birth_greg = self.birth_date_gregorian
        death_greg = self.death_date_gregorian
        
        # If both dates provided, death must be after birth
        if birth_greg and death_greg:
            if death_greg <= birth_greg:
                raise ValueError("Death date must be after birth date")
            
            # Check reasonable age range (0-150 years)
            age_days = (death_greg - birth_greg).days
            age_years = age_days / 365.25
            if age_years > 150:
                raise ValueError("Age at death seems unreasonable (over 150 years)")
        
        return self


class MemorialCreate(MemorialBase):
    """
    Schema for creating a new memorial.
    """
    pass


class MemorialUpdate(BaseModel):
    """
    Schema for updating an existing memorial.
    All fields are optional for partial updates.
    """
    hebrew_first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="First name of the deceased in Hebrew"
    )
    hebrew_last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Last name of the deceased in Hebrew"
    )
    english_first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="First name of the deceased in English"
    )
    english_last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Last name of the deceased in English"
    )
    
    # Parent name
    parent_name_hebrew: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name of parent (mother or father) in Hebrew"
    )
    
    # Family relationship fields (all optional)
    spouse_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Name of spouse/husband/wife in Hebrew (optional)"
    )
    
    children_names: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Names of children in Hebrew (optional)"
    )
    
    parents_names: Optional[str] = Field(
        None,
        min_length=1,
        max_length=300,
        description="Names of both parents in Hebrew (optional)"
    )
    
    family_names: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Names of family members or family groups in Hebrew (optional)"
    )
    
    # Combined names (can be provided or computed)
    deceased_name_hebrew: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Full Hebrew name (computed if not provided)"
    )
    deceased_name_english: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Full English name (computed if not provided)"
    )
    birth_date_gregorian: Optional[date] = Field(
        None,
        description="Birth date in Gregorian calendar"
    )
    birth_date_hebrew: Optional[str] = Field(
        None,
        max_length=50,
        description="Birth date in Hebrew calendar"
    )
    death_date_gregorian: Optional[date] = Field(
        None,
        description="Death date in Gregorian calendar"
    )
    death_date_hebrew: Optional[str] = Field(
        None,
        max_length=50,
        description="Death date in Hebrew calendar"
    )
    biography: Optional[str] = Field(
        None,
        max_length=10000,
        description="Biography and life story"
    )
    memorial_song_url: Optional[HttpUrl] = Field(
        None,
        description="URL to memorial song or audio file"
    )
    is_public: Optional[bool] = Field(
        None,
        description="Whether the memorial is publicly viewable"
    )
    enable_comments: Optional[bool] = Field(
        None,
        description="Whether memorial comments are enabled"
    )
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="Location text (cemetery, address, etc.)"
    )
    location_lat: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Location latitude"
    )
    location_lng: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Location longitude"
    )
    
    # Contact fields for notifications
    whatsapp_phones: Optional[List[str]] = Field(
        None,
        max_items=5,
        description="WhatsApp phone numbers for notifications (up to 5)"
    )
    notification_emails: Optional[List[str]] = Field(
        None,
        max_items=5,
        description="Email addresses for notifications (up to 5)"
    )
    
    # Use the same validators as MemorialBase
    _validate_hebrew_names = field_validator('hebrew_first_name', 'hebrew_last_name', 'parent_name_hebrew')(MemorialBase.validate_hebrew_names)
    _validate_hebrew_family_fields = field_validator('spouse_name', 'children_names', 'parents_names', 'family_names')(MemorialBase.validate_hebrew_family_fields)
    _validate_english_names = field_validator('english_first_name', 'english_last_name')(MemorialBase.validate_english_names)
    _validate_dates = field_validator('birth_date_gregorian', 'death_date_gregorian')(MemorialBase.validate_dates)
    _validate_hebrew_dates = field_validator('birth_date_hebrew', 'death_date_hebrew')(MemorialBase.validate_hebrew_dates)
    _validate_biography = field_validator('biography')(MemorialBase.validate_biography)


class MemorialResponse(MemorialBase):
    """
    Schema for memorial responses with computed fields.
    """
    id: UUID = Field(..., description="Memorial unique identifier")
    owner_id: UUID = Field(..., description="Owner user ID")
    
    # Ensure all family fields are included in response
    parent_name_hebrew: str = Field(..., description="Name of parent (mother or father) in Hebrew")
    spouse_name: Optional[str] = Field(None, description="Name of spouse/husband/wife in Hebrew (optional)")
    children_names: Optional[str] = Field(None, description="Names of children in Hebrew (optional)")
    parents_names: Optional[str] = Field(None, description="Names of both parents in Hebrew (optional)")
    family_names: Optional[str] = Field(None, description="Names of family members or family groups in Hebrew (optional)")
    yahrzeit_date_hebrew: Optional[str] = Field(
        None,
        description="Yahrzeit date in Hebrew calendar"
    )
    next_yahrzeit_gregorian: Optional[date] = Field(
        None,
        description="Next yahrzeit date in Gregorian calendar"
    )
    is_locked: bool = Field(
        False,
        description="Whether the memorial is locked from editing"
    )
    page_views: int = Field(
        0,
        description="Number of page views"
    )
    unique_slug: Optional[str] = Field(
        None,
        description="Unique URL slug for public access"
    )
    
    # Computed fields
    display_name: str = Field(..., description="Best display name for memorial")
    age_at_death: Optional[int] = Field(
        None,
        description="Age at death in years"
    )
    public_url: Optional[str] = Field(
        None,
        description="Public URL for memorial page"
    )
    years_since_death: Optional[int] = Field(
        None,
        description="Years since death"
    )
    
    # Relationship counts
    photo_count: int = Field(0, description="Number of photos")
    contact_count: int = Field(0, description="Number of contacts")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class MemorialWithPhotos(MemorialResponse):
    """
    Memorial response with embedded photos.
    """
    photos: List[PhotoResponse] = Field(
        default_factory=list,
        description="Memorial photos"
    )
    primary_photo: Optional[PhotoResponse] = Field(
        None,
        description="Primary memorial photo"
    )


class MemorialWithOwner(MemorialResponse):
    """
    Memorial response with embedded owner information.
    """
    owner: UserResponse = Field(..., description="Memorial owner")


class PublicMemorialResponse(BaseModel):
    """
    Public memorial view schema (limited information).
    """
    id: UUID = Field(..., description="Memorial unique identifier")
    deceased_name_hebrew: str = Field(
        ...,
        description="Name of the deceased in Hebrew"
    )
    deceased_name_english: Optional[str] = Field(
        None,
        description="Name of the deceased in English"
    )
    birth_date_gregorian: Optional[date] = Field(
        None,
        description="Birth date in Gregorian calendar"
    )
    death_date_gregorian: Optional[date] = Field(
        None,
        description="Death date in Gregorian calendar"
    )
    biography: Optional[str] = Field(
        None,
        description="Biography and life story"
    )
    memorial_song_url: Optional[HttpUrl] = Field(
        None,
        description="Memorial song URL"
    )
    unique_slug: Optional[str] = Field(
        None,
        description="Unique URL slug"
    )
    
    # Computed fields
    display_name: str = Field(..., description="Display name")
    age_at_death: Optional[int] = Field(
        None,
        description="Age at death in years"
    )
    years_since_death: Optional[int] = Field(
        None,
        description="Years since death"
    )
    
    # Public photos only
    photos: List[PhotoResponse] = Field(
        default_factory=list,
        description="Public memorial photos"
    )
    primary_photo: Optional[PhotoResponse] = Field(
        None,
        description="Primary photo"
    )
    
    # Basic stats (no personal info)
    photo_count: int = Field(0, description="Number of photos")
    created_at: datetime = Field(..., description="Creation date")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class MemorialListResponse(BaseModel):
    """
    Paginated list of memorials.
    """
    items: List[MemorialResponse] = Field(
        default_factory=list,
        description="List of memorials"
    )
    total: int = Field(0, description="Total number of memorials")
    skip: int = Field(0, description="Number of items skipped")
    limit: int = Field(20, description="Maximum items per page")
    has_next: bool = Field(False, description="Whether there are more items")
    has_previous: bool = Field(False, description="Whether there are previous items")


class MemorialSearchRequest(BaseModel):
    """
    Memorial search parameters.
    """
    query: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Search query (name, biography)"
    )
    birth_year_from: Optional[int] = Field(
        None,
        ge=1800,
        le=2024,
        description="Birth year range start"
    )
    birth_year_to: Optional[int] = Field(
        None,
        ge=1800,
        le=2024,
        description="Birth year range end"
    )
    death_year_from: Optional[int] = Field(
        None,
        ge=1800,
        le=2024,
        description="Death year range start"
    )
    death_year_to: Optional[int] = Field(
        None,
        ge=1800,
        le=2024,
        description="Death year range end"
    )
    has_photos: Optional[bool] = Field(
        None,
        description="Filter by presence of photos"
    )
    is_public: Optional[bool] = Field(
        None,
        description="Filter by public visibility"
    )
    sort_by: str = Field(
        "created_at",
        regex="^(created_at|updated_at|deceased_name_hebrew|death_date_gregorian|page_views)$",
        description="Sort field"
    )
    sort_order: str = Field(
        "desc",
        regex="^(asc|desc)$",
        description="Sort order"
    )
    
    @model_validator(mode='after')
    def validate_year_ranges(self):
        """Validate year ranges are logical."""
        birth_from = self.birth_year_from
        birth_to = self.birth_year_to
        death_from = self.death_year_from
        death_to = self.death_year_to
        
        if birth_from and birth_to and birth_from > birth_to:
            raise ValueError("Birth year 'from' must be less than or equal to 'to'")
        
        if death_from and death_to and death_from > death_to:
            raise ValueError("Death year 'from' must be less than or equal to 'to'")
        
        return self


class MemorialSearchResponse(BaseModel):
    """
    Memorial search results.
    """
    items: List[MemorialResponse] = Field(
        default_factory=list,
        description="Search results"
    )
    total: int = Field(0, description="Total matching results")
    skip: int = Field(0, description="Results skipped")
    limit: int = Field(20, description="Results limit")
    query: Optional[str] = Field(None, description="Original search query")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Applied search filters"
    )
    search_time_ms: Optional[float] = Field(
        None,
        description="Search execution time in milliseconds"
    )


class MemorialPhotoRequest(BaseModel):
    """
    Request to add photo to memorial.
    """
    photo_create: PhotoCreate = Field(..., description="Photo creation data")
    is_primary: bool = Field(
        False,
        description="Set as primary photo"
    )
    display_order: Optional[int] = Field(
        None,
        ge=0,
        description="Display order (auto-assigned if not provided)"
    )


class MemorialStatsResponse(BaseModel):
    """
    Memorial statistics.
    """
    id: UUID = Field(..., description="Memorial ID")
    page_views: int = Field(0, description="Total page views")
    photo_count: int = Field(0, description="Number of photos")
    contact_count: int = Field(0, description="Number of contacts")
    notification_count: int = Field(0, description="Number of notifications")
    days_since_created: int = Field(0, description="Days since memorial created")
    next_yahrzeit_days: Optional[int] = Field(
        None,
        description="Days until next yahrzeit"
    )
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemorialSlugRequest(BaseModel):
    """
    Request to update memorial slug.
    """
    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        regex="^[a-z0-9-]+$",
        description="New URL slug (lowercase, numbers, hyphens only)"
    )


class MemorialSlugResponse(BaseModel):
    """
    Memorial slug update response.
    """
    id: UUID = Field(..., description="Memorial ID")
    old_slug: Optional[str] = Field(None, description="Previous slug")
    new_slug: str = Field(..., description="New slug")
    public_url: str = Field(..., description="New public URL")
    success: bool = Field(True, description="Update successful")


class MemorialVisibilityRequest(BaseModel):
    """
    Request to change memorial visibility.
    """
    is_public: bool = Field(..., description="New public visibility status")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for visibility change"
    )


class MemorialLockRequest(BaseModel):
    """
    Request to lock/unlock memorial.
    """
    is_locked: bool = Field(..., description="Lock status")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for lock status change"
    )


# Response schemas for API operations
class MemorialCreateResponse(BaseModel):
    """
    Response for memorial creation.
    """
    success: bool = Field(True, description="Operation successful")
    message: str = Field(..., description="Success message")
    memorial: MemorialResponse = Field(..., description="Created memorial")
    public_url: Optional[str] = Field(
        None,
        description="Public URL if memorial is public"
    )


class MemorialUpdateResponse(BaseModel):
    """
    Response for memorial update.
    """
    success: bool = Field(True, description="Operation successful")
    message: str = Field(..., description="Success message")
    memorial: MemorialResponse = Field(..., description="Updated memorial")
    changes: List[str] = Field(
        default_factory=list,
        description="List of fields that were changed"
    )


class MemorialDeleteResponse(BaseModel):
    """
    Response for memorial deletion.
    """
    success: bool = Field(True, description="Operation successful")
    message: str = Field(..., description="Success message")
    memorial_id: UUID = Field(..., description="Deleted memorial ID")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Error schemas
class MemorialError(BaseModel):
    """
    Memorial operation error.
    """
    success: bool = Field(False, description="Operation failed")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    memorial_id: Optional[UUID] = Field(
        None,
        description="Memorial ID if applicable"
    )