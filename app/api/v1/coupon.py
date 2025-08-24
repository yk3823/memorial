"""
Coupon API endpoints for Memorial Website manual payment system.
Provides coupon generation, validation, and management functionality.
"""

import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_current_admin_user
from app.models.user import User
from app.models.coupon import Coupon
from app.services.coupon import CouponService, get_coupon_service, CouponError, CouponValidationError
from app.schemas.coupon import (
    CouponCreate, CouponResponse, CouponValidation, CouponValidationResponse,
    CouponListResponse, CouponStatsResponse, CouponRevoke
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", 
             response_model=CouponResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Generate new coupon",
             description="Generate a new coupon for manual office payment (Admin only)")
async def generate_coupon(
    coupon_data: CouponCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    Generate a new coupon for manual office payment.
    
    Requires admin privileges. Creates a unique coupon code that can be
    validated by customers who paid manually in the office.
    
    Args:
        coupon_data: Coupon creation data
        db: Database session
        current_user: Current admin user
        coupon_service: Coupon service instance
        
    Returns:
        CouponResponse: Created coupon data
        
    Raises:
        HTTPException: If generation fails or user lacks privileges
    """
    try:
        logger.info(f"Admin {current_user.id} generating coupon for {coupon_data.customer_name}")
        
        coupon = await coupon_service.generate_coupon(
            db=db,
            customer_name=coupon_data.customer_name,
            unique_password=coupon_data.unique_password,
            created_by_admin_id=current_user.id,
            customer_email=coupon_data.customer_email,
            payment_amount=coupon_data.payment_amount,
            currency=coupon_data.currency,
            office_payment_reference=coupon_data.office_payment_reference,
            notes=coupon_data.notes,
            expires_in_days=coupon_data.expires_in_days,
            subscription_months=coupon_data.subscription_months,
            max_memorials_granted=coupon_data.max_memorials_granted
        )
        
        logger.info(f"Coupon generated successfully: {coupon.id}")
        
        return CouponResponse(
            success=True,
            message="קופון נוצר בהצלחה",
            coupon=coupon.to_admin_dict()
        )
        
    except CouponError as e:
        logger.error(f"Coupon generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"יצירת הקופון נכשלה: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating coupon: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה פנימית ביצירת הקופון"
        )


@router.post("/validate",
             response_model=CouponValidationResponse,
             summary="Validate coupon code",
             description="Validate a coupon code for payment processing")
async def validate_coupon(
    validation_data: CouponValidation,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    Validate a coupon code for payment processing.
    
    Checks if the coupon is valid, unused, and matches the customer details.
    If validation succeeds, marks the coupon as used and creates payment.
    
    Args:
        validation_data: Coupon validation data
        request: HTTP request for IP tracking
        db: Database session
        current_user: Current user
        coupon_service: Coupon service instance
        
    Returns:
        CouponValidationResponse: Validation result
    """
    try:
        logger.info(f"Validating coupon {validation_data.coupon_code} for user {current_user.id}")
        
        # Validate coupon
        is_valid, coupon, error_message = await coupon_service.validate_coupon(
            db=db,
            coupon_code=validation_data.coupon_code,
            customer_name=validation_data.customer_name,
            customer_email=validation_data.customer_email
        )
        
        if not is_valid:
            logger.warning(f"Coupon validation failed: {error_message}")
            return CouponValidationResponse(
                success=False,
                message=error_message or "קוד הקופון אינו תקין",
                is_valid=False
            )
        
        # Use the coupon
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        await coupon_service.use_coupon(
            db=db,
            coupon=coupon,
            user=current_user,
            validation_ip=client_ip,
            validation_user_agent=user_agent
        )
        
        logger.info(f"Coupon used successfully: {coupon.code} by user {current_user.id}")
        
        return CouponValidationResponse(
            success=True,
            message="הקופון תקין ונוצל בהצלחה! המנוי שלך הופעל",
            is_valid=True,
            coupon=coupon.to_dict(include_sensitive=False) if coupon else None
        )
        
    except CouponValidationError as e:
        logger.error(f"Coupon validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error validating coupon: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה פנימית באימות הקופון"
        )


@router.get("/list",
            response_model=CouponListResponse,
            summary="List coupons",
            description="List coupons with filtering options (Admin only)")
async def list_coupons(
    status_filter: Optional[str] = Query(None, description="Filter by coupon status"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    include_expired: bool = Query(True, description="Include expired coupons"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    List coupons with filtering options.
    
    Provides paginated listing of coupons with various filter options.
    Admin users can see all coupons, or filter by specific criteria.
    
    Args:
        status_filter: Filter by coupon status
        customer_name: Filter by customer name (partial match)
        limit: Maximum results per page
        offset: Results to skip (pagination)
        include_expired: Whether to include expired coupons
        db: Database session
        current_user: Current admin user
        coupon_service: Coupon service instance
        
    Returns:
        CouponListResponse: List of coupons with metadata
    """
    try:
        logger.info(f"Admin {current_user.id} listing coupons")
        
        coupons = await coupon_service.list_coupons(
            db=db,
            status=status_filter,
            customer_name=customer_name,
            limit=limit,
            offset=offset,
            include_expired=include_expired
        )
        
        # Convert to dictionaries for response
        coupon_list = [coupon.to_admin_dict() for coupon in coupons]
        
        return CouponListResponse(
            success=True,
            coupons=coupon_list,
            total_count=len(coupon_list),
            limit=limit,
            offset=offset,
            has_more=len(coupon_list) == limit
        )
        
    except Exception as e:
        logger.error(f"Error listing coupons: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בטעינת רשימת הקופונים"
        )


@router.get("/stats",
            response_model=CouponStatsResponse,
            summary="Get coupon statistics",
            description="Get coupon usage statistics (Admin only)")
async def get_coupon_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    Get coupon usage statistics.
    
    Provides comprehensive statistics about coupon creation and usage.
    
    Args:
        db: Database session
        current_user: Current admin user
        coupon_service: Coupon service instance
        
    Returns:
        CouponStatsResponse: Coupon statistics
    """
    try:
        logger.info(f"Admin {current_user.id} requesting coupon stats")
        
        stats = await coupon_service.get_coupon_stats(db=db)
        
        return CouponStatsResponse(
            success=True,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting coupon stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בטעינת סטטיסטיקות הקופונים"
        )


@router.get("/{coupon_id}",
            response_model=CouponResponse,
            summary="Get coupon by ID",
            description="Get specific coupon details (Admin only)")
async def get_coupon(
    coupon_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    Get specific coupon details by ID.
    
    Args:
        coupon_id: UUID of the coupon
        db: Database session
        current_user: Current admin user
        coupon_service: Coupon service instance
        
    Returns:
        CouponResponse: Coupon details
        
    Raises:
        HTTPException: If coupon not found
    """
    try:
        logger.info(f"Admin {current_user.id} requesting coupon {coupon_id}")
        
        coupon = await coupon_service.get_coupon_by_id(db=db, coupon_id=coupon_id)
        
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="קופון לא נמצא"
            )
        
        return CouponResponse(
            success=True,
            coupon=coupon.to_admin_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupon: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בטעינת פרטי הקופון"
        )


@router.post("/{coupon_id}/revoke",
             response_model=Dict[str, Any],
             summary="Revoke coupon",
             description="Revoke a coupon, making it unusable (Admin only)")
async def revoke_coupon(
    coupon_id: uuid.UUID,
    revoke_data: CouponRevoke,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    Revoke a coupon, making it unusable.
    
    Args:
        coupon_id: UUID of the coupon to revoke
        revoke_data: Revocation data including reason
        db: Database session
        current_user: Current admin user
        coupon_service: Coupon service instance
        
    Returns:
        Dict: Success message
        
    Raises:
        HTTPException: If revocation fails
    """
    try:
        logger.info(f"Admin {current_user.id} revoking coupon {coupon_id}")
        
        success = await coupon_service.revoke_coupon(
            db=db,
            coupon_id=coupon_id,
            reason=revoke_data.reason,
            admin_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="לא ניתן לבטל את הקופון"
            )
        
        return {
            "success": True,
            "message": "הקופון בוטל בהצלחה"
        }
        
    except HTTPException:
        raise
    except CouponValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error revoking coupon: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בביטול הקופון"
        )


@router.post("/cleanup-expired",
             response_model=Dict[str, Any],
             summary="Cleanup expired coupons",
             description="Mark expired coupons as expired status (Admin only)")
async def cleanup_expired_coupons(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """
    Mark expired coupons as expired status.
    
    Maintenance endpoint to update expired coupons to proper status.
    
    Args:
        db: Database session
        current_user: Current admin user
        coupon_service: Coupon service instance
        
    Returns:
        Dict: Cleanup results
    """
    try:
        logger.info(f"Admin {current_user.id} cleaning up expired coupons")
        
        expired_count = await coupon_service.cleanup_expired_coupons(db=db)
        
        return {
            "success": True,
            "message": f"עודכנו {expired_count} קופונים שפג תוקפם",
            "expired_count": expired_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired coupons: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בניקוי קופונים שפג תוקפם"
        )