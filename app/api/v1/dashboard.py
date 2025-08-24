"""
Dashboard API endpoints for Memorial Website.
Provides dashboard statistics and analytics in Hebrew.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.memorial import Memorial
from app.models.user import User
from app.models.photo import Photo
from app.models.qr_memorial import QRMemorialCode, QRScanEvent, ManufacturingPartner
from app.schemas.user import UserResponse as UserSchema

router = APIRouter()


@router.get("/stats", tags=["Dashboard"])
async def get_dashboard_stats(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the current user in Hebrew.
    
    Returns:
        Dictionary with Hebrew dashboard statistics
    """
    try:
        # Get total memorials for current user  
        total_memorials_result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            )
        )
        total_memorials = total_memorials_result.scalar() or 0
        
        # Get public memorials for current user
        public_memorials_result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False,
                Memorial.is_public == True
            )
        )
        public_memorials = public_memorials_result.scalar() or 0
        
        # Get total page views for user's memorials
        total_views_result = await db.execute(
            select(func.sum(Memorial.page_views)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            )
        )
        total_views = total_views_result.scalar() or 0
        
        # Get total psalm verses associated with user's memorials
        # Count unique psalm verses linked to this user's memorials
        psalm_verses_result = await db.execute(
            text("""
                SELECT COUNT(DISTINCT mpv.psalm_verse_id) 
                FROM memorial_psalm_verses mpv
                JOIN memorials m ON mpv.memorial_id = m.id
                WHERE m.owner_id = :user_id AND m.is_deleted = false
            """),
            {"user_id": current_user.id}
        )
        total_verses = psalm_verses_result.scalar() or 0
        
        # Get memorials created in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_memorials_result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False,
                Memorial.created_at >= thirty_days_ago
            )
        )
        recent_memorials = recent_memorials_result.scalar() or 0
        
        # Get total photos uploaded
        total_photos_result = await db.execute(
            select(func.count(Photo.id)).where(
                Photo.memorial_id.in_(
                    select(Memorial.id).where(Memorial.owner_id == current_user.id)
                )
            )
        )
        total_photos = total_photos_result.scalar() or 0
        
        # Get upcoming Hebrew dates (next 7 days of yahrzeit dates)
        upcoming_yahrzeits_result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False,
                Memorial.yahrzeit_date_hebrew.isnot(None)
            )
        )
        upcoming_yahrzeits = upcoming_yahrzeits_result.scalar() or 0
        
        # Get memorial with most recent activity
        recent_memorial_result = await db.execute(
            select(Memorial).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            ).order_by(Memorial.updated_at.desc()).limit(1)
        )
        recent_memorial = recent_memorial_result.scalar_one_or_none()
        
        recent_memorial_name = ""
        if recent_memorial:
            recent_memorial_name = recent_memorial.deceased_name_hebrew or recent_memorial.deceased_name_english or "ללא שם"
        
        # Get QR code statistics
        qr_codes_result = await db.execute(
            select(func.count(QRMemorialCode.id)).where(
                QRMemorialCode.memorial_id.in_(
                    select(Memorial.id).where(Memorial.owner_id == current_user.id)
                ),
                QRMemorialCode.is_active == True
            )
        )
        total_qr_codes = qr_codes_result.scalar() or 0
        
        # Get total QR scans
        qr_scans_result = await db.execute(
            select(func.count(QRScanEvent.id)).where(
                QRScanEvent.qr_code_id.in_(
                    select(QRMemorialCode.id).where(
                        QRMemorialCode.memorial_id.in_(
                            select(Memorial.id).where(Memorial.owner_id == current_user.id)
                        )
                    )
                )
            )
        )
        total_qr_scans = qr_scans_result.scalar() or 0
        
        # Get recent QR scans (last 30 days)
        recent_qr_scans_result = await db.execute(
            select(func.count(QRScanEvent.id)).where(
                QRScanEvent.qr_code_id.in_(
                    select(QRMemorialCode.id).where(
                        QRMemorialCode.memorial_id.in_(
                            select(Memorial.id).where(Memorial.owner_id == current_user.id)
                        )
                    )
                ),
                QRScanEvent.scanned_at >= thirty_days_ago
            )
        )
        recent_qr_scans = recent_qr_scans_result.scalar() or 0
        
        # Return data in the format expected by the frontend dashboard template
        return {
            "status": "success",
            # Main dashboard metrics (expected by updateStats function)
            "total_memorials": total_memorials,
            "public_memorials": public_memorials,
            "total_views": total_views,
            "total_verses": total_verses,
            "total_qr_codes": total_qr_codes,
            "total_qr_scans": total_qr_scans,
            
            # Additional detailed data for other dashboard components
            "data": {
                "total_memorials": {
                    "value": total_memorials,
                    "label": "סך הכל הנצחות",
                    "description": "מספר ההנצחות הפעילות שיצרת"
                },
                "public_memorials": {
                    "value": public_memorials,
                    "label": "הנצחות ציבוריות",
                    "description": "מספר ההנצחות הציבוריות שיכולים לצפות בהן"
                },
                "total_views": {
                    "value": total_views,
                    "label": "סה״כ צפיות",
                    "description": "מספר הצפיות הכולל בכל ההנצחות שלך"
                },
                "total_verses": {
                    "value": total_verses,
                    "label": "פסוקי תהילים",
                    "description": "מספר פסוקי תהילים קיט המקושרים להנצחות שלך"
                },
                "recent_memorials": {
                    "value": recent_memorials,
                    "label": "הנצחות חדשות (30 יום)",
                    "description": "מספר ההנצחות שנוצרו ב-30 הימים האחרונים"
                },
                "total_photos": {
                    "value": total_photos,
                    "label": "סך הכל תמונות",
                    "description": "מספר התמונות שהועלו לכל ההנצחות"
                },
                "upcoming_yahrzeits": {
                    "value": upcoming_yahrzeits,
                    "label": "יום השנה קרובים",
                    "description": "מספר ימי השנה הרשומים"
                },
                "total_qr_codes": {
                    "value": total_qr_codes,
                    "label": "קודי QR פעילים",
                    "description": "מספר קודי ה-QR הפעילים להנצחות שלך"
                },
                "total_qr_scans": {
                    "value": total_qr_scans,
                    "label": "סריקות QR",
                    "description": "מספר הסריקות הכולל של כל קודי ה-QR"
                },
                "recent_qr_scans": {
                    "value": recent_qr_scans,
                    "label": "סריקות QR (30 יום)",
                    "description": "מספר סריקות ה-QR ב-30 הימים האחרונים"
                },
                "recent_activity": {
                    "memorial_name": recent_memorial_name,
                    "label": "פעילות אחרונה",
                    "description": "ההנצחה שעודכנה לאחרונה"
                },
                "user_info": {
                    "name": current_user.full_name or current_user.email.split("@")[0],
                    "member_since": current_user.created_at.strftime("%B %Y") if current_user.created_at else "",
                    "label": "חבר מאז",
                    "greeting": f"שלום, {current_user.full_name or 'משתמש יקר'}"
                },
                "system_stats": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "timezone": "UTC",
                    "hebrew_calendar_enabled": True
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "שגיאה בטעינת נתוני הלוח",
                "error": str(e),
                "hebrew_message": "לא הצלחנו לטעון את נתוני הלוח. אנא נסה שוב מאוחר יותר."
            }
        )


