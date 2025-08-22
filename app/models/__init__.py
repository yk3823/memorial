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
    
    # Enums
    "UserRole",
    "SubscriptionStatus",
    "ContactType",
    "NotificationType",
    "NotificationStatus",
    
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
}

# Enum registry
ENUMS = {
    "UserRole": UserRole,
    "SubscriptionStatus": SubscriptionStatus,
    "ContactType": ContactType,
    "NotificationType": NotificationType,
    "NotificationStatus": NotificationStatus,
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
    },
    
    "Memorial": {
        "owner": "Many-to-one with User",
        "photos": "One-to-many with Photo",
        "contacts": "One-to-many with Contact",
        "notifications": "One-to-many with Notification",
        "location": "One-to-one with Location",
        "psalm_verses": "Many-to-many with Psalm119Verse",
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
}


def get_model_relationships():
    """
    Get model relationships summary.
    
    Returns:
        dict: Model relationships documentation
    """
    return MODEL_RELATIONSHIPS.copy()