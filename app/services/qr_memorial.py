"""
QR Memorial service for Memorial Website.
Handles QR code generation, tracking, and manufacturing partner coordination.
"""

import logging
import uuid
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.models.memorial import Memorial
from app.models.qr_memorial import QRMemorialCode, QRScanEvent, ManufacturingPartner, QROrderStatus
from app.services.email import EmailService
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class QRMemorialService:
    """Service for managing QR memorial codes and tracking."""
    
    def __init__(self):
        self.settings = get_settings()
        self.email_service = EmailService()
        self.base_url = self.settings.SITE_BASE_URL or "https://memorial.com"
    
    async def generate_qr_code(
        self,
        db: AsyncSession,
        memorial_id: uuid.UUID,
        user_id: uuid.UUID,
        design_template: str = "standard",
        custom_message: Optional[str] = None,
        subscription_tier: str = "basic"
    ) -> QRMemorialCode:
        """
        Generate a QR code for a memorial.
        
        Args:
            db: Database session
            memorial_id: ID of memorial to generate QR for
            user_id: ID of user creating QR code
            design_template: Design template to use
            custom_message: Optional custom message
            subscription_tier: QR subscription tier
            
        Returns:
            QRMemorialCode: Created QR code record
            
        Raises:
            ValueError: If memorial not found or user doesn't own memorial
        """
        # Verify memorial exists and user owns it
        stmt = select(Memorial).where(
            Memorial.id == memorial_id,
            Memorial.owner_id == user_id,
            Memorial.is_deleted == False
        )
        result = await db.execute(stmt)
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise ValueError("Memorial not found or access denied")
        
        # Check if QR code already exists
        if memorial.qr_code:
            raise ValueError("Memorial already has a QR code")
        
        # Create QR code record
        qr_code = QRMemorialCode(
            memorial_id=memorial_id,
            design_template=design_template,
            custom_message=custom_message,
            subscription_tier=subscription_tier,
            qr_code_data="",  # Will be set after creation
            qr_code_url=""    # Will be set after creation
        )
        
        db.add(qr_code)
        await db.flush()  # Get the ID
        
        # Generate QR URL and data
        qr_url = self._generate_qr_url(memorial.unique_slug, str(qr_code.id))
        qr_code.qr_code_data = qr_url
        qr_code.qr_code_url = qr_url
        
        # Generate and save QR code image
        qr_image_path = await self._generate_qr_image(qr_url, str(qr_code.id))
        qr_code.qr_image_path = qr_image_path
        
        # Set billing date
        qr_code.next_billing_date = datetime.utcnow() + timedelta(days=365)
        
        # Activate QR code
        qr_code.activate()
        
        await db.commit()
        
        logger.info(f"QR code generated for memorial {memorial_id} by user {user_id}")
        
        return qr_code
    
    async def update_qr_code(
        self,
        db: AsyncSession,
        qr_code_id: uuid.UUID,
        user_id: uuid.UUID,
        **updates
    ) -> QRMemorialCode:
        """
        Update QR code settings.
        
        Args:
            db: Database session
            qr_code_id: ID of QR code to update
            user_id: ID of user making update
            **updates: Fields to update
            
        Returns:
            QRMemorialCode: Updated QR code record
        """
        # Get QR code with memorial
        stmt = select(QRMemorialCode).options(
            selectinload(QRMemorialCode.memorial)
        ).where(QRMemorialCode.id == qr_code_id)
        result = await db.execute(stmt)
        qr_code = result.scalar_one_or_none()
        
        if not qr_code:
            raise ValueError("QR code not found")
        
        if not qr_code.can_be_managed_by(user_id):
            raise ValueError("Access denied")
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(qr_code, field):
                setattr(qr_code, field, value)
        
        await db.commit()
        
        return qr_code
    
    async def deactivate_qr_code(
        self,
        db: AsyncSession,
        qr_code_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """
        Deactivate a QR code.
        
        Args:
            db: Database session
            qr_code_id: ID of QR code to deactivate
            user_id: ID of user requesting deactivation
            
        Returns:
            bool: True if deactivated successfully
        """
        stmt = select(QRMemorialCode).options(
            selectinload(QRMemorialCode.memorial)
        ).where(QRMemorialCode.id == qr_code_id)
        result = await db.execute(stmt)
        qr_code = result.scalar_one_or_none()
        
        if not qr_code:
            return False
        
        if not qr_code.can_be_managed_by(user_id):
            return False
        
        qr_code.deactivate()
        await db.commit()
        
        logger.info(f"QR code {qr_code_id} deactivated by user {user_id}")
        return True
    
    async def record_scan_event(
        self,
        db: AsyncSession,
        qr_code_id: uuid.UUID,
        visitor_data: Dict[str, Any]
    ) -> QRScanEvent:
        """
        Record a QR code scan event.
        
        Args:
            db: Database session
            qr_code_id: ID of QR code that was scanned
            visitor_data: Visitor information and context
            
        Returns:
            QRScanEvent: Created scan event record
        """
        # Verify QR code exists and is active
        stmt = select(QRMemorialCode).options(
            selectinload(QRMemorialCode.memorial)
        ).where(
            QRMemorialCode.id == qr_code_id,
            QRMemorialCode.is_active == True
        )
        result = await db.execute(stmt)
        qr_code = result.scalar_one_or_none()
        
        if not qr_code or qr_code.is_expired:
            raise ValueError("QR code not found or expired")
        
        # Create scan event
        scan_event = QRScanEvent(
            qr_code_id=qr_code_id,
            visitor_ip=visitor_data.get("ip"),
            visitor_location_lat=visitor_data.get("lat"),
            visitor_location_lng=visitor_data.get("lng"),
            visitor_country=visitor_data.get("country"),
            visitor_city=visitor_data.get("city"),
            user_agent=visitor_data.get("user_agent"),
            device_type=visitor_data.get("device_type"),
            browser_name=visitor_data.get("browser_name"),
            operating_system=visitor_data.get("operating_system"),
            scan_source=visitor_data.get("scan_source", "gravesite"),
            referrer_url=visitor_data.get("referrer_url"),
            tracking_consent=visitor_data.get("tracking_consent", False)
        )
        
        # Anonymize data if no tracking consent
        if not scan_event.tracking_consent:
            scan_event.anonymize_visitor_data()
        
        db.add(scan_event)
        
        # Update QR code scan count
        qr_code.update_scan_count()
        
        await db.commit()
        
        # Send notifications asynchronously
        await self._send_scan_notifications(qr_code, scan_event)
        
        logger.info(f"Scan recorded for QR code {qr_code_id}")
        
        return scan_event
    
    async def update_scan_engagement(
        self,
        db: AsyncSession,
        scan_event_id: uuid.UUID,
        session_duration_seconds: int,
        pages_visited: int = 1
    ) -> bool:
        """
        Update scan event with engagement metrics.
        
        Args:
            db: Database session
            scan_event_id: ID of scan event to update
            session_duration_seconds: How long visitor stayed
            pages_visited: Number of pages visited
            
        Returns:
            bool: True if updated successfully
        """
        stmt = select(QRScanEvent).where(QRScanEvent.id == scan_event_id)
        result = await db.execute(stmt)
        scan_event = result.scalar_one_or_none()
        
        if not scan_event:
            return False
        
        scan_event.session_duration_seconds = session_duration_seconds
        scan_event.pages_visited = pages_visited
        scan_event.bounce_rate = pages_visited == 1 and session_duration_seconds < 30
        
        await db.commit()
        
        return True
    
    async def get_qr_analytics(
        self,
        db: AsyncSession,
        memorial_id: uuid.UUID,
        user_id: uuid.UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get QR code analytics for a memorial.
        
        Args:
            db: Database session
            memorial_id: Memorial ID
            user_id: User ID (for authorization)
            days: Number of days to analyze
            
        Returns:
            dict: Analytics data
        """
        # Get memorial and QR code
        stmt = select(Memorial).options(
            selectinload(Memorial.qr_code).selectinload(QRMemorialCode.scan_events)
        ).where(
            Memorial.id == memorial_id,
            Memorial.owner_id == user_id
        )
        result = await db.execute(stmt)
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise ValueError("Memorial not found or access denied")
        
        if not memorial.qr_code:
            return {"has_qr_code": False}
        
        qr_code = memorial.qr_code
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter recent scan events
        recent_scans = [
            scan for scan in qr_code.scan_events
            if scan.scanned_at >= start_date
        ]
        
        # Calculate metrics
        total_scans = len(recent_scans)
        unique_visitors = len(set(scan.visitor_ip for scan in recent_scans if scan.visitor_ip))
        
        # Engagement metrics
        engaged_sessions = [scan for scan in recent_scans if scan.session_duration_seconds and scan.session_duration_seconds > 30]
        avg_session_duration = sum(scan.session_duration_seconds or 0 for scan in recent_scans) / max(total_scans, 1)
        bounce_rate = sum(1 for scan in recent_scans if scan.bounce_rate) / max(total_scans, 1) * 100
        
        # Geographic distribution
        countries = {}
        cities = {}
        for scan in recent_scans:
            if scan.visitor_country:
                countries[scan.visitor_country] = countries.get(scan.visitor_country, 0) + 1
            if scan.visitor_city:
                cities[scan.visitor_city] = cities.get(scan.visitor_city, 0) + 1
        
        # Device distribution
        devices = {}
        browsers = {}
        for scan in recent_scans:
            if scan.device_type:
                devices[scan.device_type] = devices.get(scan.device_type, 0) + 1
            if scan.browser_name:
                browsers[scan.browser_name] = browsers.get(scan.browser_name, 0) + 1
        
        # Daily scan distribution
        daily_scans = {}
        for scan in recent_scans:
            date_key = scan.scanned_at.date().isoformat()
            daily_scans[date_key] = daily_scans.get(date_key, 0) + 1
        
        return {
            "has_qr_code": True,
            "qr_code_id": str(qr_code.id),
            "is_active": qr_code.is_active,
            "total_scans_all_time": qr_code.total_scans,
            "period_days": days,
            "period_scans": total_scans,
            "unique_visitors": unique_visitors,
            "engagement": {
                "avg_session_duration_seconds": round(avg_session_duration, 1),
                "engaged_sessions": len(engaged_sessions),
                "bounce_rate_percent": round(bounce_rate, 1),
                "pages_per_session": sum(scan.pages_visited for scan in recent_scans) / max(total_scans, 1)
            },
            "geographic": {
                "countries": sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10],
                "cities": sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            "devices": {
                "device_types": sorted(devices.items(), key=lambda x: x[1], reverse=True),
                "browsers": sorted(browsers.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "timeline": {
                "daily_scans": daily_scans
            },
            "order_info": {
                "status": qr_code.order_status,
                "manufacturing_partner": qr_code.manufacturing_partner.company_name if qr_code.manufacturing_partner else None,
                "order_placed_at": qr_code.order_placed_at,
                "shipped_at": qr_code.shipped_at,
                "delivered_at": qr_code.delivered_at
            }
        }
    
    async def get_manufacturing_partners(
        self,
        db: AsyncSession,
        active_only: bool = True,
        preferred_first: bool = True
    ) -> List[ManufacturingPartner]:
        """
        Get list of manufacturing partners.
        
        Args:
            db: Database session
            active_only: Only return active partners
            preferred_first: Sort preferred partners first
            
        Returns:
            List of manufacturing partners
        """
        stmt = select(ManufacturingPartner)
        
        if active_only:
            stmt = stmt.where(ManufacturingPartner.is_active == True)
        
        if preferred_first:
            stmt = stmt.order_by(
                ManufacturingPartner.is_preferred.desc(),
                ManufacturingPartner.rating.desc(),
                ManufacturingPartner.company_name
            )
        else:
            stmt = stmt.order_by(
                ManufacturingPartner.rating.desc(),
                ManufacturingPartner.company_name
            )
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def place_aluminum_order(
        self,
        db: AsyncSession,
        qr_code_id: uuid.UUID,
        partner_id: uuid.UUID,
        user_id: uuid.UUID,
        quantity: int = 1,
        rush_order: bool = False
    ) -> Dict[str, Any]:
        """
        Place an order for aluminum QR pieces with manufacturing partner.
        
        Args:
            db: Database session
            qr_code_id: QR code to create aluminum piece for
            partner_id: Manufacturing partner ID
            user_id: User placing order
            quantity: Number of pieces to order
            rush_order: Whether this is a rush order
            
        Returns:
            dict: Order details and confirmation
        """
        # Get QR code and verify ownership
        stmt = select(QRMemorialCode).options(
            selectinload(QRMemorialCode.memorial)
        ).where(QRMemorialCode.id == qr_code_id)
        result = await db.execute(stmt)
        qr_code = result.scalar_one_or_none()
        
        if not qr_code or not qr_code.can_be_managed_by(user_id):
            raise ValueError("QR code not found or access denied")
        
        # Get manufacturing partner
        stmt = select(ManufacturingPartner).where(
            ManufacturingPartner.id == partner_id,
            ManufacturingPartner.is_active == True
        )
        result = await db.execute(stmt)
        partner = result.scalar_one_or_none()
        
        if not partner:
            raise ValueError("Manufacturing partner not found or inactive")
        
        # Calculate quote
        try:
            quote = partner.calculate_quote(quantity, rush_order)
        except ValueError as e:
            raise ValueError(f"Quote calculation failed: {e}")
        
        # Generate partner order ID
        order_id = f"QR-{qr_code.id.hex[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Update QR code with order information
        qr_code.manufacturing_partner_id = partner_id
        qr_code.aluminum_piece_order_id = order_id
        qr_code.update_order_status(QROrderStatus.PENDING)
        
        await db.commit()
        
        # Send order notification to partner (if they support webhooks)
        if partner.api_webhook_url:
            await self._notify_partner_new_order(partner, qr_code, quote)
        
        logger.info(f"Aluminum order placed: {order_id} with partner {partner.company_name}")
        
        return {
            "order_id": order_id,
            "partner_name": partner.company_name,
            "quote": quote,
            "estimated_delivery": f"{quote['estimated_delivery_days']} days",
            "order_status": "pending"
        }
    
    def _generate_qr_url(self, memorial_slug: str, qr_code_id: str) -> str:
        """Generate QR URL with tracking parameters."""
        return f"{self.base_url}/memorial/{memorial_slug}?source=qr&code={qr_code_id}"
    
    async def _generate_qr_image(self, qr_data: str, qr_code_id: str) -> str:
        """
        Generate QR code image and save to storage.
        
        Args:
            qr_data: Data to encode in QR code
            qr_code_id: Unique ID for filename
            
        Returns:
            str: Path to saved QR code image
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to storage directory
        storage_dir = Path("storage/qr_codes")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = storage_dir / f"{qr_code_id}.png"
        img.save(image_path)
        
        return str(image_path)
    
    async def _send_scan_notifications(
        self,
        qr_code: QRMemorialCode,
        scan_event: QRScanEvent
    ) -> None:
        """Send email notifications when QR code is scanned."""
        try:
            # Get memorial information
            memorial = qr_code.memorial
            
            # Prepare notification emails
            notification_emails = []
            
            # Add site administrator email
            if self.settings.ADMIN_EMAIL:
                notification_emails.append(self.settings.ADMIN_EMAIL)
            
            # Add manufacturing partner email
            if qr_code.manufacturing_partner:
                notification_emails.append(qr_code.manufacturing_partner.contact_email)
            
            # Prepare email content
            subject = f"QR Memorial Scan: {memorial.display_name}"
            
            scan_location = "Unknown location"
            if scan_event.visitor_city and scan_event.visitor_country:
                scan_location = f"{scan_event.visitor_city}, {scan_event.visitor_country}"
            elif scan_event.visitor_country:
                scan_location = scan_event.visitor_country
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">QR Memorial Code Scanned</h2>
                
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Memorial Information</h3>
                    <p><strong>Name:</strong> {memorial.display_name}</p>
                    <p><strong>Memorial URL:</strong> <a href="{qr_code.qr_code_url}">{qr_code.qr_code_url}</a></p>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Scan Details</h3>
                    <p><strong>Scanned at:</strong> {scan_event.scanned_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p><strong>Location:</strong> {scan_location}</p>
                    <p><strong>Device:</strong> {scan_event.device_type or 'Unknown'}</p>
                    <p><strong>Browser:</strong> {scan_event.browser_name or 'Unknown'}</p>
                </div>
                
                <div style="background-color: #fff3e0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">QR Code Analytics</h3>
                    <p><strong>Total Scans:</strong> {qr_code.total_scans}</p>
                    <p><strong>QR Code Status:</strong> {qr_code.order_status_display}</p>
                    <p><strong>Subscription Tier:</strong> {qr_code.subscription_tier.title()}</p>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This is an automated notification from the Memorial QR Code system.
                </p>
            </div>
            """
            
            # Send notifications
            for email in notification_emails:
                await self.email_service.send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_content
                )
            
            logger.info(f"Scan notifications sent for QR code {qr_code.id}")
            
        except Exception as e:
            logger.error(f"Failed to send scan notifications: {e}")
    
    async def _notify_partner_new_order(
        self,
        partner: ManufacturingPartner,
        qr_code: QRMemorialCode,
        quote: Dict[str, Any]
    ) -> None:
        """Send webhook notification to manufacturing partner about new order."""
        # This would implement webhook notification to partner
        # For now, just log the order details
        logger.info(f"New order notification for partner {partner.company_name}: {qr_code.aluminum_piece_order_id}")


def get_qr_memorial_service() -> QRMemorialService:
    """Get QR memorial service instance."""
    return QRMemorialService()