"""
Dashboard API endpoints for Memorial Website.
Provides dashboard statistics and analytics in Hebrew.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.deps import get_current_user, get_db
from app.models.memorial import Memorial
from app.models.user import User
from app.models.photo import Photo
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
        
        return {
            "status": "success",
            "data": {
                "total_memorials": {
                    "value": total_memorials,
                    "label": "סך הכל אזכרות",
                    "description": "מספר האזכרות הפעילות שיצרת"
                },
                "recent_memorials": {
                    "value": recent_memorials,
                    "label": "אזכרות חדשות (30 יום)",
                    "description": "מספר האזכרות שנוצרו ב-30 הימים האחרונים"
                },
                "total_photos": {
                    "value": total_photos,
                    "label": "סך הכל תמונות",
                    "description": "מספר התמונות שהועלו לכל האזכרות"
                },
                "upcoming_yahrzeits": {
                    "value": upcoming_yahrzeits,
                    "label": "יום השנה קרובים",
                    "description": "מספר ימי השנה הרשומים"
                },
                "recent_activity": {
                    "memorial_name": recent_memorial_name,
                    "label": "פעילות אחרונה",
                    "description": "האזכרה שעודכנה לאחרונה"
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