@router.get("/memorial-usage", tags=["Dashboard"])
async def get_memorial_usage(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get memorial usage statistics for the current user.
    
    Returns:
        Dictionary with memorial usage and limits
    """
    try:
        # Get memorial usage using async query to avoid greenlet issues
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            )
        )
        active_memorials_count = result.scalar() or 0
        
        memorial_usage = {
            "current": active_memorials_count,
            "limit": current_user.max_memorials,
            "remaining": max(0, current_user.max_memorials - active_memorials_count),
            "can_create": active_memorials_count < current_user.max_memorials
        }
        
        return {
            "status": "success",
            "data": {
                "usage": memorial_usage,
                "subscription": {
                    "status": current_user.subscription_status,
                    "can_create": memorial_usage['can_create'],
                    "upgrade_available": memorial_usage['current'] >= memorial_usage['limit']
                },
                "labels": {
                    "current": "אזכרות פעילות",
                    "limit": "מגבלת אזכרות",
                    "remaining": "אזכרות שנותרו",
                    "subscription_status": "סטטוס מנוי",
                    "upgrade_message": "לייצור אזכרות נוספות, שדרג את החשבון שלך"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "שגיאה בטעינת נתוני השימוש",
                "error": str(e),
                "hebrew_message": "לא הצלחנו לטעון את נתוני השימוש. אנא נסה שוב מאוחר יותר."
            }
        )


@router.get("/qr-analytics", tags=["Dashboard"])
async def get_qr_analytics_dashboard(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get QR code analytics dashboard for admin users.
    
    Returns:
        Comprehensive QR analytics data for dashboard display
    """
    try:
        # Get all QR codes for user's memorials with detailed analytics
        qr_codes_with_analytics = await db.execute(
            select(QRMemorialCode).options(
                selectinload(QRMemorialCode.memorial),
                selectinload(QRMemorialCode.manufacturing_partner),
                selectinload(QRMemorialCode.scan_events)
            ).where(
                QRMemorialCode.memorial_id.in_(
                    select(Memorial.id).where(Memorial.owner_id == current_user.id)
                )
            ).order_by(QRMemorialCode.created_at.desc())
        )
        qr_codes = qr_codes_with_analytics.scalars().all()
        
        # Calculate analytics
        total_qr_codes = len(qr_codes)
        active_qr_codes = len([qr for qr in qr_codes if qr.is_active])
        total_scans = sum(qr.total_scans for qr in qr_codes)
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_scans = 0
        for qr_code in qr_codes:
            recent_scans += len([
                scan for scan in qr_code.scan_events 
                if scan.scanned_at >= thirty_days_ago
            ])
        
        # Order status breakdown
        order_status_counts = {}
        for qr_code in qr_codes:
            status = qr_code.order_status
            order_status_counts[status] = order_status_counts.get(status, 0) + 1
        
        # Manufacturing partner breakdown
        partner_stats = {}
        for qr_code in qr_codes:
            if qr_code.manufacturing_partner:
                partner_name = qr_code.manufacturing_partner.company_name
                if partner_name not in partner_stats:
                    partner_stats[partner_name] = {
                        "orders": 0,
                        "scans": 0,
                        "rating": float(qr_code.manufacturing_partner.rating)
                    }
                partner_stats[partner_name]["orders"] += 1
                partner_stats[partner_name]["scans"] += qr_code.total_scans
        
        # Top performing QR codes
        top_qr_codes = sorted(qr_codes, key=lambda x: x.total_scans, reverse=True)[:5]
        top_qr_data = []
        for qr in top_qr_codes:
            top_qr_data.append({
                "id": str(qr.id),
                "memorial_name": qr.memorial.display_name if qr.memorial else "Unknown",
                "total_scans": qr.total_scans,
                "last_scan": qr.last_scan_at.strftime("%Y-%m-%d") if qr.last_scan_at else "Never",
                "is_active": qr.is_active,
                "order_status": qr.order_status
            })
        
        # Revenue analytics (basic calculation)
        total_annual_revenue = sum(qr.annual_fee_cents for qr in qr_codes) / 100.0
        monthly_revenue = total_annual_revenue / 12.0
        
        return {
            "status": "success",
            "data": {
                "overview": {
                    "total_qr_codes": {
                        "value": total_qr_codes,
                        "label": "סך קודי QR",
                        "description": "מספר קודי QR שנוצרו"
                    },
                    "active_qr_codes": {
                        "value": active_qr_codes,
                        "label": "קודי QR פעילים",
                        "description": "מספר קודי QR פעילים כרגע"
                    },
                    "total_scans": {
                        "value": total_scans,
                        "label": "סך סריקות",
                        "description": "מספר סריקות כולל"
                    },
                    "recent_scans": {
                        "value": recent_scans,
                        "label": "סריקות (30 יום)",
                        "description": "סריקות ב-30 יום האחרונים"
                    }
                },
                "order_status": {
                    "breakdown": order_status_counts,
                    "labels": {
                        "pending": "ממתין",
                        "manufacturing": "בייצור",
                        "shipped": "נשלח",
                        "delivered": "נמסר",
                        "cancelled": "בוטל"
                    }
                },
                "manufacturing_partners": {
                    "stats": partner_stats,
                    "total_partners": len(partner_stats)
                },
                "top_performers": {
                    "qr_codes": top_qr_data,
                    "label": "קודי QR מובילים"
                },
                "revenue": {
                    "annual_total": round(total_annual_revenue, 2),
                    "monthly_average": round(monthly_revenue, 2),
                    "currency": "USD",
                    "labels": {
                        "annual": "הכנסה שנתית",
                        "monthly": "ממוצע חודשי"
                    }
                },
                "engagement": {
                    "avg_scans_per_qr": round(total_scans / max(total_qr_codes, 1), 1),
                    "active_percentage": round((active_qr_codes / max(total_qr_codes, 1)) * 100, 1),
                    "recent_activity_percentage": round((recent_scans / max(total_scans, 1)) * 100, 1) if total_scans > 0 else 0
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "שגיאה בטעינת נתוני QR",
                "error": str(e),
                "hebrew_message": "לא הצלחנו לטעון את נתוני קודי ה-QR. אנא נסה שוב מאוחר יותר."
            }
        )


@router.get("/activity", tags=["Dashboard"])
async def get_recent_activity(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get recent activity for the user's memorials.
    
    Args:
        limit: Maximum number of activity items to return
        
    Returns:
        Dictionary with recent activity in Hebrew
    """
    try:
        # Get recent memorials with their activity
        recent_memorials_result = await db.execute(
            select(Memorial).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            ).order_by(Memorial.updated_at.desc()).limit(limit)
        )
        recent_memorials = recent_memorials_result.scalars().all()
        
        activities = []
        for memorial in recent_memorials:
            activity = {
                "memorial_id": memorial.id,
                "memorial_name": memorial.deceased_name_hebrew or memorial.deceased_name_english,
                "activity_type": "עדכון אזכרה",
                "date": memorial.updated_at.isoformat(),
                "hebrew_date": memorial.yahrzeit_date_hebrew,
                "description": f"האזכרה '{memorial.deceased_name_hebrew or memorial.deceased_name_english}' עודכנה"
            }
            activities.append(activity)
        
        return {
            "status": "success",
            "data": {
                "activities": activities,
                "total": len(activities),
                "label": "פעילות אחרונה",
                "description": f"עדכונים אחרונים של {len(activities)} אזכרות"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "שגיאה בטעינת נתוני הפעילות",
                "error": str(e),
                "hebrew_message": "לא הצלחנו לטעון את נתוני הפעילות. אנא נסה שוב מאוחר יותר."
            }
        )


@router.get("/summary", tags=["Dashboard"])
async def get_dashboard_summary(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a summary of the user's memorial data in Hebrew.
    
    Returns:
        Dictionary with Hebrew summary statistics
    """
    try:
        # Get all user memorials
        user_memorials_result = await db.execute(
            select(Memorial).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            )
        )
        user_memorials = user_memorials_result.scalars().all()
        
        # Count by categories
        memorials_with_photos = sum(1 for m in user_memorials if m.photos)
        memorials_with_hebrew_dates = sum(1 for m in user_memorials if m.yahrzeit_date_hebrew)
        memorials_with_both_names = sum(1 for m in user_memorials if m.deceased_name_hebrew and m.deceased_name_english)
        
        return {
            "status": "success",
            "data": {
                "total_memorials": len(user_memorials),
                "memorials_with_photos": memorials_with_photos,
                "memorials_with_hebrew_dates": memorials_with_hebrew_dates,
                "memorials_with_both_names": memorials_with_both_names,
                "completion_stats": {
                    "photos_percentage": round((memorials_with_photos / len(user_memorials)) * 100) if user_memorials else 0,
                    "hebrew_dates_percentage": round((memorials_with_hebrew_dates / len(user_memorials)) * 100) if user_memorials else 0,
                    "both_names_percentage": round((memorials_with_both_names / len(user_memorials)) * 100) if user_memorials else 0
                },
                "labels": {
                    "total_memorials": "סך הכל אזכרות",
                    "memorials_with_photos": "אזכרות עם תמונות",
                    "memorials_with_hebrew_dates": "אזכרות עם תאריכים עבריים",
                    "memorials_with_both_names": "אזכרות עם שמות בעברית ובאנגלית",
                    "completion_stats": "סטטיסטיקות השלמה"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "שגיאה בטעינת סיכום הנתונים",
                "error": str(e),
                "hebrew_message": "לא הצלחנו לטעון את סיכום הנתונים. אנא נסה שוב מאוחר יותר."
            }
        )