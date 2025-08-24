"""
Models package for Memorial Website.
Exports all database models for easy importing.
"""

# Import base classes first
from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin

# Import all models
from .user import User, UserRole, SubscriptionStatus
from .memorial import Memorial, memorial_psalm_verses
from .photo import Photo
from .contact import Contact, ContactType
from .notification import Notification, NotificationType, NotificationStatus
from .location import Location
from .psalm_119 import Psalm119Letter, Psalm119Verse
from .qr_memorial import QRMemorialCode, QRScanEvent, ManufacturingPartner, QROrderStatus, QRDesignTemplate
from .payment import Payment, PaymentStatus, PaymentMethod, CurrencyCode
from .coupon import Coupon, CouponStatus

# Import existing models if they exist
try:
    from .audit import *
except ImportError:
    pass

try:
    from .permission import *
except ImportError:
    pass

# Export all models and enums for easy importing
__all__ = [
    # Base classes
    "Base",
    "BaseModel", 
    "TimestampMixin",
    "SoftDeleteMixin",
    
    # Core models
    "User",
    "Memorial",
    "Photo",
    "Contact", 
    "Notification",
    "Location",
    "Psalm119Letter",
    "Psalm119Verse",
    "QRMemorialCode",
    "QRScanEvent", 
    "ManufacturingPartner",
    "Payment",
    "Coupon",
    
    # Enums
    "UserRole",
    "SubscriptionStatus",
    "ContactType",
    "NotificationType",
    "NotificationStatus",
    "QROrderStatus",
    "QRDesignTemplate",
    "PaymentStatus",
    "PaymentMethod",
    "CurrencyCode",
    "CouponStatus",
    
    # Association tables
    "memorial_psalm_verses",
]

# Model registry for dynamic access
MODELS = {
    "User": User,
    "Memorial": Memorial, 
    "Photo": Photo,
    "Contact": Contact,
    "Notification": Notification,
    "Location": Location,
    "Psalm119Letter": Psalm119Letter,
    "Psalm119Verse": Psalm119Verse,
    "QRMemorialCode": QRMemorialCode,
    "QRScanEvent": QRScanEvent,
    "ManufacturingPartner": ManufacturingPartner,
    "Payment": Payment,
    "Coupon": Coupon,
}

# Enum registry
ENUMS = {
    "UserRole": UserRole,
    "SubscriptionStatus": SubscriptionStatus,
    "ContactType": ContactType,
    "NotificationType": NotificationType,
    "NotificationStatus": NotificationStatus,
    "QROrderStatus": QROrderStatus,
    "QRDesignTemplate": QRDesignTemplate,
    "PaymentStatus": PaymentStatus,
    "PaymentMethod": PaymentMethod,
    "CurrencyCode": CurrencyCode,
    "CouponStatus": CouponStatus,
}


def get_model(model_name: str):
    """
    Get model class by name.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Model class or None if not found
    """
    return MODELS.get(model_name)


def get_enum(enum_name: str):
    """
    Get enum class by name.
    
    Args:
        enum_name: Name of the enum
        
    Returns:
        Enum class or None if not found
    """
    return ENUMS.get(enum_name)


def get_all_models():
    """
    Get all registered models.
    
    Returns:
        dict: Dictionary of model name -> model class
    """
    return MODELS.copy()


def get_all_enums():
    """
    Get all registered enums.
    
    Returns:
        dict: Dictionary of enum name -> enum class
    """
    return ENUMS.copy()


# Model relationships summary for documentation
MODEL_RELATIONSHIPS = {
    "User": {
        "memorials": "One-to-many with Memorial",
        "uploaded_photos": "One-to-many with Photo (uploaded_by)",
        "added_contacts": "One-to-many with Contact (added_by)",
        "notifications": "One-to-many with Notification (user_id)",
        "verified_locations": "One-to-many with Location (verified_by)",
        "payments": "One-to-many with Payment",
    },
    
    "Memorial": {
        "owner": "Many-to-one with User",
        "photos": "One-to-many with Photo",
        "contacts": "One-to-many with Contact",
        "notifications": "One-to-many with Notification",
        "location": "One-to-one with Location",
        "psalm_verses": "Many-to-many with Psalm119Verse",
        "qr_code": "One-to-one with QRMemorialCode",
    },
    
    "Photo": {
        "memorial": "Many-to-one with Memorial",
        "uploaded_by": "Many-to-one with User",
    },
    
    "Contact": {
        "memorial": "Many-to-one with Memorial",
        "added_by": "Many-to-one with User",
        "notifications": "One-to-many with Notification",
    },
    
    "Notification": {
        "memorial": "Many-to-one with Memorial",
        "contact": "Many-to-one with Contact",
        "user": "Many-to-one with User",
    },
    
    "Location": {
        "memorial": "One-to-one with Memorial",
        "verified_by": "Many-to-one with User",
    },
    
    "Psalm119Letter": {
        "verses": "One-to-many with Psalm119Verse",
    },
    
    "Psalm119Verse": {
        "letter": "Many-to-one with Psalm119Letter",
    },
    
    "QRMemorialCode": {
        "memorial": "One-to-one with Memorial",
        "manufacturing_partner": "Many-to-one with ManufacturingPartner",
        "scan_events": "One-to-many with QRScanEvent",
    },
    
    "QRScanEvent": {
        "qr_code": "Many-to-one with QRMemorialCode",
    },
    
    "ManufacturingPartner": {
        "qr_orders": "One-to-many with QRMemorialCode",
    },
    
    "Payment": {
        "user": "Many-to-one with User",
    },
    
    "Coupon": {
        "created_by_admin": "Many-to-one with User (created_by_admin_id)",
        "used_by_user": "Many-to-one with User (used_by_user_id)",
    },
    
}


def get_model_relationships():
    """
    Get model relationships summary.
    
    Returns:
        dict: Model relationships documentation
    """
    return MODEL_RELATIONSHIPS.copy()