"""
QR Memorial models for Memorial Website.
Handles QR code generation, tracking, and manufacturing partner integration.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Index, DECIMAL, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class QROrderStatus(PyEnum):
    """Order status for QR memorial aluminum pieces."""
    PENDING = "pending"
    MANUFACTURING = "manufacturing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class QRDesignTemplate(PyEnum):
    """Available QR code design templates."""
    STANDARD = "standard"
    HEBREW_BORDER = "hebrew_border"
    ELEGANT = "elegant"
    CUSTOM = "custom"


class QRMemorialCode(BaseModel):
    """
    QR Memorial Code model representing QR codes for memorial pages.
    
    Links memorial pages to QR codes and tracks manufacturing/ordering details.
    """
    
    __tablename__ = "qr_memorial_codes"
    
    # Memorial relationship
    memorial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memorials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the memorial this QR code belongs to"
    )
    
    # QR Code data
    qr_code_data: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual URL/data encoded in the QR code"
    )
    
    qr_code_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full URL that the QR code resolves to"
    )
    
    qr_image_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="File path to generated QR code image"
    )
    
    # Design and customization
    design_template: Mapped[str] = mapped_column(
        String(50),
        default=QRDesignTemplate.STANDARD.value,
        nullable=False,
        comment="Design template used for QR code"
    )
    
    custom_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Custom message to display with QR code"
    )
    
    # Status and activation
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the QR code is active and scannable"
    )
    
    activation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the QR code was activated"
    )
    
    expiration_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the QR code expires (optional)"
    )
    
    # Manufacturing and ordering
    manufacturing_partner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("manufacturing_partners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID of manufacturing partner for aluminum piece"
    )
    
    aluminum_piece_order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Partner's order ID for tracking"
    )
    
    order_status: Mapped[str] = mapped_column(
        String(20),
        default=QROrderStatus.PENDING.value,
        nullable=False,
        index=True,
        comment="Current status of aluminum piece order"
    )
    
    order_placed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the aluminum piece order was placed"
    )
    
    shipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the aluminum piece was shipped"
    )
    
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the aluminum piece was delivered"
    )
    
    # Pricing and subscription
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        default="basic",
        nullable=False,
        comment="QR subscription tier (basic, premium)"
    )
    
    annual_fee_cents: Mapped[int] = mapped_column(
        Integer,
        default=1800,  # $18.00
        nullable=False,
        comment="Annual QR service fee in cents"
    )
    
    next_billing_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Next billing date for QR service"
    )
    
    # Analytics summary (for quick access)
    total_scans: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of QR code scans"
    )
    
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the QR code was last scanned"
    )
    
    # Relationships
    memorial: Mapped["Memorial"] = relationship(
        "Memorial",
        back_populates="qr_code",
        lazy="select"
    )
    
    manufacturing_partner: Mapped[Optional["ManufacturingPartner"]] = relationship(
        "ManufacturingPartner",
        back_populates="qr_orders",
        lazy="select"
    )
    
    scan_events: Mapped[List["QRScanEvent"]] = relationship(
        "QRScanEvent",
        back_populates="qr_code",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="QRScanEvent.scanned_at.desc()"
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("ix_qr_memorial_active", "memorial_id", "is_active"),
        Index("ix_qr_order_status", "order_status", "order_placed_at"),
        Index("ix_qr_billing", "next_billing_date", "subscription_tier"),
        Index("ix_qr_analytics", "total_scans", "last_scan_at"),
    )
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if QR code is expired."""
        if not self.expiration_date:
            return False
        return datetime.utcnow() > self.expiration_date
    
    @hybrid_property
    def order_status_display(self) -> str:
        """Get human-readable order status."""
        status_display = {
            QROrderStatus.PENDING.value: "Pending Order",
            QROrderStatus.MANUFACTURING.value: "In Production", 
            QROrderStatus.SHIPPED.value: "Shipped",
            QROrderStatus.DELIVERED.value: "Delivered",
            QROrderStatus.CANCELLED.value: "Cancelled"
        }
        return status_display.get(self.order_status, self.order_status.title())
    
    @hybrid_property
    def annual_fee_dollars(self) -> float:
        """Get annual fee in dollars."""
        return self.annual_fee_cents / 100.0
    
    def generate_qr_url(self, base_url: str = "https://memorial.com") -> str:
        """
        Generate the URL that the QR code should resolve to.
        
        Args:
            base_url: Base URL for the memorial site
            
        Returns:
            str: Full URL with tracking parameters
        """
        memorial_slug = self.memorial.unique_slug if self.memorial else "unknown"
        return f"{base_url}/memorial/{memorial_slug}?source=qr&code={str(self.id)}"
    
    def activate(self) -> None:
        """Activate the QR code."""
        self.is_active = True
        self.activation_date = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the QR code."""
        self.is_active = False
    
    def update_scan_count(self) -> None:
        """Update scan analytics (called when QR is scanned)."""
        self.total_scans += 1
        self.last_scan_at = datetime.utcnow()
    
    def update_order_status(self, new_status: QROrderStatus, tracking_info: Optional[dict] = None) -> None:
        """
        Update aluminum piece order status.
        
        Args:
            new_status: New order status
            tracking_info: Optional tracking information from partner
        """
        self.order_status = new_status.value
        
        current_time = datetime.utcnow()
        
        if new_status == QROrderStatus.MANUFACTURING and not self.order_placed_at:
            self.order_placed_at = current_time
        elif new_status == QROrderStatus.SHIPPED:
            self.shipped_at = current_time
        elif new_status == QROrderStatus.DELIVERED:
            self.delivered_at = current_time
    
    def can_be_managed_by(self, user_id: uuid.UUID) -> bool:
        """
        Check if a user can manage this QR code.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user can manage this QR code
        """
        return self.memorial and self.memorial.owner_id == user_id
    
    def __repr__(self) -> str:
        """String representation of QR code."""
        return f"<QRMemorialCode(id={self.id}, memorial_id={self.memorial_id}, active={self.is_active})>"


class QRScanEvent(BaseModel):
    """
    QR Scan Event model for tracking QR code usage analytics.
    
    Records each time a QR code is scanned with visitor information.
    """
    
    __tablename__ = "qr_scan_events"
    
    # QR Code relationship
    qr_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qr_memorial_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the QR code that was scanned"
    )
    
    # Scan timing
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the QR code was scanned"
    )
    
    # Visitor information (anonymized)
    visitor_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # Support IPv4 and IPv6
        nullable=True,
        comment="Visitor's IP address (anonymized for privacy)"
    )
    
    visitor_location_lat: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 8),
        nullable=True,
        comment="Visitor's approximate latitude"
    )
    
    visitor_location_lng: Mapped[Optional[float]] = mapped_column(
        DECIMAL(11, 8),
        nullable=True,
        comment="Visitor's approximate longitude"
    )
    
    visitor_country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Visitor's country (from IP geolocation)"
    )
    
    visitor_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Visitor's city (from IP geolocation)"
    )
    
    # Device and browser information
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Visitor's browser user agent string"
    )
    
    device_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Device type (mobile, tablet, desktop)"
    )
    
    browser_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Browser name (Chrome, Safari, etc.)"
    )
    
    operating_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Operating system (iOS, Android, Windows, etc.)"
    )
    
    # Engagement metrics
    session_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="How long visitor spent on memorial page"
    )
    
    pages_visited: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of pages visited in session"
    )
    
    bounce_rate: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if visitor left immediately (bounce)"
    )
    
    # Scan context
    scan_source: Mapped[str] = mapped_column(
        String(50),
        default="gravesite",
        nullable=False,
        comment="Where the QR code was scanned (gravesite, online, etc.)"
    )
    
    referrer_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="URL that referred the visitor (if any)"
    )
    
    # Privacy and compliance
    tracking_consent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether visitor consented to detailed tracking"
    )
    
    # Relationships
    qr_code: Mapped["QRMemorialCode"] = relationship(
        "QRMemorialCode",
        back_populates="scan_events",
        lazy="select"
    )
    
    # Database indexes for analytics
    __table_args__ = (
        Index("ix_scan_events_time", "scanned_at", "qr_code_id"),
        Index("ix_scan_events_location", "visitor_country", "visitor_city"),
        Index("ix_scan_events_device", "device_type", "browser_name"),
        Index("ix_scan_events_engagement", "session_duration_seconds", "pages_visited"),
        Index("ix_scan_events_source", "scan_source", "scanned_at"),
    )
    
    @hybrid_property
    def is_recent(self) -> bool:
        """Check if scan event is from the last 24 hours."""
        from datetime import timedelta
        return self.scanned_at and self.scanned_at > (datetime.utcnow() - timedelta(days=1))
    
    @hybrid_property
    def engagement_score(self) -> float:
        """Calculate engagement score based on session metrics."""
        score = 0.0
        
        # Base score for scanning
        score += 1.0
        
        # Duration bonus (max 3 points)
        if self.session_duration_seconds:
            duration_minutes = self.session_duration_seconds / 60.0
            score += min(duration_minutes * 0.5, 3.0)
        
        # Pages visited bonus (max 2 points)
        if self.pages_visited > 1:
            score += min((self.pages_visited - 1) * 0.5, 2.0)
        
        # Not a bounce bonus
        if not self.bounce_rate:
            score += 1.0
        
        return round(score, 2)
    
    def anonymize_visitor_data(self) -> None:
        """Anonymize visitor data for privacy compliance."""
        if self.visitor_ip:
            # Keep only first 3 octets for IPv4
            ip_parts = str(self.visitor_ip).split('.')
            if len(ip_parts) == 4:
                self.visitor_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0"
        
        # Keep only general location, remove precise coordinates
        if self.visitor_location_lat and self.visitor_location_lng:
            # Round to ~1km accuracy
            self.visitor_location_lat = round(float(self.visitor_location_lat), 2)
            self.visitor_location_lng = round(float(self.visitor_location_lng), 2)
        
        # Simplify user agent
        if self.user_agent and len(self.user_agent) > 200:
            self.user_agent = self.user_agent[:200] + "..."
    
    def __repr__(self) -> str:
        """String representation of scan event."""
        return f"<QRScanEvent(id={self.id}, qr_code_id={self.qr_code_id}, scanned_at={self.scanned_at})>"


class ManufacturingPartner(BaseModel):
    """
    Manufacturing Partner model for aluminum piece engraving companies.
    
    Manages partnerships with companies that create physical QR memorial pieces.
    """
    
    __tablename__ = "manufacturing_partners"
    
    # Company information
    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Company name"
    )
    
    contact_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Primary contact email"
    )
    
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Primary contact phone number"
    )
    
    website_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Company website URL"
    )
    
    # Capabilities and specialties
    specialties: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="Partner specialties (Hebrew, weather-resistant, etc.)"
    )
    
    supported_materials: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)),
        default=["aluminum"],
        comment="Supported materials for engraving"
    )
    
    minimum_order_quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Minimum order quantity"
    )
    
    maximum_order_quantity: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum order quantity (null for unlimited)"
    )
    
    # Pricing and terms
    base_price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Base price per unit in cents"
    )
    
    setup_fee_cents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="One-time setup fee in cents"
    )
    
    rush_order_fee_cents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Rush order additional fee in cents"
    )
    
    turnaround_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Standard turnaround time in days"
    )
    
    rush_turnaround_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Rush order turnaround time in days"
    )
    
    # Quality and performance metrics
    rating: Mapped[float] = mapped_column(
        DECIMAL(3, 2),
        default=0.00,
        nullable=False,
        comment="Average customer rating (0.00-5.00)"
    )
    
    total_orders: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of orders completed"
    )
    
    successful_orders: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of successfully completed orders"
    )
    
    average_delivery_days: Mapped[Optional[float]] = mapped_column(
        DECIMAL(4, 1),
        nullable=True,
        comment="Average actual delivery time in days"
    )
    
    # Status and activation
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether partner is currently accepting orders"
    )
    
    is_preferred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether partner is featured as preferred"
    )
    
    onboarded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When partner was onboarded"
    )
    
    last_order_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When last order was placed with partner"
    )
    
    # API integration
    api_webhook_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Webhook URL for order status updates"
    )
    
    api_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="API key for partner integration"
    )
    
    supports_api: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether partner supports API integration"
    )
    
    # Relationships
    qr_orders: Mapped[List["QRMemorialCode"]] = relationship(
        "QRMemorialCode",
        back_populates="manufacturing_partner",
        lazy="select"
    )
    
    # Database indexes for performance
    __table_args__ = (
        Index("ix_partner_active_rating", "is_active", "rating"),
        Index("ix_partner_preferred", "is_preferred", "rating"),
        Index("ix_partner_pricing", "base_price_cents", "turnaround_days"),
        Index("ix_partner_performance", "rating", "total_orders", "successful_orders"),
    )
    
    @hybrid_property
    def success_rate(self) -> float:
        """Calculate partner success rate percentage."""
        if self.total_orders == 0:
            return 0.0
        return round((self.successful_orders / self.total_orders) * 100, 1)
    
    @hybrid_property
    def base_price_dollars(self) -> float:
        """Get base price in dollars."""
        return self.base_price_cents / 100.0
    
    @hybrid_property
    def display_rating(self) -> str:
        """Get formatted rating display."""
        if self.rating == 0:
            return "No ratings yet"
        return f"{self.rating:.1f}/5.0 stars"
    
    def calculate_quote(self, quantity: int = 1, rush: bool = False) -> dict:
        """
        Calculate quote for an order.
        
        Args:
            quantity: Number of pieces to order
            rush: Whether this is a rush order
            
        Returns:
            dict: Quote details with pricing breakdown
        """
        if quantity < self.minimum_order_quantity:
            raise ValueError(f"Minimum order quantity is {self.minimum_order_quantity}")
        
        if self.maximum_order_quantity and quantity > self.maximum_order_quantity:
            raise ValueError(f"Maximum order quantity is {self.maximum_order_quantity}")
        
        # Calculate pricing
        unit_price = self.base_price_cents
        subtotal = unit_price * quantity
        setup_fee = self.setup_fee_cents if quantity > 0 else 0
        rush_fee = self.rush_order_fee_cents if rush else 0
        
        total = subtotal + setup_fee + rush_fee
        
        # Calculate delivery time
        delivery_days = self.rush_turnaround_days if rush and self.rush_turnaround_days else self.turnaround_days
        
        return {
            "quantity": quantity,
            "unit_price_cents": unit_price,
            "unit_price_dollars": unit_price / 100.0,
            "subtotal_cents": subtotal,
            "subtotal_dollars": subtotal / 100.0,
            "setup_fee_cents": setup_fee,
            "setup_fee_dollars": setup_fee / 100.0,
            "rush_fee_cents": rush_fee,
            "rush_fee_dollars": rush_fee / 100.0,
            "total_cents": total,
            "total_dollars": total / 100.0,
            "estimated_delivery_days": delivery_days,
            "rush_order": rush
        }
    
    def update_performance_metrics(self, successful: bool, delivery_days: int) -> None:
        """
        Update partner performance metrics after order completion.
        
        Args:
            successful: Whether the order was successful
            delivery_days: Actual delivery time in days
        """
        self.total_orders += 1
        if successful:
            self.successful_orders += 1
        
        # Update average delivery time
        if self.average_delivery_days is None:
            self.average_delivery_days = float(delivery_days)
        else:
            # Weighted average with more weight on recent orders
            weight = 0.2  # 20% weight for new order
            self.average_delivery_days = (
                (1 - weight) * float(self.average_delivery_days) + 
                weight * delivery_days
            )
        
        self.last_order_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of manufacturing partner."""
        return f"<ManufacturingPartner(id={self.id}, name={self.company_name}, rating={self.rating})>"