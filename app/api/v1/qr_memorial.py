"""
QR Memorial API endpoints for Memorial Website.
Handles QR code generation, tracking, and manufacturing partner integration.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.qr_memorial import QRMemorialCode, ManufacturingPartner
from app.services.qr_memorial import get_qr_memorial_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qr-memorial", tags=["qr-memorial"])


# Pydantic schemas for request/response
class QRCodeCreateRequest(BaseModel):
    """Request schema for creating QR code."""
    memorial_id: uuid.UUID
    design_template: str = Field(default="standard", description="QR design template")
    custom_message: Optional[str] = Field(None, description="Custom message for QR code")
    subscription_tier: str = Field(default="basic", description="Subscription tier (basic/premium)")


class QRCodeResponse(BaseModel):
    """Response schema for QR code data."""
    id: uuid.UUID
    memorial_id: uuid.UUID
    qr_code_url: str
    design_template: str
    custom_message: Optional[str]
    is_active: bool
    subscription_tier: str
    total_scans: int
    last_scan_at: Optional[datetime]
    order_status: str
    manufacturing_partner_name: Optional[str]
    created_at: datetime


class QRCodeUpdateRequest(BaseModel):
    """Request schema for updating QR code."""
    design_template: Optional[str] = None
    custom_message: Optional[str] = None
    subscription_tier: Optional[str] = None


class ScanEventRequest(BaseModel):
    """Request schema for recording scan events."""
    qr_code_id: uuid.UUID
    visitor_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Visitor information and context"
    )


class ScanEngagementRequest(BaseModel):
    """Request schema for updating scan engagement metrics."""
    scan_event_id: uuid.UUID
    session_duration_seconds: int
    pages_visited: int = 1


class ManufacturingPartnerResponse(BaseModel):
    """Response schema for manufacturing partner data."""
    id: uuid.UUID
    company_name: str
    specialties: List[str]
    base_price_dollars: float
    turnaround_days: int
    rating: float
    total_orders: int
    success_rate: float
    is_preferred: bool


class AluminumOrderRequest(BaseModel):
    """Request schema for placing aluminum piece orders."""
    qr_code_id: uuid.UUID
    partner_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=100)
    rush_order: bool = False


class QRAnalyticsResponse(BaseModel):
    """Response schema for QR analytics data."""
    has_qr_code: bool
    qr_code_id: Optional[uuid.UUID]
    is_active: bool
    total_scans_all_time: int
    period_days: int
    period_scans: int
    unique_visitors: int
    engagement: Dict[str, Any]
    geographic: Dict[str, Any]
    devices: Dict[str, Any]
    timeline: Dict[str, Any]
    order_info: Dict[str, Any]


@router.post("/generate", response_model=QRCodeResponse)
async def generate_qr_code(
    request: QRCodeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate QR code for a memorial.
    
    Creates a new QR code that links to the memorial page with tracking capabilities.
    Only the memorial owner can generate QR codes for their memorials.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        qr_code = await qr_service.generate_qr_code(
            db=db,
            memorial_id=request.memorial_id,
            user_id=current_user.id,
            design_template=request.design_template,
            custom_message=request.custom_message,
            subscription_tier=request.subscription_tier
        )
        
        return QRCodeResponse(
            id=qr_code.id,
            memorial_id=qr_code.memorial_id,
            qr_code_url=qr_code.qr_code_url,
            design_template=qr_code.design_template,
            custom_message=qr_code.custom_message,
            is_active=qr_code.is_active,
            subscription_tier=qr_code.subscription_tier,
            total_scans=qr_code.total_scans,
            last_scan_at=qr_code.last_scan_at,
            order_status=qr_code.order_status,
            manufacturing_partner_name=qr_code.manufacturing_partner.company_name if qr_code.manufacturing_partner else None,
            created_at=qr_code.created_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate QR code")


@router.get("/memorial/{memorial_id}", response_model=Optional[QRCodeResponse])
async def get_memorial_qr_code(
    memorial_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get QR code details for a memorial.
    
    Returns QR code information if it exists and user owns the memorial.
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.memorial import Memorial
        
        # Get memorial with QR code
        stmt = select(Memorial).options(
            selectinload(Memorial.qr_code).selectinload(QRMemorialCode.manufacturing_partner)
        ).where(
            Memorial.id == memorial_id,
            Memorial.owner_id == current_user.id
        )
        result = await db.execute(stmt)
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise HTTPException(status_code=404, detail="Memorial not found")
        
        if not memorial.qr_code:
            return None
        
        qr_code = memorial.qr_code
        
        return QRCodeResponse(
            id=qr_code.id,
            memorial_id=qr_code.memorial_id,
            qr_code_url=qr_code.qr_code_url,
            design_template=qr_code.design_template,
            custom_message=qr_code.custom_message,
            is_active=qr_code.is_active,
            subscription_tier=qr_code.subscription_tier,
            total_scans=qr_code.total_scans,
            last_scan_at=qr_code.last_scan_at,
            order_status=qr_code.order_status,
            manufacturing_partner_name=qr_code.manufacturing_partner.company_name if qr_code.manufacturing_partner else None,
            created_at=qr_code.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QR code: {e}")
        raise HTTPException(status_code=500, detail="Failed to get QR code")


@router.put("/{qr_code_id}", response_model=QRCodeResponse)
async def update_qr_code(
    qr_code_id: uuid.UUID,
    request: QRCodeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update QR code settings.
    
    Allows owners to modify QR code design template, custom message, and subscription tier.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        # Prepare updates dict (only include non-None values)
        updates = {}
        for field, value in request.dict().items():
            if value is not None:
                updates[field] = value
        
        qr_code = await qr_service.update_qr_code(
            db=db,
            qr_code_id=qr_code_id,
            user_id=current_user.id,
            **updates
        )
        
        return QRCodeResponse(
            id=qr_code.id,
            memorial_id=qr_code.memorial_id,
            qr_code_url=qr_code.qr_code_url,
            design_template=qr_code.design_template,
            custom_message=qr_code.custom_message,
            is_active=qr_code.is_active,
            subscription_tier=qr_code.subscription_tier,
            total_scans=qr_code.total_scans,
            last_scan_at=qr_code.last_scan_at,
            order_status=qr_code.order_status,
            manufacturing_partner_name=qr_code.manufacturing_partner.company_name if qr_code.manufacturing_partner else None,
            created_at=qr_code.created_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating QR code: {e}")
        raise HTTPException(status_code=500, detail="Failed to update QR code")


@router.delete("/{qr_code_id}")
async def deactivate_qr_code(
    qr_code_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Deactivate QR code.
    
    Deactivates the QR code so it no longer resolves to the memorial page.
    Only the memorial owner can deactivate QR codes.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        success = await qr_service.deactivate_qr_code(
            db=db,
            qr_code_id=qr_code_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="QR code not found or access denied")
        
        return {"message": "QR code deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating QR code: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate QR code")


@router.get("/image/{qr_code_id}")
async def get_qr_code_image(
    qr_code_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Get QR code image file.
    
    Returns the PNG image of the QR code for download or display.
    """
    try:
        from sqlalchemy import select
        
        # Get QR code
        stmt = select(QRMemorialCode).where(QRMemorialCode.id == qr_code_id)
        result = await db.execute(stmt)
        qr_code = result.scalar_one_or_none()
        
        if not qr_code or not qr_code.is_active:
            raise HTTPException(status_code=404, detail="QR code not found or inactive")
        
        # Check if user has access (owners can always access, others only if memorial is public)
        if current_user and qr_code.can_be_managed_by(current_user.id):
            # Owner access - always allowed
            pass
        elif not qr_code.memorial.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return image file
        if qr_code.qr_image_path and Path(qr_code.qr_image_path).exists():
            return FileResponse(
                qr_code.qr_image_path,
                media_type="image/png",
                filename=f"qr_memorial_{qr_code_id.hex[:8]}.png"
            )
        else:
            raise HTTPException(status_code=404, detail="QR code image not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QR code image: {e}")
        raise HTTPException(status_code=500, detail="Failed to get QR code image")


