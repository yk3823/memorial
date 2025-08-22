"""
Subscription management API endpoints for Memorial Website.
Handles user subscription plans and memorial limits.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse as UserSchema

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Subscription"])


class SubscriptionPlan(BaseModel):
    """Subscription plan configuration."""
    name: str
    max_memorials: int
    price_monthly: float
    price_yearly: float
    features: list[str]


# Available subscription plans
SUBSCRIPTION_PLANS = {
    "free": SubscriptionPlan(
        name="חינם",
        max_memorials=1,
        price_monthly=0.0,
        price_yearly=0.0,
        features=["1 אזכרה", "שיתוף ציבורי", "פסוקי נשמה"]
    ),
    "basic": SubscriptionPlan(
        name="בסיסי",
        max_memorials=3,
        price_monthly=19.99,
        price_yearly=199.99,
        features=["3 אזכרות", "העלאת תמונות", "פסוקי נשמה", "תזכורות יום השנה"]
    ),
    "premium": SubscriptionPlan(
        name="פרמיום",
        max_memorials=10,
        price_monthly=39.99,
        price_yearly=399.99,
        features=["10 אזכרות", "העלאת תמונות ווידאו", "פסוקי נשמה", "תזכורות יום השנה", "עיצוב מתקדם", "תמיכה מועדפת"]
    ),
    "unlimited": SubscriptionPlan(
        name="ללא הגבלה",
        max_memorials=999,
        price_monthly=79.99,
        price_yearly=799.99,
        features=["אזכרות ללא הגבלה", "כל התכונות", "תמיכה VIP", "אחסון מורחב"]
    )
}


@router.get("/plans", summary="Get available subscription plans")
async def get_subscription_plans() -> Dict[str, Any]:
    """
    Get all available subscription plans.
    
    Returns:
        Dictionary with available subscription plans
    """
    return {
        "status": "success",
        "data": {
            "plans": SUBSCRIPTION_PLANS,
            "currency": "ILS",
            "labels": {
                "monthly": "מחיר חודשי",
                "yearly": "מחיר שנתי",
                "features": "תכונות כלולות",
                "max_memorials": "מספר אזכרות מותר"
            }
        }
    }


@router.get("/current", summary="Get current user subscription")
async def get_current_subscription(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current user's subscription information.
    
    Returns:
        Dictionary with subscription details and usage
    """
    try:
        # Get memorial usage using async query to avoid greenlet issues
        from sqlalchemy import select, func
        from app.models.memorial import Memorial
        
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
        
        # Determine current plan based on max_memorials
        current_plan_key = "free"
        for plan_key, plan in SUBSCRIPTION_PLANS.items():
            if current_user.max_memorials == plan.max_memorials:
                current_plan_key = plan_key
                break
        
        current_plan = SUBSCRIPTION_PLANS[current_plan_key]
        
        return {
            "status": "success",
            "data": {
                "current_plan": {
                    "key": current_plan_key,
                    "name": current_plan.name,
                    "max_memorials": current_plan.max_memorials,
                    "features": current_plan.features
                },
                "subscription_status": current_user.subscription_status,
                "subscription_end_date": current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None,
                "trial_end_date": current_user.trial_end_date.isoformat() if current_user.trial_end_date else None,
                "usage": memorial_usage,
                "can_create_memorial": memorial_usage['can_create'],
                "needs_upgrade": memorial_usage['current'] >= memorial_usage['limit']
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בטעינת פרטי המנוי"
        )


class UpgradeRequest(BaseModel):
    """Request to upgrade subscription."""
    plan: str
    billing_cycle: str = "monthly"  # monthly or yearly


@router.post("/upgrade", summary="Upgrade subscription (demo)")
async def upgrade_subscription(
    upgrade_request: UpgradeRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upgrade user subscription (demo implementation).
    
    In production, this would integrate with payment processing.
    For now, it just updates the user's limits immediately.
    """
    try:
        if upgrade_request.plan not in SUBSCRIPTION_PLANS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="תוכנית מנוי לא חוקית"
            )
        
        plan = SUBSCRIPTION_PLANS[upgrade_request.plan]
        
        # Update user subscription (demo - in production would require payment)
        from sqlalchemy import update
        
        # Calculate subscription end date
        if upgrade_request.billing_cycle == "yearly":
            end_date = date.today() + timedelta(days=365)
        else:
            end_date = date.today() + timedelta(days=30)
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                max_memorials=plan.max_memorials,
                subscription_status="active",
                subscription_end_date=end_date
            )
        )
        await db.commit()
        
        # Refresh user object
        await db.refresh(current_user)
        
        logger.info(f"User {current_user.id} upgraded to {upgrade_request.plan}")
        
        return {
            "status": "success",
            "message": f"החשבון שלך שודרג בהצלחה לתוכנית {plan.name}!",
            "data": {
                "plan": {
                    "key": upgrade_request.plan,
                    "name": plan.name,
                    "max_memorials": plan.max_memorials,
                    "features": plan.features
                },
                "subscription_end_date": end_date.isoformat(),
                "new_limits": {
                    "max_memorials": plan.max_memorials,
                    "current_usage": active_memorials_count
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade subscription for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בשדרוג החשבון"
        )


@router.post("/cancel", summary="Cancel subscription")
async def cancel_subscription(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel user subscription (downgrade to free plan).
    
    Note: Existing memorials beyond the free limit will remain but
    user won't be able to create new ones until they upgrade again.
    """
    try:
        from sqlalchemy import update
        
        # Downgrade to free plan
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                max_memorials=1,
                subscription_status="cancelled",
                subscription_end_date=None
            )
        )
        await db.commit()
        
        logger.info(f"User {current_user.id} cancelled subscription")
        
        return {
            "status": "success",
            "message": "המנוי בוטל בהצלחה. עברת לתוכנית החינמית.",
            "data": {
                "plan": "free",
                "max_memorials": 1,
                "note": "האזכרות הקיימות שלך יישארו זמינות, אך לא תוכל ליצור אזכרות חדשות עד לשדרוג החשבון."
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel subscription for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בביטול המנוי"
        )