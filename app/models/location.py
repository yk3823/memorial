"""
Location model for Memorial Website.
Handles grave location information including cemetery details and GPS coordinates.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class Location(BaseModel):
    """
    Location model for storing grave and burial site information.
    
    Provides cemetery details, plot information, GPS coordinates,
    and navigation assistance for memorial sites.
    """
    
    __tablename__ = "locations"
    
    # Memorial relationship (one-to-one)
    memorial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memorials.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="ID of the memorial this location belongs to"
    )
    
    # Cemetery information
    cemetery_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Name of the cemetery or burial ground"
    )
    
    cemetery_address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Full address of the cemetery"
    )
    
    cemetery_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="City where the cemetery is located"
    )
    
    cemetery_country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Country where the cemetery is located"
    )
    
    # Plot location within cemetery
    section: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Section or area within the cemetery"
    )
    
    row: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Row identifier within the section"
    )
    
    plot: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific plot or grave number"
    )
    
    block: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Block identifier (if applicable)"
    )
    
    # GPS coordinates (using high precision for accurate location)
    gps_latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=7),
        nullable=True,
        comment="GPS latitude coordinate (decimal degrees)"
    )
    
    gps_longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=7),
        nullable=True,
        comment="GPS longitude coordinate (decimal degrees)"
    )
    
    gps_accuracy_meters: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="GPS accuracy in meters"
    )
    
    # Navigation and directions
    directions_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Written directions to find the grave"
    )
    
    directions_video_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to a video showing directions to the grave"
    )
    
    landmark_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of nearby landmarks or distinctive features"
    )
    
    # Grave details
    grave_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of grave (burial, mausoleum, columbarium, etc.)"
    )
    
    headstone_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the headstone or marker"
    )
    
    headstone_inscription: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Text inscription on the headstone"
    )
    
    # Administrative information
    burial_permit_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Official burial permit or certificate number"
    )
    
    plot_deed_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Plot deed or ownership document number"
    )
    
    # Maintenance and updates
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When the location information was last updated"
    )
    
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the location was last physically verified"
    )
    
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID of the user who verified this location"
    )
    
    # Relationships
    memorial: Mapped["Memorial"] = relationship(
        "Memorial",
        back_populates="location",
        lazy="select"
    )
    
    verified_by: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="select"
    )
    
    # Database constraints and indexes
    __table_args__ = (
        # Ensure valid GPS coordinates
        CheckConstraint(
            "gps_latitude >= -90 AND gps_latitude <= 90",
            name="ck_location_latitude_range"
        ),
        
        CheckConstraint(
            "gps_longitude >= -180 AND gps_longitude <= 180",
            name="ck_location_longitude_range"
        ),
        
        # Ensure positive GPS accuracy
        CheckConstraint(
            "gps_accuracy_meters > 0",
            name="ck_location_gps_accuracy_positive"
        ),
        
        # Performance indexes
        Index("ix_location_cemetery_name", "cemetery_name"),
        Index("ix_location_cemetery_city", "cemetery_city"),
        Index("ix_location_gps_coordinates", "gps_latitude", "gps_longitude", postgresql_where="gps_latitude IS NOT NULL AND gps_longitude IS NOT NULL"),
        Index("ix_location_plot_info", "section", "row", "plot"),
        Index("ix_location_last_updated", "last_updated_at"),
        Index("ix_location_verification", "verified_at", "verified_by_user_id"),
    )
    
    # GPS and coordinate methods
    def set_gps_coordinates(self, latitude: float, longitude: float, accuracy_meters: Optional[int] = None) -> None:
        """
        Set GPS coordinates for the location.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            accuracy_meters: GPS accuracy in meters
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees")
        
        self.gps_latitude = Decimal(str(latitude))
        self.gps_longitude = Decimal(str(longitude))
        
        if accuracy_meters is not None and accuracy_meters > 0:
            self.gps_accuracy_meters = accuracy_meters
        
        self.last_updated_at = datetime.utcnow()
    
    def has_gps_coordinates(self) -> bool:
        """
        Check if location has GPS coordinates.
        
        Returns:
            bool: True if both latitude and longitude are set
        """
        return self.gps_latitude is not None and self.gps_longitude is not None
    
    def get_gps_coordinates(self) -> Optional[tuple]:
        """
        Get GPS coordinates as a tuple.
        
        Returns:
            tuple: (latitude, longitude) or None if not set
        """
        if self.has_gps_coordinates():
            return (float(self.gps_latitude), float(self.gps_longitude))
        return None
    
    def calculate_distance_to(self, other_lat: float, other_lng: float) -> Optional[float]:
        """
        Calculate distance to another point using Haversine formula.
        
        Args:
            other_lat: Other point's latitude
            other_lng: Other point's longitude
            
        Returns:
            float: Distance in kilometers, or None if no GPS coordinates
        """
        if not self.has_gps_coordinates():
            return None
        
        import math
        
        # Convert to radians
        lat1_rad = math.radians(float(self.gps_latitude))
        lng1_rad = math.radians(float(self.gps_longitude))
        lat2_rad = math.radians(other_lat)
        lng2_rad = math.radians(other_lng)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        earth_radius_km = 6371
        
        return earth_radius_km * c
    
    # Plot location methods
    def set_plot_location(self, section: Optional[str] = None, row: Optional[str] = None, 
                         plot: Optional[str] = None, block: Optional[str] = None) -> None:
        """
        Set plot location information.
        
        Args:
            section: Cemetery section
            row: Row within section
            plot: Plot number
            block: Block identifier
        """
        self.section = section
        self.row = row
        self.plot = plot
        self.block = block
        self.last_updated_at = datetime.utcnow()
    
    def get_plot_identifier(self) -> Optional[str]:
        """
        Get formatted plot identifier string.
        
        Returns:
            str: Formatted plot location or None if no plot info
        """
        parts = []
        
        if self.section:
            parts.append(f"Section {self.section}")
        
        if self.block:
            parts.append(f"Block {self.block}")
        
        if self.row:
            parts.append(f"Row {self.row}")
        
        if self.plot:
            parts.append(f"Plot {self.plot}")
        
        return ", ".join(parts) if parts else None
    
    # Navigation methods
    def get_google_maps_url(self) -> Optional[str]:
        """
        Get Google Maps URL for the location.
        
        Returns:
            str: Google Maps URL or None if no coordinates
        """
        if self.has_gps_coordinates():
            lat = float(self.gps_latitude)
            lng = float(self.gps_longitude)
            return f"https://www.google.com/maps?q={lat},{lng}"
        return None
    
    def get_apple_maps_url(self) -> Optional[str]:
        """
        Get Apple Maps URL for the location.
        
        Returns:
            str: Apple Maps URL or None if no coordinates
        """
        if self.has_gps_coordinates():
            lat = float(self.gps_latitude)
            lng = float(self.gps_longitude)
            return f"https://maps.apple.com/?q={lat},{lng}"
        return None
    
    def get_waze_url(self) -> Optional[str]:
        """
        Get Waze navigation URL for the location.
        
        Returns:
            str: Waze URL or None if no coordinates
        """
        if self.has_gps_coordinates():
            lat = float(self.gps_latitude)
            lng = float(self.gps_longitude)
            return f"https://waze.com/ul?ll={lat},{lng}&navigate=yes"
        return None
    
    # Verification methods
    def mark_as_verified(self, user_id: uuid.UUID) -> None:
        """
        Mark location as verified by a user.
        
        Args:
            user_id: ID of the user verifying the location
        """
        self.verified_at = datetime.utcnow()
        self.verified_by_user_id = user_id
        self.last_updated_at = datetime.utcnow()
    
    def is_verified(self) -> bool:
        """
        Check if location has been verified.
        
        Returns:
            bool: True if location is verified
        """
        return self.verified_at is not None
    
    def needs_verification(self, days_threshold: int = 365) -> bool:
        """
        Check if location needs verification.
        
        Args:
            days_threshold: Days since last verification to consider stale
            
        Returns:
            bool: True if verification is needed
        """
        if not self.verified_at:
            return True
        
        from datetime import timedelta
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        return self.verified_at < threshold_date
    
    # Display properties
    @hybrid_property
    def full_cemetery_address(self) -> str:
        """Get full formatted cemetery address."""
        parts = [self.cemetery_name]
        
        if self.cemetery_address:
            parts.append(self.cemetery_address)
        elif self.cemetery_city:
            parts.append(self.cemetery_city)
        
        if self.cemetery_country and self.cemetery_country.lower() != 'israel':
            parts.append(self.cemetery_country)
        
        return ", ".join(parts)
    
    @hybrid_property
    def display_location(self) -> str:
        """Get display-friendly location description."""
        parts = [self.cemetery_name]
        
        plot_info = self.get_plot_identifier()
        if plot_info:
            parts.append(plot_info)
        
        return " - ".join(parts)
    
    @hybrid_property
    def has_navigation_info(self) -> bool:
        """Check if location has any navigation information."""
        return (
            self.has_gps_coordinates() or
            bool(self.directions_text) or
            bool(self.directions_video_url)
        )
    
    @hybrid_property
    def gps_precision_description(self) -> Optional[str]:
        """Get description of GPS precision."""
        if not self.gps_accuracy_meters:
            return None
        
        if self.gps_accuracy_meters <= 5:
            return "Very High Precision"
        elif self.gps_accuracy_meters <= 10:
            return "High Precision"
        elif self.gps_accuracy_meters <= 20:
            return "Good Precision"
        elif self.gps_accuracy_meters <= 50:
            return "Moderate Precision"
        else:
            return "Low Precision"
    
    def __repr__(self) -> str:
        """String representation of location."""
        return f"<Location(id={self.id}, memorial_id={self.memorial_id}, cemetery={self.cemetery_name})>"
    
    def to_dict(self, include_navigation_urls: bool = True, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert location to dictionary.
        
        Args:
            include_navigation_urls: Whether to include navigation URLs
            exclude: Fields to exclude
            
        Returns:
            dict: Location data dictionary
        """
        data = super().to_dict(exclude=exclude)
        
        # Add computed fields
        data['full_cemetery_address'] = self.full_cemetery_address
        data['display_location'] = self.display_location
        data['plot_identifier'] = self.get_plot_identifier()
        data['has_gps_coordinates'] = self.has_gps_coordinates()
        data['has_navigation_info'] = self.has_navigation_info
        data['is_verified'] = self.is_verified()
        data['needs_verification'] = self.needs_verification()
        data['gps_precision_description'] = self.gps_precision_description
        
        if include_navigation_urls and self.has_gps_coordinates():
            data['navigation_urls'] = {
                'google_maps': self.get_google_maps_url(),
                'apple_maps': self.get_apple_maps_url(),
                'waze': self.get_waze_url(),
            }
        
        # Convert GPS coordinates to float for JSON serialization
        if self.gps_latitude:
            data['gps_latitude'] = float(self.gps_latitude)
        if self.gps_longitude:
            data['gps_longitude'] = float(self.gps_longitude)
        
        return data
    
    @staticmethod
    def get_supported_grave_types() -> List[str]:
        """Get list of supported grave types."""
        return [
            "burial",
            "mausoleum", 
            "columbarium",
            "cremation_garden",
            "memorial_wall",
            "scattering_garden"
        ]