@router.post("/scan", status_code=201)
async def record_scan_event(
    request: ScanEventRequest,
    client_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Record QR code scan event.
    
    Called when a QR code is scanned to track analytics and send notifications.
    This endpoint is public as it's called by QR code scanners.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        # Extract visitor data from request
        visitor_data = request.visitor_data.copy()
        
        # Add request-based data
        visitor_data.update({
            "ip": str(client_request.client.host) if client_request.client else None,
            "user_agent": client_request.headers.get("user-agent"),
            "referrer_url": client_request.headers.get("referer"),
        })
        
        # Parse user agent for device info (basic implementation)
        user_agent = visitor_data.get("user_agent", "").lower()
        if "mobile" in user_agent:
            visitor_data["device_type"] = "mobile"
        elif "tablet" in user_agent:
            visitor_data["device_type"] = "tablet"
        else:
            visitor_data["device_type"] = "desktop"
        
        # Extract browser name
        if "chrome" in user_agent:
            visitor_data["browser_name"] = "Chrome"
        elif "firefox" in user_agent:
            visitor_data["browser_name"] = "Firefox"
        elif "safari" in user_agent:
            visitor_data["browser_name"] = "Safari"
        elif "edge" in user_agent:
            visitor_data["browser_name"] = "Edge"
        
        # Extract OS
        if "android" in user_agent:
            visitor_data["operating_system"] = "Android"
        elif "ios" in user_agent or "iphone" in user_agent or "ipad" in user_agent:
            visitor_data["operating_system"] = "iOS"
        elif "windows" in user_agent:
            visitor_data["operating_system"] = "Windows"
        elif "mac" in user_agent:
            visitor_data["operating_system"] = "macOS"
        
        scan_event = await qr_service.record_scan_event(
            db=db,
            qr_code_id=request.qr_code_id,
            visitor_data=visitor_data
        )
        
        return {
            "scan_event_id": scan_event.id,
            "message": "Scan recorded successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording scan event: {e}")
        raise HTTPException(status_code=500, detail="Failed to record scan event")


@router.put("/scan/{scan_event_id}/engagement")
async def update_scan_engagement(
    scan_event_id: uuid.UUID,
    request: ScanEngagementRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update scan event engagement metrics.
    
    Called via JavaScript on memorial pages to track how long visitors stayed
    and how many pages they viewed. This improves analytics accuracy.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        success = await qr_service.update_scan_engagement(
            db=db,
            scan_event_id=scan_event_id,
            session_duration_seconds=request.session_duration_seconds,
            pages_visited=request.pages_visited
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Scan event not found")
        
        return {"message": "Engagement metrics updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scan engagement: {e}")
        raise HTTPException(status_code=500, detail="Failed to update engagement metrics")


@router.get("/analytics/{memorial_id}", response_model=QRAnalyticsResponse)
async def get_qr_analytics(
    memorial_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get QR code analytics for memorial.
    
    Provides detailed analytics including scan counts, visitor engagement,
    geographic distribution, device types, and timeline data.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        analytics = await qr_service.get_qr_analytics(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id,
            days=days
        )
        
        return QRAnalyticsResponse(**analytics)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting QR analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get QR analytics")


@router.get("/manufacturing-partners", response_model=List[ManufacturingPartnerResponse])
async def get_manufacturing_partners(
    active_only: bool = Query(default=True, description="Only return active partners"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of manufacturing partners.
    
    Returns available partners for ordering aluminum QR memorial pieces.
    Includes pricing, ratings, and capabilities information.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        partners = await qr_service.get_manufacturing_partners(
            db=db,
            active_only=active_only
        )
        
        return [
            ManufacturingPartnerResponse(
                id=partner.id,
                company_name=partner.company_name,
                specialties=partner.specialties or [],
                base_price_dollars=partner.base_price_dollars,
                turnaround_days=partner.turnaround_days,
                rating=float(partner.rating),
                total_orders=partner.total_orders,
                success_rate=partner.success_rate,
                is_preferred=partner.is_preferred
            )
            for partner in partners
        ]
        
    except Exception as e:
        logger.error(f"Error getting manufacturing partners: {e}")
        raise HTTPException(status_code=500, detail="Failed to get manufacturing partners")


@router.post("/order-aluminum")
async def place_aluminum_order(
    request: AluminumOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Place order for aluminum QR memorial pieces.
    
    Coordinates with manufacturing partner to create physical QR code pieces
    for installation at gravesites. Includes quote calculation and order tracking.
    """
    try:
        qr_service = get_qr_memorial_service()
        
        order_details = await qr_service.place_aluminum_order(
            db=db,
            qr_code_id=request.qr_code_id,
            partner_id=request.partner_id,
            user_id=current_user.id,
            quantity=request.quantity,
            rush_order=request.rush_order
        )
        
        return order_details
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error placing aluminum order: {e}")
        raise HTTPException(status_code=500, detail="Failed to place aluminum order")


@router.get("/partner/{partner_id}/quote")
async def get_partner_quote(
    partner_id: uuid.UUID,
    quantity: int = Query(default=1, ge=1, le=100),
    rush: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get quote from manufacturing partner.
    
    Calculates pricing for aluminum QR pieces including setup fees,
    rush charges, and estimated delivery time.
    """
    try:
        from sqlalchemy import select
        
        # Get manufacturing partner
        stmt = select(ManufacturingPartner).where(
            ManufacturingPartner.id == partner_id,
            ManufacturingPartner.is_active == True
        )
        result = await db.execute(stmt)
        partner = result.scalar_one_or_none()
        
        if not partner:
            raise HTTPException(status_code=404, detail="Manufacturing partner not found")
        
        try:
            quote = partner.calculate_quote(quantity, rush)
            return quote
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting partner quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quote")