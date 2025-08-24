"""
Memorial model for Memorial Website.
Handles memorial pages with Hebrew/English dates, biography, and relationships.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional
from urllib.parse import quote_plus

from sqlalchemy import String, Text, Date, Boolean, Integer, ForeignKey, Index, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class Memorial(BaseModel):
    """
    Memorial model representing a memorial page for a deceased person.
    
    Handles both Hebrew and Gregorian dates, biography, media,
    and relationships to photos, contacts, and location data.
    """
    
    __tablename__ = "memorials"
    
    # Owner relationship
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the user who owns this memorial"
    )
    
    # Names (Hebrew and English)
    deceased_name_hebrew: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of the deceased in Hebrew"
    )
    
    deceased_name_english: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of the deceased in English (optional)"
    )
    
    parent_name_hebrew: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of parent (mother or father) in Hebrew"
    )
    
    # Family relationships (optional fields)
    spouse_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of spouse/husband/wife in Hebrew (optional)"
    )
    
    children_names: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Names of children in Hebrew (optional)"
    )
    
    parents_names: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="Names of both parents in Hebrew (optional)"
    )
    
    family_names: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Names of family members or family groups in Hebrew (optional)"
    )
    
    # Birth dates (both Gregorian and Hebrew)
    birth_date_gregorian: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Birth date in Gregorian calendar"
    )
    
    birth_date_hebrew: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Birth date in Hebrew calendar (formatted string)"
    )
    
    # Death dates (both Gregorian and Hebrew)
    death_date_gregorian: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Death date in Gregorian calendar"
    )
    
    death_date_hebrew: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Death date in Hebrew calendar (formatted string)"
    )
    
    # Yahrzeit information
    yahrzeit_date_hebrew: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Yahrzeit date in Hebrew calendar (11 months after death)"
    )
    
    next_yahrzeit_gregorian: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="Next yahrzeit date in Gregorian calendar for reminders"
    )
    
    # Biography and content
    biography: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Biography and life story of the deceased"
    )
    
    # Media
    memorial_song_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to memorial song or audio file"
    )
    
    # Page settings
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the memorial is locked from editing"
    )
    
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the memorial is publicly viewable"
    )
    
    enable_comments: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether memorial comments are enabled"
    )
    
    # Location information
    location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Location text (cemetery, address, etc.)"
    )
    
    location_lat: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Location latitude coordinate"
    )
    
    location_lng: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Location longitude coordinate"
    )
    
    # Contact fields for notifications (stored as JSON arrays)
    whatsapp_phones: Mapped[Optional[str]] = mapped_column(
        Text,  # Store as JSON string
        nullable=True,
        comment="WhatsApp phone numbers for notifications (JSON array)"
    )
    
    notification_emails: Mapped[Optional[str]] = mapped_column(
        Text,  # Store as JSON string
        nullable=True,
        comment="Email addresses for notifications (JSON array)"
    )
    
    # Analytics
    page_views: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times the memorial page has been viewed"
    )
    
    # URL slug for public access
    unique_slug: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Unique URL slug for public memorial page access"
    )
    
    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="memorials",
        lazy="select"
    )
    
    photos: Mapped[List["Photo"]] = relationship(
        "Photo",
        back_populates="memorial",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="Photo.display_order"
    )
    
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact",
        back_populates="memorial",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="memorial",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    location: Mapped[Optional["Location"]] = relationship(
        "Location",
        back_populates="memorial",
        lazy="select",
        cascade="all, delete-orphan",
        uselist=False
    )
    
    psalm_verses: Mapped[List["Psalm119Verse"]] = relationship(
        "Psalm119Verse",
        secondary="memorial_psalm_verses",
        lazy="select"
    )
    
    qr_code: Mapped[Optional["QRMemorialCode"]] = relationship(
        "QRMemorialCode",
        back_populates="memorial",
        lazy="select",
        cascade="all, delete-orphan",
        uselist=False
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("ix_memorial_owner_public", "owner_id", "is_public"),
        Index("ix_memorial_yahrzeit", "next_yahrzeit_gregorian", postgresql_where="next_yahrzeit_gregorian IS NOT NULL"),
        Index("ix_memorial_slug_public", "unique_slug", "is_public", postgresql_where="unique_slug IS NOT NULL"),
        Index("ix_memorial_name_search", "deceased_name_hebrew", "deceased_name_english"),
        Index("ix_memorial_death_date", "death_date_gregorian", postgresql_where="death_date_gregorian IS NOT NULL"),
    )
    
    
    # Slug generation and management
    def generate_unique_slug(self) -> str:
        """
        Generate a unique URL slug based on the deceased's name.
        
        Returns:
            str: Generated unique slug
        """
        import re
        from sqlalchemy import select
        from app.core.database import _session_factory
        
        # Use Hebrew name primarily, fallback to English
        base_name = self.deceased_name_hebrew or self.deceased_name_english or "memorial"
        
        # Create slug from name
        # Remove Hebrew characters and use transliteration or English name
        if self.deceased_name_english:
            slug_base = self.deceased_name_english.lower()
        else:
            # Use a simple Hebrew to English mapping or just use "memorial"
            slug_base = "memorial"
        
        # Clean up the slug
        slug_base = re.sub(r'[^\w\s-]', '', slug_base)
        slug_base = re.sub(r'[\s_-]+', '-', slug_base)
        slug_base = slug_base.strip('-')
        
        # Ensure we have something to work with
        if not slug_base:
            slug_base = "memorial"
        
        # Check for uniqueness and append number if needed
        original_slug = slug_base
        counter = 1
        
        # This would need to be done in a service layer with proper session management
        # For now, just return the base slug
        return slug_base[:50]  # Limit length
    
    def update_slug(self) -> None:
        """Update the memorial's unique slug."""
        if not self.unique_slug:
            self.unique_slug = self.generate_unique_slug()
    
    # Hebrew calendar integration
    def calculate_yahrzeit_date(self) -> None:
        """
        Calculate the yahrzeit date (11 months after death in Hebrew calendar).
        Updates yahrzeit_date_hebrew and next_yahrzeit_gregorian fields.
        """
        if not self.death_date_hebrew:
            return
        
        # This would integrate with Hebrew calendar service
        # For now, we'll set a placeholder
        # In actual implementation, this would use the HebrewCalendar service
        pass
    
    def update_next_yahrzeit(self) -> None:
        """Update the next yahrzeit date in Gregorian calendar for reminders."""
        if not self.yahrzeit_date_hebrew:
            return
        
        # This would convert Hebrew date to next Gregorian occurrence
        # For now, we'll set a placeholder
        pass
    
    # Content management
    def increment_page_views(self) -> None:
        """Increment the page view counter."""
        self.page_views += 1
    
    def can_be_edited_by(self, user_id: uuid.UUID) -> bool:
        """
        Check if a user can edit this memorial.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user can edit this memorial
        """
        if self.is_locked:
            return False
        return self.owner_id == user_id
    
    def lock_memorial(self, reason: Optional[str] = None) -> None:
        """
        Lock the memorial from editing.
        
        Args:
            reason: Optional reason for locking
        """
        self.is_locked = True
    
    def unlock_memorial(self) -> None:
        """Unlock the memorial for editing."""
        self.is_locked = False
    
    def make_private(self) -> None:
        """Make the memorial private (not publicly viewable)."""
        self.is_public = False
    
    def make_public(self) -> None:
        """Make the memorial publicly viewable."""
        self.is_public = True
    
    # Photo management
    def get_primary_photo(self) -> Optional["Photo"]:
        """
        Get the primary photo for this memorial.
        
        Returns:
            Photo or None: Primary photo if exists
        """
        for photo in self.photos:
            if photo.is_primary:
                return photo
        
        # If no primary photo set, return first photo
        return self.photos[0] if self.photos else None
    
    def set_primary_photo(self, photo_id: uuid.UUID) -> bool:
        """
        Set a photo as the primary photo for this memorial.
        
        Args:
            photo_id: ID of the photo to make primary
            
        Returns:
            bool: True if photo was found and set as primary
        """
        # First, unset all primary flags
        for photo in self.photos:
            photo.is_primary = False
        
        # Set the specified photo as primary
        for photo in self.photos:
            if photo.id == photo_id:
                photo.is_primary = True
                return True
        
        return False
    
    def get_display_photos(self, limit: int = 4) -> List["Photo"]:
        """
        Get photos for display, ordered by display_order.
        
        Args:
            limit: Maximum number of photos to return
            
        Returns:
            List of photos ordered by display_order
        """
        return sorted(
            [p for p in self.photos if not p.is_deleted],
            key=lambda x: x.display_order
        )[:limit]
    
    # Contact and notification management
    def get_notification_contacts(self) -> List["Contact"]:
        """
        Get all contacts that have notifications enabled.
        
        Returns:
            List of contacts with notifications enabled
        """
        return [c for c in self.contacts if c.notification_enabled and c.is_verified]
    
    # Display properties
    @hybrid_property
    def display_name(self) -> str:
        """Get the best display name for the memorial."""
        if self.deceased_name_english:
            return f"{self.deceased_name_hebrew} ({self.deceased_name_english})"
        return self.deceased_name_hebrew
    
    @hybrid_property
    def age_at_death(self) -> Optional[int]:
        """Calculate age at death if both birth and death dates are available."""
        if self.birth_date_gregorian and self.death_date_gregorian:
            delta = self.death_date_gregorian - self.birth_date_gregorian
            return delta.days // 365
        return None
    
    @hybrid_property
    def public_url(self) -> Optional[str]:
        """Get the public URL for this memorial if it has a slug."""
        if self.unique_slug and self.is_public:
            return f"/memorial/{self.unique_slug}"
        return None
    
    @hybrid_property
    def years_since_death(self) -> Optional[int]:
        """Calculate years since death."""
        if self.death_date_gregorian:
            delta = date.today() - self.death_date_gregorian
            return delta.days // 365
        return None
    
    def __repr__(self) -> str:
        """String representation of memorial."""
        return f"<Memorial(id={self.id}, name={self.deceased_name_hebrew}, owner_id={self.owner_id})>"
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert memorial to dictionary with computed fields.
        
        Args:
            exclude: Fields to exclude from output
            
        Returns:
            dict: Memorial data dictionary
        """
        data = super().to_dict(exclude=exclude)
        
        # Add computed fields
        data['display_name'] = self.display_name
        data['age_at_death'] = self.age_at_death
        data['public_url'] = self.public_url
        data['years_since_death'] = self.years_since_death
        
        # Family fields are already included in base to_dict since they're database columns
        
        # Handle primary photo safely without async calls
        primary_photo = self.get_primary_photo()
        data['primary_photo'] = primary_photo.to_dict() if primary_photo else None
        
        # Count photos and contacts safely
        data['photo_count'] = len([p for p in self.photos if not p.is_deleted]) if self.photos else 0
        data['contact_count'] = len([c for c in self.contacts if not c.is_deleted]) if self.contacts else 0
        
        # Add QR code information
        data['has_qr_code'] = bool(self.qr_code and self.qr_code.is_active)
        data['qr_code_data'] = self.qr_code.to_dict() if self.qr_code else None
        
        return data
    
    # QR Code management methods
    def has_active_qr_code(self) -> bool:
        """
        Check if this memorial has an active QR code.
        
        Returns:
            bool: True if memorial has active QR code
        """
        return bool(self.qr_code and self.qr_code.is_active and not self.qr_code.is_expired)
    
    def get_qr_url(self, base_url: str = "https://memorial.com") -> Optional[str]:
        """
        Get QR code URL for this memorial.
        
        Args:
            base_url: Base URL for the site
            
        Returns:
            str or None: QR URL if QR code exists and is active
        """
        if self.has_active_qr_code():
            return self.qr_code.generate_qr_url(base_url)
        return None
    
    def get_qr_analytics_summary(self) -> dict:
        """
        Get QR code analytics summary for this memorial.
        
        Returns:
            dict: Analytics summary with scan counts and recent activity
        """
        if not self.qr_code:
            return {
                "has_qr_code": False,
                "total_scans": 0,
                "recent_scans": 0,
                "last_scan_date": None
            }
        
        # Count recent scans (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_scans = len([
            scan for scan in self.qr_code.scan_events 
            if scan.scanned_at > thirty_days_ago
        ])
        
        return {
            "has_qr_code": True,
            "is_active": self.qr_code.is_active,
            "total_scans": self.qr_code.total_scans,
            "recent_scans": recent_scans,
            "last_scan_date": self.qr_code.last_scan_at,
            "order_status": self.qr_code.order_status_display,
            "subscription_tier": self.qr_code.subscription_tier
        }


# Association table for memorial-psalm verse many-to-many relationship
from sqlalchemy import Table, Column, ForeignKey

memorial_psalm_verses = Table(
    'memorial_psalm_verses',
    BaseModel.metadata,
    Column('memorial_id', UUID(as_uuid=True), ForeignKey('memorials.id', ondelete='CASCADE'), primary_key=True),
    Column('psalm_verse_id', Integer, ForeignKey('psalm_119_verses.id', ondelete='CASCADE'), primary_key=True),
    comment="Association table linking memorials to psalm verses"
)


# Event listeners for automatic slug generation
@event.listens_for(Memorial, 'before_insert')
def generate_slug_on_insert(mapper, connection, target):
    """Generate slug when creating a new memorial."""
    if not target.unique_slug:
        target.update_slug()


@event.listens_for(Memorial, 'before_update')
def update_yahrzeit_on_death_date_change(mapper, connection, target):
    """Update yahrzeit when death date changes."""
    if target.death_date_hebrew and not target.yahrzeit_date_hebrew:
        target.calculate_yahrzeit_date()